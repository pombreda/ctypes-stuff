#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""resources for py3exe
"""
import _wapi

import contextlib

@contextlib.contextmanager
def UpdateResources(filename, *, delete_existing=False):
    hrscr = _wapi.BeginUpdateResourceW(filename, delete_existing)
    yield ResourceWriter(hrscr, filename)
    _wapi.EndUpdateResourceW(hrscr, False)

class ResourceWriter(object):
    def __init__(self, hrscr, filename):
        self._hrscr = hrscr
        self._filename = filename
        
    def add(self, res_type, res_name, res_data):
        print("Add RSC %s/%s %d bytes to %s" % (res_type, res_name, len(res_data), self._filename))
        try:
            _wapi.UpdateResourceW(self._hrscr,
                                  _wapi.LPCWSTR(res_type),
                                  _wapi.LPCWSTR(res_name),
                                  0, # wLanguage
                                  res_data,
                                  len(res_data))
        except WindowsError as details:
            raise WindowsError(details) from None
