# coding: utf-8

from starlette.applications import Starlette


bp = Starlette()
bp.debug = True


from . import (index,) # NOQA
