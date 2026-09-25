from typing import Type
from fastapi import Depends
from source.application.interfaces import IGroupRepository
from source.application.use_cases import (
    CreateGroup,
    EditGroup,
    DeleteGroup,
    AddUserToGroup,
    RemoveUserFromGroup,
    GetUsersInGroup,
)
from source.presentation.api.dependencies.adapters import get_group_repository


class GroupUseCaseFactory:
    def __init__(self, use_case_class: Type):
        self.use_case_class = use_case_class

    async def __call__(self, repo: IGroupRepository = Depends(get_group_repository)):
        return self.use_case_class(repo=repo)


get_create_group_use_case = GroupUseCaseFactory(CreateGroup)
get_edit_group_use_case = GroupUseCaseFactory(EditGroup)
get_delete_group_use_case = GroupUseCaseFactory(DeleteGroup)
get_add_user_to_group_use_case = GroupUseCaseFactory(AddUserToGroup)
get_remove_user_from_group_use_case = GroupUseCaseFactory(RemoveUserFromGroup)
get_get_users_in_group_use_case = GroupUseCaseFactory(GetUsersInGroup)
