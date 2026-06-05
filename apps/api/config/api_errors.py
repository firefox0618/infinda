from collections.abc import Mapping

from rest_framework import status
from rest_framework.views import exception_handler


DEFAULT_ERROR_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: "Validation error.",
    status.HTTP_401_UNAUTHORIZED: "Authentication failed.",
    status.HTTP_403_FORBIDDEN: "Permission denied.",
    status.HTTP_404_NOT_FOUND: "Resource not found.",
}

DEFAULT_ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "VALIDATION_ERROR",
    status.HTTP_401_UNAUTHORIZED: "AUTHENTICATION_FAILED",
    status.HTTP_403_FORBIDDEN: "PERMISSION_DENIED",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
}


def _normalize_error_details(data):
    if isinstance(data, Mapping):
        normalized = dict(data)
        detail = normalized.pop("detail", None)

        if normalized:
            return detail, normalized

        return detail, {}

    if isinstance(data, list):
        return None, {"items": data}

    return data, {}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    detail_message, details = _normalize_error_details(response.data)
    default_message = DEFAULT_ERROR_MESSAGES.get(response.status_code, "Request failed.")
    default_code = DEFAULT_ERROR_CODES.get(response.status_code, "API_ERROR")

    error_code = getattr(exc, "default_code", None)
    if isinstance(error_code, str):
        error_code = error_code.upper()
        if error_code == "INVALID":
            error_code = default_code
    else:
        error_code = default_code

    response.data = {
        "error": {
            "code": error_code,
            "message": detail_message or default_message,
            "details": details,
        }
    }

    return response
