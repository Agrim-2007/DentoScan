class AppError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class InvalidFileError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=400)


class ProcessingError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=500)


class ExternalServiceError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=502)


class ServiceConfigurationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=503)
