from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
from source.domain.exceptions import (
    PasswordLengthError,
    PasswordPatternError,
    EmailPatternError,
    NameLengthError,
    NamePatternError,
)
from source.application.exceptions import (
    InvalidCredentialsError,
    EmailTakenError,
    UsernameTakenError,
    PhoneNumberTaken,
    UserNotFoundError,
    TokenExpiredError,
    InvalidTokenError,
    MissingTokenError,
    TokenRevokedError,
    UploadImageError,
    UserHasNoImageError,
    ImageReceivingError,
    DeleteImageError,
)

GENERAL_ERRORS = {
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    PasswordPatternError: status.HTTP_400_BAD_REQUEST,
    PasswordLengthError: status.HTTP_400_BAD_REQUEST,
    EmailPatternError: status.HTTP_400_BAD_REQUEST,
    NamePatternError: status.HTTP_400_BAD_REQUEST,
    NameLengthError: status.HTTP_400_BAD_REQUEST,
    UsernameTakenError: status.HTTP_409_CONFLICT,
    EmailTakenError: status.HTTP_409_CONFLICT,
    PhoneNumberTaken: status.HTTP_409_CONFLICT,
}
AUTH_ERRORS = {
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    MissingTokenError: status.HTTP_401_UNAUTHORIZED,
    TokenRevokedError: status.HTTP_401_UNAUTHORIZED,
}
USER_ACTIONS_ERRORS = {
    UploadImageError: status.HTTP_400_BAD_REQUEST,
    DeleteImageError: status.HTTP_400_BAD_REQUEST,
    UserHasNoImageError: status.HTTP_404_NOT_FOUND,
    ImageReceivingError: status.HTTP_400_BAD_REQUEST,
}
AUTH_ERROR_MAP = AUTH_ERRORS | GENERAL_ERRORS
USERS_ME_ERROR_MAP = AUTH_ERROR_MAP
USER_ACTIONS_MAP = USER_ACTIONS_ERRORS | AUTH_ERROR_MAP


ERROR_STATUS: dict[type[Exception], int] = USER_ACTIONS_MAP


async def application_error_handler(
    request: Request, exception: Exception
) -> JSONResponse:
    status_code = ERROR_STATUS.get(type(exception))
    if status_code is None:
        raise exception
    return JSONResponse(status_code=status_code, content={"error": str(exception)})
