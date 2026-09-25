import bcrypt
import asyncio
from source.domain.interfaces import IPasswordHasher
from source.domain.value_objects import RawPassword, PasswordHash


class PasswordHasher(IPasswordHasher):
    async def hash(self, password: RawPassword) -> PasswordHash:
        pwd_bytes = password.value.encode("utf-8")
        salt = await asyncio.to_thread(bcrypt.gensalt)
        hashed = await asyncio.to_thread(bcrypt.hashpw, pwd_bytes, salt)
        return PasswordHash(hashed.decode("utf-8"))

    async def verify(self, raw_password: str, password_hash: str) -> bool:
        return await asyncio.to_thread(
            bcrypt.checkpw, raw_password.encode("utf-8"), password_hash.encode("utf-8")
        )
