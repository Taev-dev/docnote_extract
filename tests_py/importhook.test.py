import sys
import this
from unittest.mock import patch

import pytest

from docnote_extract._reftypes import RefMetadata
from docnote_extract._reftypes import ReftypeMixin
from docnote_extract._reftypes import is_reftyped
from docnote_extract.import_hook import _MANUAL_BYPASS_PACKAGES
from docnote_extract.import_hook import _MANUAL_METACLASS_MARKERS
from docnote_extract.import_hook import _MODULE_TO_INSPECT
from docnote_extract.import_hook import _stubbed_getattr
from docnote_extract.import_hook import _StubbingFinderLoader
from docnote_extract.import_hook import bypass_stubbing
from docnote_extract.import_hook import inspect_module
from docnote_extract.import_hook import install_import_hook
from docnote_extract.import_hook import uninstall_import_hook
from docnote_extract.import_hook import use_metaclass_reftype


class TestBypassStubbing:

    def test_adds_to_contextvar_contextmanager(self):
        """The context manager must add the desired modules to the
        context var. After exiting the context, the contextvar must be
        reset.

        This tests the contextmanager form.
        """
        with bypass_stubbing('foo'):
            with bypass_stubbing('bar'):
                retval = _MANUAL_BYPASS_PACKAGES.get()

        assert retval == frozenset({'foo', 'bar'})
        assert not _MANUAL_BYPASS_PACKAGES.get()

    def test_adds_to_contextvar_decorator(self):
        """The context manager must add the desired modules to the
        context var. After exiting the context, the contextvar must be
        reset.

        This tests the decorator form.
        """
        retval: frozenset[str] = frozenset()

        @bypass_stubbing('foo', 'bar')
        @bypass_stubbing('baz')
        def inner_func():
            nonlocal retval
            retval = _MANUAL_BYPASS_PACKAGES.get()

        inner_func()
        assert retval == frozenset({'foo', 'bar', 'baz'})
        assert not _MANUAL_BYPASS_PACKAGES.get()


class TestUseMetaclassReftype:

    def test_both_forms(self):
        """Both the context form and decorator form must work without
        error. This ensures our documentation is correct.
        """
        with use_metaclass_reftype():
            ...

        @use_metaclass_reftype()
        def _():
            ...

        assert True

    def test_adds_to_contextvar(self):
        """The context manager must add the desired qualnames to the
        context var. After exiting the context, the contextvar must be
        reset.

        This tests only the contextmanager form, since testing both
        forms is more a test of contextlib than docnote_extract.
        """
        with use_metaclass_reftype('foo:Foo'):
            with use_metaclass_reftype('bar:Bar', 'baz:Baz'):
                retval = _MANUAL_METACLASS_MARKERS.get()

        assert retval == frozenset({
            RefMetadata(module='foo', name='Foo'),
            RefMetadata(module='bar', name='Bar'),
            RefMetadata(module='baz', name='Baz')})
        assert not _MANUAL_METACLASS_MARKERS.get()


class TestInspectModule:

    def test_both_forms(self):
        """Both the context form and decorator form must work without
        error. This ensures our documentation is correct.
        """
        # I'd do antigravity but it opens a browser window...
        with inspect_module('this'):
            ...

        @inspect_module('this')
        def _():
            ...

        assert True

    def test_adds_to_contextvar(self):
        """Entering the context must add the module to the corresponding
        context var. Exiting the context must cause the contextvar to
        be reset. The returned context must be the loaded module.
        """
        with inspect_module('this') as loaded_module:
            assert _MODULE_TO_INSPECT.get(None) == 'this'
            assert loaded_module.__name__ == 'this'

        assert _MODULE_TO_INSPECT.get(None) is None

    def test_reloading_behavior_purge(self, fresh_unpurgeable_modules, capsys):
        """Entering the context must force reloading of the module.
        If the module is purgeable, exiting the context must remove it
        from sys.modules.
        """
        # This makes sure we get the diff right, in case... iunno, we added
        # a decorator or something that caused some logging. No idea. Just
        # being defensive.
        _, _ = capsys.readouterr()
        with inspect_module('this') as loaded_module:
            # Reloaded, so it won't be exactly the same object
            assert loaded_module is not this

        # This is a quick and dirty way of checking for re-import without
        # patching out importlib.reload, which sounds like a terrible idea.
        # Note that each call to readouterr() flushes the buffer, so this is
        # already a diff.
        stdout_diff, _ = capsys.readouterr()
        assert 'The Zen of Python' in stdout_diff

        assert 'this' not in sys.modules

    def test_reloading_behavior_nopurge(
            self, fresh_unpurgeable_modules, capsys):
        """Entering the context must force reloading of the module.
        If the module is unpurgeable, exiting the context must forcibly
        reload it a second time.
        """
        # This makes sure we get the diff right, in case... iunno, we added
        # a decorator or something that caused some logging. No idea. Just
        # being defensive.
        fresh_unpurgeable_modules.add('this')
        _, _ = capsys.readouterr()
        with inspect_module('this') as loaded_module:
            stdout_diff_middle, _ = capsys.readouterr()
            # Reloaded, so it won't be exactly the same object
            assert loaded_module is not this

        # This is a quick and dirty way of checking for re-import without
        # patching out importlib.reload, which sounds like a terrible idea.
        # Note that each call to readouterr() flushes the buffer, so this is
        # already a diff.
        stdout_diff_after, _ = capsys.readouterr()
        assert 'The Zen of Python' in stdout_diff_middle
        assert 'The Zen of Python' in stdout_diff_after

        assert 'this' in sys.modules


@pytest.fixture
def fresh_unpurgeable_modules():
    """Use this if you want a quick and dirty fixture to control the
    value of the unpurgeable_modules constant.
    """
    unpurgeable_modules = set()
    with patch(
        'docnote_extract.import_hook.UNPURGEABLE_MODULES',
        unpurgeable_modules
    ):
        yield unpurgeable_modules


class TestLoadStubMockingModule:

    def test_find_spec_skips_stdlib(self):
        """find_spec() must return None for modules in the stdlib.
        """
        loader = _StubbingFinderLoader()
        assert loader.find_spec('antigravity', None, None) is None

    def test_find_spec_skips_3p_bypass(self):
        """find_spec() must return None for modules in the third-party
        bypass.
        """
        loader = _StubbingFinderLoader()
        assert loader.find_spec('docnote', None, None) is None

    def test_find_spec_skips_manual_bypass(self):
        """find_spec() must return None for modules in the manual
        bypass.
        """
        loader = _StubbingFinderLoader()
        with bypass_stubbing('pytest'):
            assert loader.find_spec('pytest', None, None) is None

    def test_find_spec_skips_module_to_inspect(self):
        """find_spec() must return a module spec with the alt_spec set
        as loader_state for a module currently being inspected.
        """
        loader = _StubbingFinderLoader()
        with inspect_module('docnote_extract_testpkg'):
            spec = loader.find_spec('docnote_extract_testpkg', None, None)
            assert spec is not None
            assert spec.loader_state is not None

    def test_find_spec_for_stubbable(self):
        """find_spec() must return a ModuleSpec with loader_state=None
        for a stubbable module.
        """
        loader = _StubbingFinderLoader()
        spec = loader.find_spec('docnote_extract_testpkg', None, None)
        assert spec is not None
        assert spec.loader_state is None


class TestStubbedGetattr:

    def test_shared_metaclass_markers(self):
        """Must return a metaclass reftype for any module:attr in the
        shared metaclass markers lookup.
        """
        retval = _stubbed_getattr(
            module_name='configatron', attr_name='ConfigMeta')
        assert isinstance(retval, type)
        assert issubclass(retval, type)
        assert not issubclass(retval, ReftypeMixin)
        assert is_reftyped(retval)
        assert retval._docnote_extract_metadata == RefMetadata(
            module='configatron', name='ConfigMeta')

    def test_manual_metaclass_markers(self):
        """Must return a metaclass reftype for any module:attr in the
        manual metaclass markers lookup.
        """
        with use_metaclass_reftype('foo:Foo'):
            retval = _stubbed_getattr(
                module_name='foo', attr_name='Foo')
        assert isinstance(retval, type)
        assert issubclass(retval, type)
        assert not issubclass(retval, ReftypeMixin)
        assert is_reftyped(retval)
        assert retval._docnote_extract_metadata == RefMetadata(
            module='foo', name='Foo')

    def test_normal_reftype(self):
        """Must return a normal reftype for anything not marked as a
        metaclass.
        """
        retval = _stubbed_getattr(
            module_name='foo', attr_name='Foo')
        assert isinstance(retval, type)
        assert not issubclass(retval, type)
        assert issubclass(retval, ReftypeMixin)
        assert is_reftyped(retval)
        assert retval._docnote_extract_metadata == RefMetadata(
            module='foo', name='Foo')


class TestImportHookInstallation:

    def test_added_and_removed(self):
        """Installing the import hook must add it to sys.meta_path;
        uninstalling must remove it.

        This test deliberately does as little as possible; we'll save
        the heavier lifting for an integration test.
        """
        assert not _check_for_stubbing_loader()
        install_import_hook()
        assert _check_for_stubbing_loader()
        uninstall_import_hook()
        assert not _check_for_stubbing_loader()


def _check_for_stubbing_loader() -> bool:
    instance_found = False
    for loader in sys.meta_path:
        instance_found |= isinstance(loader, _StubbingFinderLoader)

    return instance_found
