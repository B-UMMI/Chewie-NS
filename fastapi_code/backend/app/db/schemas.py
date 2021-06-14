from pydantic import BaseModel
import typing as t


class UserBase(BaseModel):
    email: str
    username: str
    name: str
    organization: str
    is_active: bool = True
    is_contributor: bool = False
    is_superuser: bool = False
    can_sync: bool = False


class UserOut(UserBase):
    pass


class UserCreate(UserBase):
    password: str

    class Config:
        orm_mode = True


class UserEdit(UserBase):
    password: t.Optional[str] = None

    class Config:
        orm_mode = True


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str = None
    permissions: str = "user"
