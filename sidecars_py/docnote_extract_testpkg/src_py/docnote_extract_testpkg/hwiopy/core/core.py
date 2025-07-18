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
''' Core / toplevel members of the hwiopy library. Everything here *should* be 
platform-independent.
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
A note on nomenclature: for clarity, I'm referring to anything on an SoC as 
a terminal, and everything on a device as a pin. I'm going to try to keep this
division as strict as possible, because I'm confused as balls over here 
already.
Will probably need to add a virtual terminal at some point? Or maybe the 
generic SoC defines terminals available in the fallback sysFS mappings? 
Or summat.
WILL NEED TO BE MADE THREADSAFE AT SOME POINT. THIS IS EXTREMELY DANGEROUS TO
RUN THREADED AT THE MOMENT.
'''
from warnings import warn
class Pin():
    ''' A generic single channel for communication on a device. Pins connect
    to the 'outside world'.
    '''
    def __init__(self, terminal, mode, methods=None, name=None, pin_num=None):
        ...

class Plug():
    ''' A base object for any multiple-pin interface, for example, SPI.
    '''
    def __init__(self):
        ...

class System():
    ''' A base object for any computer system, be it SoC, desktop, whatever.
    Might want to subclass to mmapped system, then to cortex?
    '''
    def __init__(self, resolve_mode):
        ...

    def __enter__(self):
        ...

    def on_start(self, *args, **kwargs):
        ''' Must be called to start the device.
        '''
        ...

    def __exit__(self, type, value, traceback):
        ''' Cleans up and handles errors.
        '''
        ...

    def on_stop(self, *args, **kwargs):
        ''' Cleans up the started device.
        '''
        ...

    def declare_linked_pin(self, terminal, mode):
        ''' Sets up the terminal for on_start initialization and returns a 
        pin object.
        '''
        ...

    def release_terminal(self, terminal):
        ''' Releases a terminal, allowing re-declaration. Note: the device 
        must independently release its pin; if it calls the terminal once it's
        been released, an error will result. This is NOT for repurposing a
        terminal while the device is running.
        '''
        ...

    def mutate_terminal(self, *args, **kwargs):
        ''' Changes a terminal's function while the device it's attached to is 
        running. May or may not be overridden for each individual SoC. Only 
        use if you know what you're doing. Shouldn't be necessary for normal 
        operations.
        '''
        ...

class Device():
    ''' A base object for a generic hardware-inspecific device. Will probably,
    at some point, provide a graceful fallback to sysfs access.
    __init()__
    =========================================================================
    **kwargs
    ----------------------------------------------------------------
    resolve_header: callable    takes str pin_num and returns str term_num
    system          object      core.system, subclass, etc
    local namespace (self.XXXX; use for subclassing)
    ----------------------------------------------------------------
    pinout          dict        [pin name] = core.pin object, subclass, etc
    system          object      core.system, subclass, etc
    _resolve_header callable    resolves a pin into a header   
    create_pin      callable    connects a header pin to a specific term mode
    create_pin()
    =========================================================================
    Connects a header pin to the specified mode on the corresponding system 
    terminal. Likely overridden in each platform definition. 
    *args
    ----------------------------------------------------------------
    pin_num         str         'pin number'
    mode            str         'mode of SoC terminal'
    **kwargs
    ----------------------------------------------------------------
    name=None       str         'friendly name for the pin'
    '''
    def __init__(self, system, resolve_header):
        ...

    def __enter__(self):
        ...

    def on_start(self):
        ...

    def __exit__(self, type, value, traceback):
        ...

    def on_stop(self):
        ...

    def create_pin(self, pin_num, mode, name=None, **kwargs):
        ...

    def release_pin(self, pin):
        ''' Releases the called pin. Can be called by friendly name or pin
        number.
        '''
        ...

