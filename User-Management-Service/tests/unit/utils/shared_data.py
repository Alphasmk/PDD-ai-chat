__test__ = False

from uuid import UUID
from source.domain.enums.user_role import UserRole
from source.domain.value_objects.identity import ID


BASE_USERS = dict()

BASE_USERS["SA_SELF"] = (
    UserRole.SUPER_ADMIN,
    ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
    ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
    UserRole.SUPER_ADMIN,
)
BASE_USERS["A_SELF"] = (
    UserRole.ADMIN,
    ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
    ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
    UserRole.ADMIN,
)
BASE_USERS["M_SELF"] = (
    UserRole.MODERATOR,
    ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
    ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
    UserRole.MODERATOR,
)
BASE_USERS["U_SELF"] = (
    UserRole.USER,
    ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
    ID(UUID("9ba9cdb9-41ce-401e-bb1d-8ce561e5fb11")),
    UserRole.USER,
)
BASE_USERS["A_TO_U"] = (UserRole.ADMIN, ID(), ID(), UserRole.USER)
BASE_USERS["SA_TO_U"] = (UserRole.SUPER_ADMIN, ID(), ID(), UserRole.USER)
BASE_USERS["SA_TO_A"] = (UserRole.SUPER_ADMIN, ID(), ID(), UserRole.ADMIN)
BASE_USERS["A_TO_SA"] = (UserRole.ADMIN, ID(), ID(), UserRole.SUPER_ADMIN)
BASE_USERS["M_TO_U"] = (UserRole.MODERATOR, ID(), ID(), UserRole.USER)
BASE_USERS["U_TO_U"] = (UserRole.USER, ID(), ID(), UserRole.USER)
BASE_USERS["U_TO_M"] = (UserRole.USER, ID(), ID(), UserRole.MODERATOR)
BASE_USERS["U_TO_A"] = (UserRole.USER, ID(), ID(), UserRole.ADMIN)
