from source.domain.interfaces import IPasswordHasher
from source.domain.value_objects import PasswordHash, RawPassword


class FakeHasher(IPasswordHasher):
    async def hash(self, password: RawPassword) -> PasswordHash:
        return PasswordHash(value=f"hash_{password.value}")

    async def verify(self, raw_password: str, password_hash: str) -> bool:
        return f"hash_{raw_password}" == password_hash
