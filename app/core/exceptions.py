class AppError(Exception):
    """
    Base class for errors the API reports to clients with a specific
    status code. Anything else is treated as an unexpected 500.
    """

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)

    default_message = "Internal server error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "Resource not found"


class ValidationFailedError(AppError):
    status_code = 422
    code = "validation_failed"
    default_message = "Invalid request"


class DatabaseUnavailableError(AppError):
    status_code = 503
    code = "database_unavailable"
    default_message = "Database is unavailable"


class UnsupportedFileTypeError(AppError):
    status_code = 415
    code = "unsupported_file_type"
    default_message = "Unsupported file type"


class FileTooLargeError(AppError):
    status_code = 413
    code = "file_too_large"
    default_message = "File is too large"


class InvalidUploadError(AppError):
    status_code = 400
    code = "invalid_upload"
    default_message = "The uploaded file is empty or damaged"
