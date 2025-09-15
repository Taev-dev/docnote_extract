"""This does a bunch of incredibly fragile regex magic to strip out the
bodies of functions. We use it strictly for generating realistic (as
in, real-world-esque!) code for the test package.
"""
from __future__ import annotations

import contextlib
import json
import re
import tempfile
import textwrap
import time
from collections.abc import Iterable
from dataclasses import asdict as dc_asdict
from dataclasses import dataclass
from functools import partial
from io import TextIOWrapper
from itertools import chain
from pathlib import Path
from pprint import pformat
from typing import IO
from typing import Literal
from zipfile import ZipFile
from zipfile import ZipInfo

import httpx

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
TESTPKG_PACKAGE_ROOT = (
    REPO_ROOT / 'sidecars_py/docnote_extract_testpkg/src_py'
    / 'docnote_extract_testpkg')
SRC_SPEC_FILENAME = 'source_spec.json'
RATELIMIT = .5
# 200 KiB
MAX_SIZE = 1024 * 200

_pattern_def_start = re.compile(r'^(?P<indentation>\s*)def')
_pattern_nonempty_indentation = re.compile(r'^(?P<indentation>\s*)\S')
_pattern_docstring_start = re.compile(
    r'^(?P<indentation>\s*)(?P<quotes>"""|\'\'\')')
_pattern_docstring_end = re.compile(r'(?P<quotes>"""|\'\'\')\s*$')
_pattern_empty_line = re.compile(r'^\s*$')
_pattern_empty_func = re.compile(r':\s*(\.\.\.|pass)\s*$')

_STUB_DISCLAIMER = '''This is a programmatically-vendored code sample
that has been stubbified (ie, function bodies removed). Do not modify
it directly; your changes will just be overwritten.

The original source is:
{src_spec}

The license of the original project is included in the top level of
the vendored project directory.

To regenerate, see sidecars/docnote_extract_testpkg_factory. The
command is:
``uv run python -m docnote_extract_testpkg_factory``.

'''


@dataclass(slots=True, kw_only=True)
class PkgSrcSpec:
    # Note: currently only github is supported
    forge: str = 'github'
    repo_id: str
    pkg_name: str
    offset_dest_root_dir: str | None = None
    root_path: str
    commit_hash: str
    license_paths: set[str]

    @property
    def zip_root(self) -> str:
        """Github puts the repo within a folder internally; this gives
        us the offset path for it.
        """
        _, repo_name = self.repo_id.split('/')
        return f'{repo_name}-{self.commit_hash}'


def should_unzip(tmpdir_path: Path, info: ZipInfo) -> bool:
    # Note that, if info.filename is an absolute path, the tmpdir_path will
    # be discarded. We'll deal with that when we cull things in just a second.
    hypothetical_path = tmpdir_path / info.filename
    hypothetical_size = info.file_size

    if hypothetical_size > MAX_SIZE:
        return False

    # Note that zip files can contain paths to files outside their directory,
    # strangely enough. Here we cull any of those.
    if not hypothetical_path.resolve().is_relative_to(tmpdir_path):
        return False

    if hypothetical_path.suffix != '.py':
        return False

    return True


def coerce_filename_to_path_and_cull_external(
        tmpdir_path: Path,
        filename: str
        ) -> Path | None:
    """Zipfiles can actually unpack to folders NOT inside their
    directory, by including either absolute paths or .. in the filename.
    This removes such files, and then converts the string filename to
    a Path object.
    """
    # Note that, if info.filename is an absolute path, the tmpdir_path will
    # be discarded.
    hypothetical_path = tmpdir_path / filename

    # And now resolving will also normalize any .. path segments
    if not hypothetical_path.resolve().is_relative_to(tmpdir_path):
        return None

    return Path(filename)


def filter_zip_contents(
        tmpdir_path: Path,
        zfd: ZipFile,
        src_spec: PkgSrcSpec
        ) -> Iterable[tuple[ZipInfo, Path, bool]]:
    """Inspects the zip contents. Adapts their paths so they match our
    expected destinations. Filters out anything that isn't a license
    file or python file.
    """
    all_infos = zfd.infolist()
    for info in all_infos:
        if info.file_size > MAX_SIZE:
            continue

        src_path = coerce_filename_to_path_and_cull_external(
            tmpdir_path, info.filename)
        if src_path is None:
            continue

        normalized_src_path = src_path.relative_to(src_spec.zip_root)
        if str(normalized_src_path) in src_spec.license_paths:
            yield info, Path('LICENSE.txt'), False
            continue

        try:
            dest_path = normalized_src_path.relative_to(src_spec.root_path)
        # Raised if not relative, because the path wasn't inside the root dir.
        # more filtering!
        except ValueError:
            continue

        if normalized_src_path.suffix != '.py':
            continue

        yield info, dest_path, True


def vendorify_pkg_stub(src_spec: PkgSrcSpec, debug_mode: bool = False):
    if debug_mode:
        not_so_temp_dir = REPO_ROOT / '.tmp'
        not_so_temp_dir.mkdir(exist_ok=True)
        tempdir_context = partial(contextlib.nullcontext, not_so_temp_dir)
    else:
        tempdir_context = tempfile.TemporaryDirectory

    print(f'Stubbifying: {src_spec.pkg_name}: {src_spec}')
    start_time = time.monotonic()

    if src_spec.offset_dest_root_dir is None:
        dest_root_dir = TESTPKG_PACKAGE_ROOT / src_spec.pkg_name
    else:
        dest_root_dir = (
            TESTPKG_PACKAGE_ROOT / src_spec.offset_dest_root_dir
            / src_spec.pkg_name)

    dest_root_dir.mkdir(exist_ok=True, parents=True)
    dict_src_spec = dc_asdict(src_spec)
    # Quick and dirty fix for json: just drop the set object.
    dict_src_spec.pop('license_paths', None)
    (dest_root_dir / SRC_SPEC_FILENAME).write_text(
        json.dumps(dict_src_spec), encoding='utf-8')

    with tempdir_context() as tmpdir_name:
        tmpdir_path = Path(tmpdir_name)
        zip_path = tmpdir_path / f'.git.{src_spec.commit_hash}.zip'

        do_ratelimit = download_zipped_repo(src_spec, zip_path)

        with ZipFile(zip_path) as zfd:
            for (
                zip_info, dest_path_rel, needs_stubbification
            ) in filter_zip_contents(tmpdir_path, zfd, src_spec):
                dest_path = dest_root_dir / dest_path_rel
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                with zfd.open(zip_info) as src_zfd:
                    if needs_stubbification:
                        unpack_and_stubbify(
                            src_spec,
                            TextIOWrapper(src_zfd, encoding='utf-8'),
                            dest_path)

                    else:
                        with dest_path.open('wb') as dest_fd:
                            for chunk in src_zfd:
                                dest_fd.write(chunk)

    print('Done.')
    if do_ratelimit:
        print('File was downloaded; waiting for ratelimit.')
        end_time = time.monotonic()
        # We want to be exceptionally kind to github here! This doesn't need to
        # run frequently, and nor does it need to run quickly. Avoid ratelimits
        # and other negative side effects at all costs. Plus, just, yknow, "be
        # kind, rewind" and all that.
        time.sleep(max(0, RATELIMIT - (end_time - start_time)))

    print('Proceeding.')


def download_zipped_repo(src_spec: PkgSrcSpec, dest_zip_path: Path) -> bool:
    """Note: if the repo zipfile already exists (because of debug mode),
    does nothing.

    Returns True if a file was downloaded, False if not.
    """
    if dest_zip_path.exists():
        return False

    with dest_zip_path.open('wb') as fd:
        with httpx.stream(
            'GET',
            get_archive_url(src_spec),
            follow_redirects=True
        ) as response:
            if response.status_code != 200:  # noqa: PLR2004
                raise ValueError('Bad status code!', response.status_code)

            for data in response.iter_bytes():
                fd.write(data)

    return True


@dataclass(slots=True)
class _TripleQuoteState:
    tq_single_count: int = 0
    tq_double_count: int = 0

    def advance(self, line: str) -> str:
        """Note: line must be after stripping comments.
        Returns whatever part of the line is left that wasn't inside a
        triple-quoted string.
        """
        first_quote_type = self.get_first_triple_quote_type(line)
        # No quotes, so it's all or nothing
        if first_quote_type == 0:
            if self.in_tq_string:
                return ''
            else:
                return line

        # For the rest, there's a partially-unquoted line that we need to
        # extract (and we need to update the count totals)
        if first_quote_type == 1:
            before, _, after = line.partition("'''")
            # Note that we already checked to make sure we're not inside a
            # triple-quoted string already (in get_first_tq...)
            self.tq_single_count += 1

        else:
            before, _, after = line.partition('"""')
            # Note that we already checked to make sure we're not inside a
            # triple-quoted string already (in get_first_tq...)
            self.tq_double_count += 1

        if self.in_tq_string:
            return before
        else:
            return after

    def get_first_triple_quote_type(
            self,
            line: str
            ) -> Literal[0] | Literal[1] | Literal[2]:
        """For the passed line:
        ++  Returns 0 if there is no triple-quoted string.
        ++  Returns 1 if the first triple-quoted string uses single
            quotes.
        ++  Returns 2 if the first triple-quoted string uses double
            quotes.
        """
        if '"""' in line:
            double_index = line.index('"""')
        else:
            double_index = float('inf')

        if "'''" in line:
            single_index = line.index("'''")
        else:
            single_index = float('inf')

        if double_index == single_index == float('inf'):
            return 0

        # Note that we need to make sure we aren't inside a tq-string first!
        if self.tq_single_count % 2 == 0 and double_index < single_index:
            return 2
        elif self.tq_single_count % 2 != 0 and single_index != float('inf'):
            return 1
        elif self.tq_double_count % 2 == 0 and single_index < double_index:
            return 1
        elif self.tq_double_count % 2 != 0 and double_index != float('inf'):
            return 2

        return 0

    @property
    def in_tq_string(self) -> bool:
        """This is more of a heuristic than anything smart."""
        return (
            self.tq_single_count % 2 != 0
            or self.tq_double_count % 2 != 0)


def unpack_and_stubbify(
        src_spec: PkgSrcSpec,
        src_file: IO[str],
        dest_path: Path):
    """This is an extremely simplistic way of making files smaller than
    they originally were. We strip all comments and drop function bodies
    (except docstrings via a heuristic).
    """
    tq_state = _TripleQuoteState()
    func_state: _FuncDefState | None = None
    with dest_path.open('wt', encoding='utf-8') as dest_fd:
        dest_fd.write(
            textwrap.indent(
                _STUB_DISCLAIMER.format(src_spec=pformat(src_spec, indent=4)),
                prefix='# '))
        # We add one last closing line (which we detect and drop) as a marker
        # for the end of the file, since we otherwise might not yet have
        # finished processing a function def/body/etc.
        dummy_text = 'if None: pass'
        for line in chain(src_file, [dummy_text]):
            costripped_line, _, _ = line.partition('#')
            # Normalize the newline away so it doesn't matter if there was a
            # comment or not
            costripped_line = costripped_line.rstrip('\n')
            if not costripped_line.strip():
                continue

            sanitized_line = tq_state.advance(costripped_line)
            # This is confusing, but: if we detect dedentation, OR the start
            # of a new function, we need to backtrack to re-process the current
            # line.
            line_processed = False
            next_output = None
            while not line_processed:
                if func_state is None:
                    func_state = _FuncDefState.detect_function(sanitized_line)
                    # Still none means that we don't need to re-check this,
                    # because there was no function; otherwise, we do still
                    # need to process it.
                    if func_state is None:
                        next_output = costripped_line
                        line_processed = True

                else:
                    next_output, still_funky = func_state.advance(
                        costripped_line, sanitized_line)

                    if still_funky:
                        line_processed = True
                    # This means that it was a single-line, empty function.
                    # If we backtrack, we'll get stuck in an infinite loop.
                    elif next_output == costripped_line:
                        func_state = None
                        line_processed = True
                    else:
                        # Note: this is where we do the backtracking. First,
                        # the func_state will have injected the fake function
                        # body -- that's the next_output we need to print.
                        # Then, we need to completely reset the state of the
                        # line, and reprocess it.
                        func_state = None
                        dest_fd.write(f'{next_output}\n')
                        next_output = None

            if next_output and next_output != dummy_text:
                # Note that we need to recover the newline we
                # normalized away
                dest_fd.write(f'{next_output}\n')


@dataclass(slots=True, kw_only=True)
class _FuncDefState:
    in_func_def: bool = True
    in_post_func_def: bool = False
    in_func_docstring: bool = False
    in_func_body: bool = False
    indent_level_before: int
    indent_level_inside: int | None = None
    def_open_paren_count: int = 0
    def_close_paren_count: int = 0
    docstring_quotes: str | None = None

    def advance(  # noqa: C901, PLR0911, PLR0912
            self,
            costripped_line: str,
            sanitized_line: str
            ) -> tuple[str, bool]:
        """Quick and dirty state machine for figuring out function defs.
        This isn't a greaaaat use of our time, so we're doing this as
        simply as possible, and not being super strict on typing.
        """
        if _pattern_empty_line.match(sanitized_line):
            return costripped_line, True

        if self.in_func_def:
            self.def_open_paren_count += sanitized_line.count('(')
            self.def_close_paren_count += sanitized_line.count(')')

            if (
                self.def_open_paren_count
                and self.def_open_paren_count == self.def_close_paren_count
            ):
                self.in_func_def = False

                if _pattern_empty_func.search(sanitized_line):
                    return costripped_line, False

                else:
                    self.in_post_func_def = True
                    return costripped_line, True

            else:
                return costripped_line, True

        elif self.in_post_func_def:
            # Just to be clear, this means we found a docstring for the
            # function, and we need to transition into the in_docstring state
            if (match := _pattern_docstring_start.match(costripped_line)):
                indentation = match.group('indentation')
                self.indent_level_inside = len(indentation) // 4
                self.docstring_quotes = match.group('quotes')
                self.in_post_func_def = False
                self.in_func_docstring = True
                # No recursion needed; we found a docstring, so by definition,
                # we can't possibly be ending the function on this line.
                return costripped_line, True

            # Again, for clarity: this means we DIDN'T find a docstring, and
            # we need to transition to the in_func_body state, and then
            # reprocess the line with that state applied.
            elif (
                match := _pattern_nonempty_indentation.match(costripped_line)
            ):
                indentation = match.group('indentation')
                self.indent_level_inside = len(indentation) // 4
                self.in_post_func_def = False
                self.in_func_docstring = False
                self.in_func_body = True
                # Recursion is how we're re-processing the line with the
                # advanced state. It's a little awkward, but it works.
                return self.advance(costripped_line, sanitized_line)

            else:
                raise RuntimeError(
                    'impossible branch: unknown post def state!')

        elif self.in_func_docstring:
            if (match := _pattern_docstring_end.search(costripped_line)):
                if match.group('quotes') == self.docstring_quotes:
                    self.in_func_docstring = False
                    self.in_func_body = True

            return costripped_line, True

        elif self.in_func_body:
            if (match := _pattern_nonempty_indentation.match(sanitized_line)):
                indentation = match.group('indentation')
                indent_level = len(indentation) // 4

                dedented: bool = indent_level < self.indent_level_inside  # type: ignore
                if dedented:
                    return (
                        f'{self.indent_level_inside * "    "}...\n',  # type: ignore
                        False)
                else:
                    return '', True

            # Empty line -- had no non-whitespace in it. Theoretically already
            # caught at the beginning, but this keeps the type checker happy
            else:
                return '', True

        else:
            raise RuntimeError('impossible branch: unknown func def state!')

    @classmethod
    def detect_function(cls, sanitized_line: str) -> _FuncDefState | None:
        if (match := _pattern_def_start.match(sanitized_line)):
            pre_func_indent = match.group('indentation')
            return cls(indent_level_before=len(pre_func_indent) // 4)


def get_archive_url(src_spec: PkgSrcSpec) -> str:
    # Yes, yes, too long, I know
    return (
        f'https://github.com/{src_spec.repo_id}/archive/{src_spec.commit_hash}.zip'
    )


SOURCES: list[PkgSrcSpec] = [
    # This is causing a bunch of problems because its docnotes, configs, etc
    # aren't from the "real" docnote package.
    # PkgSrcSpec(
    #     repo_id='Taev-dev/docnote',
    #     pkg_name='docnote',
    #     root_path='src_py/docnote',
    #     # Note: we're only offsetting these so we can play around with
    #     # nesting configs
    #     offset_dest_root_dir='taevcode',
    #     commit_hash='7d4b0f7b8c13f4a952dba41f722ca9de0479e562',
    #     license_paths=set(),
    #     ),
    PkgSrcSpec(
        repo_id='Taev-dev/finnr',
        pkg_name='finnr',
        root_path='src_py/finnr',
        # Note: we're only offsetting these so we can play around with
        # nesting configs
        offset_dest_root_dir='taevcode',
        commit_hash='17cf5230f6f24f968aebe07cb92072ccaa9f0eda',
        license_paths=set()),
    # This is a biiiiig repo, I don't think we want to use it
    # PkgSrcSpec(
    #     repo_id='pyca/cryptography',
    #     pkg_name='cryptography',
    #     root_path='src/cryptography',
    #     commit_hash='d8a3f9aad4ca9b802d6beee7eb71b6f85a50c6a4',
    #     license_paths={'LICENSE', 'LICENSE.APACHE', 'LICENSE.BSD'}),
    # This had some weird issues with indentation and docstrings
    # PkgSrcSpec(
    #     repo_id='agronholm/anyio',
    #     pkg_name='anyio',
    #     root_path='src/anyio',
    #     commit_hash='65fe287039e2ded48752e1111a82c29d07725e36',
    #     license_paths={'LICENSE'}),
    # This does too much magic with sync/async stuff
    # PkgSrcSpec(
    #     repo_id='encode/httpx',
    #     pkg_name='httpx',
    #     root_path='httpx',
    #     commit_hash='4fb9528c2f5ac000441c3634d297e77da23067cd',
    #     license_paths={'LICENSE.md'}),
    PkgSrcSpec(
        repo_id='Badg/hwiopy',
        pkg_name='hwiopy',
        root_path='hwiopy',
        commit_hash='c6536bc4e1c410f835def3847e1881f2d7f0c076',
        license_paths={'LICENSE.txt'}),
]


if __name__ == '__main__':
    for src_spec in SOURCES:
        vendorify_pkg_stub(src_spec, True)
