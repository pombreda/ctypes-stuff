# -*- coding: latin-1 -*-
"""Windows SxS context manager
"""
from __future__ import division, with_statement, absolute_import

import os
import wapi
from contextlib import contextmanager

class Context(object):
    _handle = None
    def __init__(self, manifest):
        self.manifest = manifest
        ctx = wapi.ACTCTXW()
        ctx.cbSize = wapi.sizeof(ctx)
        ctx.dwFlags = wapi.ACTCTX_FLAG_RESOURCE_NAME_VALID
        ctx.lpSource = os.path.abspath(manifest)
        ctx.lpResourceName = wapi.MAKEINTRESOURCE(2)
        self._handle = wapi.CreateActCtxW(ctx)

    def Activate(self):
        cookie = wapi.ULONG_PTR()
        wapi.ActivateActCtx(self._handle, cookie)
        return cookie

    def Deactivate(self, cookie):
        wapi.DeactivateActCtx(0, cookie)

    @contextmanager
    def activate(self):
        cookie = self.Activate()
        yield
        self.Deactivate(cookie)

