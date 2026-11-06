from pydantic import BaseModel, Field, ConfigDict


class Credentials(BaseModel):
    email: str = Field(
        min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    )
    password: str = Field(min_length=12, max_length=128)


class Registration(Credentials):
    name: str = Field(min_length=2, max_length=100)
    organization: str = Field(min_length=2, max_length=100)


class Named(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)


class MemberInput(BaseModel):
    email: str = Field(max_length=254)
    role: str = Field(pattern="^(admin|member|viewer)$")


class RoleInput(BaseModel):
    role: str = Field(pattern="^(admin|member|viewer)$")


class ChatInput(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    conversation_id: str | None = None


class DocumentUpdate(BaseModel):
    visibility: str = Field(pattern="^(private|organization)$")
    workspace_id: str | None = None


class EmailInput(BaseModel):
    email: str = Field(max_length=254)


class ResetInput(BaseModel):
    token: str = Field(max_length=200)
    password: str = Field(min_length=12, max_length=128)


class TokenInput(BaseModel):
    token: str = Field(max_length=200)
