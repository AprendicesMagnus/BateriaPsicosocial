from fastapi import HTTPException, status


def error_http(status_code: int, mensaje: str, **extra) -> HTTPException:
    payload = {"error": mensaje, **extra}
    return HTTPException(status_code=status_code, detail=payload)


class AppError(HTTPException):
    def __init__(self, status_code: int, mensaje: str, **extra):
        super().__init__(status_code=status_code, detail={"error": mensaje, **extra})
