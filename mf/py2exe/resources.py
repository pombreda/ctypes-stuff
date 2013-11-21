#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""resources for py3exe
"""
from collections import defaultdict
import contextlib
import ctypes

from . import _wapi
from . import icons

@contextlib.contextmanager
def UpdateResources(filename, *, delete_existing=False):
    """A contextmanager which will update the resources in a Windows
    executable file.

    Returns a ResourceWriter object that has methods to add resource
    types.
    """
    hrscr = _wapi.BeginUpdateResourceW(filename, delete_existing)
    resource_writer = ResourceWriter(hrscr, filename)
    yield resource_writer
    resource_writer.flush()
    _wapi.EndUpdateResourceW(hrscr, False)
    # XXX We should update the file checksum here...


class ResourceWriter(object):
    def __init__(self, hrscr, filename):
        self._hrscr = hrscr
        self._filename = filename
        self._strings = {}

    def add(self, *, type, name, value, langid=0):
        """Write a resource to the exefile.
        <type> is typically a RT_xxx value.
        <name> can be a string or an integer.
        <value> is a byte string containing the resource data.
        """
        # I use keyword only args when I cannot remember the order of
        # positional arguments ;-)
        try:
            _wapi.UpdateResourceW(self._hrscr,
                                  _wapi.LPCWSTR(type),
                                  _wapi.LPCWSTR(name),
                                  langid, # wLanguage
                                  value,
                                  len(value))
        except WindowsError as details:
            raise WindowsError(details) from None

    def add_string(self, key, value):
        """Add a string to the string resource.  The strings will be
        buffered until flush() is called.

        Note: flush is called automatically in the UpdateResource
        context manager.
        """
        # Should we be able to specify a langid here? (see below)
        self._strings[key] = value

    def flush(self):
        """Flush all buffered data."""
        # Strings in the string resources are grouped in groups of 16.
        groups = defaultdict(dict)
        for i in sorted(self._strings):
            sectnum, tabnum = divmod(i, 16)
            table = groups[sectnum+1]
            table[tabnum] = self._strings[i]

        # Collect the strings in each group, write them to a w_char_t
        # buffer prepended by the length and add them as RT_STRING
        # resource.
        for key, strings in groups.items():
            data = b""
            for i in range(16):
                text = strings.get(i, "")
                # Is it a performance problem to create a separate
                # structure for each group?
                class Entry(ctypes.Structure):
                    _fields_ = [("len", ctypes.c_ushort),
                                ("text", ctypes.c_wchar * len(text))]
                entry = Entry(len(text), text)
                data += memoryview(entry).tobytes()
            self.add(type=_wapi.RT_STRING, name=key, value=data,
                     langid=0x04b00409) # US english

        self._strings = {}

    def add_icon(self, resource_id, iconpath):
        # Each RT_ICON resource in an image file (containing the icon
        # for one specific resolution and number of colors) must have
        # a unique id, and the id must be in the GRPICONDIRHEADER's
        # nID member.

        # So, we use a *static* variable rt_icon_id which is
        # incremented for each RT_ICON resource and written into the
        # GRPICONDIRHEADER's nID member.
        with open(iconpath, "rb") as ifi:
            hdr = icons.ICONDIRHEADER.readfrom(ifi)

        # CreateGrpIconDirHeader creates RT_ICON resources for each
        # image in the icon file; for this it needs separate resource
        # ids.  We start with resource_id*100 and increment it for
        # each image.  All these ids must be unique for the exe-file.
        grp_header = icons.CreateGrpIconDirHeader(hdr, resource_id*100)

        # Maybe we should manage the resource ids for the RT_ICON
        # resources here, in this class?
        for i, entry in enumerate(grp_header.idEntries):
            self.add(type=_wapi.RT_ICON, name=entry.nID, value=hdr.iconimages[i])

        self.add(type=_wapi.RT_GROUP_ICON, name=resource_id, value=grp_header.tobytes())
