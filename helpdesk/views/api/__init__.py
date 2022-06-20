# coding: utf-8

from fastapi import APIRouter

router = APIRouter()


from . import index, auth, approval_flow # NOQA
