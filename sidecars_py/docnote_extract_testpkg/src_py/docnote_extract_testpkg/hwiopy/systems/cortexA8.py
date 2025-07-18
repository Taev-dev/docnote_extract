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
''' Beaglebone Black hardware-specific operations.
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
Missing a great many error traps.
This should all be made threadsafe. It is currently HIGHLY un-threadsafe.
'''
import io
import json
import struct
import mmap
from pkg_resources import resource_string
from math import ceil
from . import __path__
from .. import core
_mode_generators = {}
class _memory_map():
    ''' Callable class that resolves the memory mapping for registers into a 
    [start, end] tuple. Also provides utility functions to list available 
    registers, etc.
    _memory_map():
    ======================================================
    *args
    ------------------------------------------------------
    register:           str             'name of register'
    return
    -------------------------------------------------------
    tuple               (start address, end address)
    _memory_map.list():
    ========================================================
    return
    --------------------------------------------------------
    tuple               ('register0', 'register1', 'register2'...)
    _memory_map.describe():
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

    def __call__(self, register):
        ...

    def get_clockcontrol(self, register):
        ...

    def list(self):
        ...

    def describe(self, register):
        ...

class _register_map():
    ''' Callable class that resolves the bit mapping for registers into an 
    [offset, size] tuple. Also provides utility functions to list available 
    registers, etc.
    _register_map():
    ======================================================
    *args
    ------------------------------------------------------
    register_type:      str             'ex: gpio, pwm, etc'
    register_function=None: str             'ex: dataout, cleardataout, etc'
    bit_command=None:   str             'ex: autoidle, enawakeup, etc'
    return
    -------------------------------------------------------
    register_function=None: dict            {'function': (offset, bitsize)...}
    register_function=str:
        bit_command=None:   tuple           (offset, bitsize)
        bit_command=str:    tuple           (offset, bitsize, bitrange)
    _register_map.list():
    ========================================================
    *args
    --------------------------------------------------------
    register_type=None: str             'ex: gpio, pwm, etc'
    return
    --------------------------------------------------------
    register_type=None: tuple           ['gpio', 'pwm'...]
    register_type=str:  tuple           ['autoidle', 'enawakeup'...]
    _register_map.describe():
    =========================================================
    *args
    ---------------------------------------------------------
    register_type:      str             'ex: gpio, pwm, etc'
    return
    -------------------------------------------------------
    dict                {'function': ['bit op 1', 'bit op 2'...]}
    '''
    _channelwise = '_intchannel'
    def __init__(self):
        ...

    def __call__(self, register_type, register_function=None, 
            bit_command=None):
        ...

    def list(self, register_type=None):
        ...

    def describe(self, register_type):
        ...

class _mode_map():
    ''' Callable class that resolves a sitara terminal into its 
    available modes, which are callable to initialize that mode.
    _mode_map():
    ======================================================
    *args
    ------------------------------------------------------
    terminal:           str             'name of terminal'
    mode=None           str             'mode for terminal'
    return
    -------------------------------------------------------
    mode=None           dict            {'mode': callable, 'gpio': gpio}
    mode=str            callable class  
    _mode_map.list():
    ========================================================
    *args
    --------------------------------------------------------
    terminal=None       str             'name of terminal'
    only_assignable=False   bool        Only list assignable modes
    return
    --------------------------------------------------------
    terminal=None       dict            {'term': ['mode', ...], ...}
    terminal=str        list            ['mode', 'mode', ...]
    _mode_map.describe():
    ========================================================
    *args
    --------------------------------------------------------
    terminal            str             'name of terminal'
    mode=None           str             'name of mode to describe'
    return
    --------------------------------------------------------
    mode=None           list            ['mode description, mode descr...]
    mode=str            str             'description of mode'
    _mode_map.get_register():
    ========================================================
    *args
    --------------------------------------------------------
    terminal            str             'name of terminal'
    mode                str             'name of mode'
    return
    --------------------------------------------------------
    str                 'name of register'
    '''
    def __init__(self, modes_file):
        ...

    def __call__(self, system, terminal, mode):
        ...

    def list(self, terminal=None, only_assignable=False):
        ...

    def describe(self, terminal, mode=None):
        ...

    def get_register(self, terminal, mode):
        ...

class Sitara335(core.System):
    ''' The sitara 335 SoC. Used in the Beaglebone Black.
    '''
    def __init__(self, mem_filename):
        ...

    def __enter__(self):
        ''' Overrides the generic chipset entry method.
        '''
        ...

    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        ...

    def __exit__(self, type, value, traceback):
        ''' Overrides the generic chipset exit method.
        '''
        ...

    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        ...

    def declare_linked_pin(self, terminal, mode, *args, **kwargs):
        ''' Sets up a pin as something, checks for available modes, etc.
        '''
        ...

    def _get_register_mmap(self, register):
        ''' Returns an mmap for the specified register. If the register hasn't
        been opened, opens it.
        This should only be called during setup, not during initialization or
        after the system has started.
        '''
        ...

class _gpio():
    ''' Callable class for creating a GPIO terminal for cortex A8 SoCs.
    Functions as a generator for core.Pin update, status, and setup methods,
    as well as any other methods relevant to the gpio.
    '''
    def __init__(self, system, terminal):
        ...

    def __call__(self):
        ...

    def update(self, status):
        ...

    def output_high_nocheck(self):
        ...

    def output_low_nocheck(self):
        ...

    def input_nocheck(self):
        ...

    def status(self):
        ...

    def on_start(self):
        ...

    def on_stop(self):
        ...

    def _set_direction(self):
        ...

    def _start_bus_clock(self):
        ''' Makes sure the bus clock for the gpio bank is running. Together
        with _set_direction, these make up the two functions of the sysfs
        "export" mapping.
        '''
        ...

    def config(self, direction):
        ...

_mode_generators['gpio'] = _gpio
def _mode_not_implemented():
    ...

