# coding: utf-8

from app.libs.rest import ApiError, ApiErrors as ApiErrorsBuiltin, jsonize

from starlette.exceptions import HTTPException

from . import bp


class ApiErrors(ApiErrorsBuiltin):
    # error_code, message, status_code
    not_found = (20001, 'not_found', 404)
    forbidden = (20002, 'forbidden', 403)
    method_not_allowed = (20003, 'method_not_allowed', 405)
    unknown_config_type = (20004, 'unknown_config_type', 400)
    unknown_operation = (20005, 'unknown_operation', 400)
    unrepeatable_operation = (20006, 'unrepeatable_operation', 400)

    unknown_exception = (22001, 'unknown_exception', 400)


@bp.exception_handler(ApiError)
@jsonize
async def api_error_handler(request, exc):
    return exc.to_dict()


@bp.exception_handler(HTTPException)
@jsonize
async def http_exception_handler(request, exc):
    if exc.status_code == 404:
        return ApiError(ApiErrors.not_found).to_dict()
    if exc.status_code == 403:
        return ApiError(ApiErrors.forbidden).to_dict()
    if exc.status_code == 405:
        return ApiError(ApiErrors.method_not_allowed).to_dict()
    error = ApiError(ApiErrors.unknown_exception)
    if exc.detail:
        error.description = exc.detail
    if exc.status_code:
        error.status_code = exc.status_code
    return error.to_dict()
