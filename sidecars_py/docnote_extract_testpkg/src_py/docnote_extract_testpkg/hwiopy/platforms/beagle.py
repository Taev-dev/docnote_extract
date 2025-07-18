"""This is a programmatically-vendored code sample
that has been stubbified (ie, function bodies removed). Do not modify
it directly; your changes will just be overwritten.

The original source is:
PkgSrcSpec(forge='github',
           repo_id='Badg/hwiopy',
           pkg_name='hwiopy',
           offset_dest_root_dir=None,
           root_path='hwiopy',
           commit_hash='c6536bc4e1c410f835def3847e1881f2d7f0c076',
           license_paths={'LICENSE.txt'})

The license of the original project is included in the top level of
the vendored project directory.

To regenerate, see sidecars/docnote_extract_testpkg_factory. The
command is:
``uv run python -m docnote_extract_testpkg_factory``.

"""
''' Beaglebone/Beagleboard/Etc hardware-specific operations.
LICENSING
-------------------------------------------------
hwiopy: A common API for hardware input/output access.
    Copyright (C) 2014-2015 Nicholas Badger
    badg@nickbadger.com
    nickbadger.com
    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.
    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.
    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
    USA
------------------------------------------------------
Something something sooooomething goes here.
'''
import io
import struct
import mmap
import json
from warnings import warn
from pkg_resources import resource_string
from . import __path__
from .. import core
from .. import systems
class _header_map():
    ''' Callable class that resolves the header pins into their connections, 
    as well as providing several utility functions to describe the device.
    _header_map():
    ======================================================
    Returns the header connection, be it a hardwired one (ex 5VDC) or a SoC
    terminal.
    *args
    ------------------------------------------------------
    pin_num:            str             'pin number'
    return
    -------------------------------------------------------
    str                 'SoC terminal or other'
    _header_map.list_system_headers():
    ========================================================
    Returns all of the header pins that connect to the sitara SoC.
    return
    --------------------------------------------------------
    dict                {'pin num': 
    _memory_map.list_all_headers():
    =========================================================
    *args
    ---------------------------------------------------------
    register:           str             'name of register'
    return
    -------------------------------------------------------
    str                 'description of register'
    '''
    def __init__(self):
        ...

    def __call__(self, pin_num, pin_941=None, pin_942=None, *args, **kwargs):
        ...

    def list_system_headers(self):
        ...

    def list_all_headers(self):
        ...

class BBB(core.Device):
    ''' A beaglebone black. Must have kernel version >=3.8, use overlays, etc.
    '''
    def __init__(self, mem_filename='/dev/mem'): 
        ''' Creates the device and begins setting it up.
        '''
        ...

    def create_pin(self, pin_num, mode, name=None):
        ''' Gets a pin object from the self.chipset object and connects it to 
        a pin on the self.pinout dict.
        which_terminal is redundant with mode?
        '''
        ...

    def validate(self):
        ''' Checks the device setup for conflicting pins, etc.
        Actually this is probably unnecessary (?), as individual pin 
        assignments should error out with conflicting setups.
        '''
        ...

