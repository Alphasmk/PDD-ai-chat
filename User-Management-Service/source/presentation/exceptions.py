from fastapi import status
from source.domain.exceptions.raw_password_exceptions import (
    PasswordLengthError,
    PasswordPatternError,
)
from source.domain.exceptions.email_exceptions import EmailPatternError
from source.domain.exceptions.name_exceptions import NameLengthError, NamePatternError
from source.domain.exceptions import (
    UserBlockedError,
    UserDeleteNotAllowedError,
    CannotBlockAdminError,
    AdminCannotChangeAdminsRoleError,
    AdminRegularAssignError,
    RoleIsUnassignableOrChangable,
)

from source.application.exceptions import (
    CannotCreateGroupError,
    CannotEditGroupError,
    CannotDeleteGroupError,
    CannotAddUserToGroupError,
    CannotGetGroupUsersError,
    CannotRemoveUserFromGroupError,
    GroupNotFoundError,
    GroupAlreadyExistsError,
    InvalidCredentialsError,
    EmailTakenError,
    UsernameTakenError,
    PhoneNumberTaken,
    UserNotFoundError,
    ActionNotAllowedError,
    UserEditNotAllowedError,
    UserGetInfoNotAllowed,
    ModeratorGetInfoNotAllowed,
    InvalidSortFieldError,
    TokenExpiredError,
    InvalidTokenError,
    MissingTokenError,
    TokenRevokedError,
    CannotChangeImageError,
    UploadImageError,
    UserHasNoImageError,
    ImageReceivingError,
    CannotDeleteImageError,
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
    UserBlockedError: status.HTTP_401_UNAUTHORIZED,
}

USERS_ME_ERRORS = {
    TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    MissingTokenError: status.HTTP_401_UNAUTHORIZED,
    TokenRevokedError: status.HTTP_401_UNAUTHORIZED,
}

USER_ACTIONS_ERRORS = {
    UserDeleteNotAllowedError: status.HTTP_403_FORBIDDEN,
    ActionNotAllowedError: status.HTTP_403_FORBIDDEN,
    UserEditNotAllowedError: status.HTTP_403_FORBIDDEN,
    UserGetInfoNotAllowed: status.HTTP_403_FORBIDDEN,
    ModeratorGetInfoNotAllowed: status.HTTP_403_FORBIDDEN,
    InvalidSortFieldError: status.HTTP_400_BAD_REQUEST,
    CannotBlockAdminError: status.HTTP_403_FORBIDDEN,
    AdminCannotChangeAdminsRoleError: status.HTTP_403_FORBIDDEN,
    AdminRegularAssignError: status.HTTP_403_FORBIDDEN,
    RoleIsUnassignableOrChangable: status.HTTP_403_FORBIDDEN,
    CannotChangeImageError: status.HTTP_403_FORBIDDEN,
    UploadImageError: status.HTTP_400_BAD_REQUEST,
    DeleteImageError: status.HTTP_400_BAD_REQUEST,
    UserHasNoImageError: status.HTTP_404_NOT_FOUND,
    ImageReceivingError: status.HTTP_400_BAD_REQUEST,
    CannotDeleteImageError: status.HTTP_403_FORBIDDEN,
}

GROUP_ACTIONS_ERRORS = {
    CannotCreateGroupError: status.HTTP_403_FORBIDDEN,
    CannotEditGroupError: status.HTTP_403_FORBIDDEN,
    CannotDeleteGroupError: status.HTTP_403_FORBIDDEN,
    CannotAddUserToGroupError: status.HTTP_403_FORBIDDEN,
    CannotRemoveUserFromGroupError: status.HTTP_403_FORBIDDEN,
    CannotGetGroupUsersError: status.HTTP_403_FORBIDDEN,
    GroupNotFoundError: status.HTTP_404_NOT_FOUND,
    GroupAlreadyExistsError: status.HTTP_409_CONFLICT,
}

AUTH_ERROR_MAP = AUTH_ERRORS | GENERAL_ERRORS
USERS_ME_ERROR_MAP = USERS_ME_ERRORS | GENERAL_ERRORS
USER_ACTIONS_MAP = USER_ACTIONS_ERRORS | GENERAL_ERRORS
GROUP_ACTIONS_MAP = GROUP_ACTIONS_ERRORS | GENERAL_ERRORS
