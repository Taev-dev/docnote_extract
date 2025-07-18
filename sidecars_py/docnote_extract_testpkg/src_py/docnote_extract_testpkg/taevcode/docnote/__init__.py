"""This is a programmatically-vendored code sample
that has been stubbified (ie, function bodies removed). Do not modify
it directly; your changes will just be overwritten.

The original source is:
PkgSrcSpec(forge='github',
           repo_id='Taev-dev/docnote',
           pkg_name='docnote',
           offset_dest_root_dir='taevcode',
           root_path='src_py/docnote',
           commit_hash='7d4b0f7b8c13f4a952dba41f722ca9de0479e562',
           license_paths=set())

The license of the original project is included in the top level of
the vendored project directory.

To regenerate, see sidecars/docnote_extract_testpkg_factory. The
command is:
``uv run python -m docnote_extract_testpkg_factory``.

"""
from __future__ import annotations
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import KW_ONLY
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields as dc_fields
from enum import Enum
from functools import partial
from typing import Annotated
from typing import Any
from typing import TypedDict
__all__ = [
    'DocnoteConfig',
    'DocnoteGroup',
    'Note',
    'docnote',
]
class MarkupLang(Enum):
    CLEANCOPY = ('cleancopy', 'clc')
    MARKDOWN = ('markdown', 'md')
    RST = ('rst',)
@dataclass(frozen=True, slots=True)
class Note:
    """``Note``s are how you add actual notes for your documentation.
    They can be given their own config, or implicitly (and lazily)
    inherit the config from their parents. Use them within ``Annotated``
    names:
    > Example note usage
    __embed__: 'code/python'
        from typing import Annotated
        from docnote import Note
        MY_VAR: Annotated[int, Note('My special int')] = 7
    """
    value: str
    _: KW_ONLY
    config: DocnoteConfig | None = field(kw_only=True, default=None)
class DocnoteConfigParams(TypedDict, total=False):
    enforce_known_lang: bool
    markup_lang: str | MarkupLang
    include_in_docs: bool
    parent_group_name: str
    child_groups: Sequence[DocnoteGroup]
    metadata: dict[str, Any]
@dataclass(frozen=True, slots=True, kw_only=True)
class DocnoteConfig:
    """``DocnoteConfig``s can be used for a variety of reasons:
    ++  to control inference of the markup language when not explicitly
        passed, and whether or not to enforce rules around markup langs
    ++  to control whether an object should be included in the generated
        documentation or not, overriding inference rules
    ++  to define documentation sections (groups) that children can
        assign themselves to
    ++  to include themselves in a parent group
    Note that most config parameters are stack-bound: children will
    assume the values of their parents (unless the child defines its
    own overriding config). Some, however -- like the ``child_groups``
    setting -- are bound to only the exact object the config has been
    "attached" to.
    Configs can be attached:
    ++  to a module, by assigning it to the ``DOCNOTE_CONFIG`` name
    ++  to arbitrary names via ``Annotated``
    ++  to classes and functions via the ``docnote`` decorator
    **Note that module configs are inherited by submodules.** You can
    use this, for example, to define a default markup language in your
    entire project, by attaching a config to the toplevel
    ``__init__.py``.
    """
    enforce_known_lang: Annotated[
            bool | None,
            Note('''When ``True``, this will ensure that the current config
                (and configs attached to its children) will enforce that the
                ``markup_lang`` is included in your specified allowlist of
                markup languages, **as determined by your docs generation
                library.**
                Note that the actual check **is not performed by docnote, and
                must be performed by your docs generation library.**
                ''')
        ] = field(default=None, metadata={'docnote.stacked': True})
    markup_lang: Annotated[
            str | MarkupLang | None,
            Note('''When specified, this sets the markup language to use
                for any ``Note`` instances on the attached object (and its
                children) that don't explicitly declare a ``lang`` value.
                ''')
        ] = field(default=None, metadata={'docnote.stacked': True})
    include_in_docs: Annotated[
            bool | None,
            Note('''Whether or not to include the attached object (and its
                children) in the generated documentation. By default
                (``None``), this will be inferred based on python conventions:
                names with a single underscore (or ``__mangled`` names) will
                be excluded, and others included.
                An explicit boolean value can be used to override this
                behavior, forcing exclusion of otherwise-conventionally-public
                objects, or inclusion of conventionally private ones.
                Note that under the following situation:
                ++  parent sets ``include_in_docs=False``
                ++  child sets ``include_in_docs=True``
                the end behavior is determined by the docs generation library.
                ''')
        ] = field(default=None, metadata={'docnote.stacked': True})
    parent_group_name: Annotated[
            str | None,
            Note('''This assigns the attached object to a group within its
                parent by its name.
                Note that docnote itself **does not validate the name** at
                definition time; this is a deliberate choice to avoid library
                consumers from paying an import-time penalty for projects
                using docnotes.
                You should instead rely upon your docs generation library for
                validating these values, ideally as part of your CI/CD suite,
                git hooks, etc.
                ''')
        ] = field(default=None, metadata={'docnote.stacked': False})
    child_groups: Annotated[
            Sequence[DocnoteGroup] | None,
            Note('''This defines both the groups that should be available
                ...

        ] = field(default=None, metadata={'docnote.stacked': False})
    metadata: Annotated[
            dict[str, Any] | None,
            Note('''Arbitrary metadata may be included in the config as
                an extension mechanism for docs generation libraries.
                Whether or not a particular key is inherited by children of
                the attached objects is up to the implementation of the
                docs generation library defining the metadata key.
                ''')
        ] = field(default=None, metadata={'docnote.stacked': None})
    def get_stackables(self) -> DocnoteConfigParams:
        ...

    def __post_init__(self):
        """The vast majority of checks are done by the docs generation
        library in order to avoid runtime consequences for libraries
        that use docnote. However, the one thing we ^^do^^ actually
        verify is that the group names are unique.
        """
        ...

ClcNote: Annotated[
        Callable[[str], Note],
        DocnoteConfig(include_in_docs=False)
    ] = partial(Note, config=DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY))
DOCNOTE_CONFIG_ATTR: Annotated[
        str,
        Note('''Docs generation libraries should use this value to
            get access to any configs attached to objects via the
            ``docnote`` decorator.
            ''')
    ] = '_docnote_config'
@dataclass(frozen=True, slots=True)
class DocnoteGroup:
    name: Annotated[
        str,
        Note('''The name of the ``DocnoteGroup`` is used by children to
            assign themselves to the group.
            It might also be used by an automatic docs generation library in
            its description of the group.
            ''')]
    _: KW_ONLY
    description: Annotated[
            str | None,
            Note('''Groups may optionally include a description, which
                may be used by your docs generation library.
                ''')
        ] = None
    metadata: Annotated[
            dict[str, Any] | None,
            Note('''Groups may optionally include metadata, which
                may be used by your docs generation library.
                ''')
        ] = None
def docnote[T](
        config: DocnoteConfig
        ) -> Callable[[T], T]:
    """This decorator attaches a configuration to a decoratable object:
    > Example usage
    __embed__: 'code/python'
        from docnote import DocnoteConfig
        from docnote import docnote
        @docnote(DocnoteConfig(include_in_docs=False))
        def my_unconventional_private_function(): ...
    """
    ...

def _attach_config[T](to_decorate: T, *, config: DocnoteConfig) -> T:
    ...

DOCNOTE_CONFIG = DocnoteConfig(
    enforce_known_lang=True, markup_lang=MarkupLang.CLEANCOPY)
