from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        return None

    response.data = {"success": False, "message": _extract_message(response.data)}
    return response


def _extract_message(data):
    if isinstance(data, dict):
        for key in ("detail", "non_field_errors"):
            if key in data:
                value = data[key]
                return str(value[0]) if isinstance(value, list) else str(value)
        for key, value in data.items():
            first = value[0] if isinstance(value, list) else value
            return f"{key}: {first}"
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)
