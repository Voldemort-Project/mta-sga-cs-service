"""Authentication and authorization schemas"""
from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """User information from token"""
    user_id: str = Field(..., description="User ID (from sub)")
    name: str = Field(..., description="Full name")
    given_name: str = Field(..., description="Given/first name")
    family_name: str = Field(default="", description="Family/last name")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")


class TokenData(BaseModel):
    """Decoded token data"""
    organization_id: str = Field(..., description="Organization ID")
    organization_name: str = Field(..., description="Organization name")
    user: UserInfo = Field(..., description="User information")

    # Additional fields that might be useful
    roles: list[str] = Field(default_factory=list, description="User roles")
    permissions: list[str] = Field(default_factory=list, description="User permissions")
    exp: int = Field(..., description="Token expiration timestamp")
