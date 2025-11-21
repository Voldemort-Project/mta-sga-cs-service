"""Security utilities for JWT token validation and authorization"""
from typing import Optional, Callable, Tuple
from functools import wraps
import httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import TokenData, UserInfo

# Security scheme for bearer token
security = HTTPBearer()


class KeycloakClient:
    """Keycloak client for token validation"""

    def __init__(self):
        self._public_key: Optional[str] = None
        self._jwks: Optional[dict] = None

    async def get_public_key(self) -> str:
        """Get Keycloak public key for token verification using JWKS endpoint"""
        if self._public_key:
            return self._public_key

        # Try JWKS endpoint first (more reliable and standard)
        certs_url = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"

        async with httpx.AsyncClient(
            verify=settings.keycloak_verify_ssl,
            timeout=10.0,
            follow_redirects=True
        ) as client:
            try:
                # Get JWKS (JSON Web Key Set)
                response = await client.get(certs_url)
                response.raise_for_status()
                jwks = response.json()

                # Get first key (usually there's only one, or we can use kid to match)
                keys = jwks.get("keys", [])
                if not keys:
                    raise ValueError("No keys found in JWKS")

                # Store JWKS for future use
                self._jwks = jwks

                # For RS256, we need to construct the public key from the JWK
                # python-jose can handle JWKS directly, so we'll return the JWKS
                # and modify validate_token to use it
                return jwks

            except httpx.HTTPError as e:
                # Fallback: Try getting public key from realm info endpoint
                try:
                    realm_url = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
                    response = await client.get(realm_url)
                    response.raise_for_status()
                    realm_info = response.json()

                    # Format public key
                    public_key = realm_info.get("public_key")
                    if not public_key:
                        raise ValueError("Public key not found in realm info")

                    self._public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
                    return self._public_key

                except httpx.HTTPError as fallback_error:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Could not connect to Keycloak: {str(e)}. Fallback also failed: {str(fallback_error)}"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Error fetching Keycloak public key: {str(e)}"
                )


# Global Keycloak client instance
keycloak_client = KeycloakClient()


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validate JWT token from Keycloak

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Get public key/JWKS from Keycloak
        key_data = await keycloak_client.get_public_key()

        # Decode and validate token
        # audience verification might fail with some Keycloak configs, so make it optional
        options = {
            "verify_signature": True,
            "verify_aud": False,  # Some Keycloak setups don't include aud claim
            "verify_exp": True,
        }

        # If key_data is a dict (JWKS), use it directly
        # If it's a string, it's a PEM-formatted public key
        if isinstance(key_data, dict):
            # JWKS format - python-jose will handle it
            payload = jwt.decode(
                token,
                key_data,
                algorithms=[settings.jwt_algorithm],
                options=options
            )
        else:
            # PEM format public key
            audience = settings.jwt_audience or settings.keycloak_client_id
            payload = jwt.decode(
                token,
                key_data,
                algorithms=[settings.jwt_algorithm],
                audience=audience,
                options=options
            )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_payload: dict = Depends(validate_token)
) -> TokenData:
    """
    Extract user data from validated token

    Args:
        token_payload: Decoded token from validate_token dependency

    Returns:
        TokenData: Structured user and organization data

    Raises:
        HTTPException: If required fields are missing from token
    """
    try:
        # Extract user_id from sub claim
        user_id = token_payload.get("sub", "")

        # Extract user information
        user_info = UserInfo(
            user_id=user_id,
            name=token_payload.get("name", ""),
            given_name=token_payload.get("given_name", ""),
            family_name=token_payload.get("family_name", ""),
            username=token_payload.get("preferred_username", ""),
            email=token_payload.get("email", "")
        )

        # Extract organization data
        # Format: {"DevHotel": {"id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1"}}
        organization_data = token_payload.get("organization", {})
        organization_name = ""
        organization_id = ""

        if isinstance(organization_data, dict) and organization_data:
            # Get first organization (assuming user belongs to one org)
            organization_name = list(organization_data.keys())[0]
            org_details = organization_data.get(organization_name, {})
            organization_id = org_details.get("id", "") if isinstance(org_details, dict) else ""

        # Fallback: try other possible organization field formats
        if not organization_name:
            organization_name = (
                token_payload.get("organization_name") or
                token_payload.get("org") or
                token_payload.get("company") or
                ""
            )

        # Extract roles and permissions
        # Keycloak typically stores roles in: realm_access.roles, resource_access.{client}.roles
        realm_roles = token_payload.get("realm_access", {}).get("roles", [])
        client_roles = token_payload.get("resource_access", {}).get(
            settings.keycloak_client_id, {}
        ).get("roles", [])

        # Combine all roles
        all_roles = list(set(realm_roles + client_roles))

        # Extract permissions if using Authorization Services
        permissions = token_payload.get("authorization", {}).get("permissions", [])
        if isinstance(permissions, list):
            permission_list = [p.get("rsname", "") for p in permissions if isinstance(p, dict)]
        else:
            permission_list = []

        # Create TokenData object
        token_data = TokenData(
            organization_id=organization_id,
            organization_name=organization_name,
            user=user_info,
            roles=all_roles,
            permissions=permission_list,
            exp=token_payload.get("exp", 0)
        )

        return token_data

    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token structure: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str) -> Callable:
    """
    Dependency factory for role-based access control

    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: TokenData = Depends(require_role("Admin"))):
            return {"message": "Admin access granted"}

    Args:
        required_role: Role name that user must have

    Returns:
        Dependency function that validates user has required role
    """
    async def check_role(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required for this operation"
            )
        return current_user

    return check_role


def require_permission(required_permission: str) -> Callable:
    """
    Dependency factory for permission-based access control

    Usage:
        @app.get("/sensitive")
        async def sensitive_endpoint(
            user: TokenData = Depends(require_permission("read:sensitive"))
        ):
            return {"message": "Permission granted"}

    Args:
        required_permission: Permission name that user must have

    Returns:
        Dependency function that validates user has required permission
    """
    async def check_permission(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if required_permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required for this operation"
            )
        return current_user

    return check_permission


def require_any_role(*roles: str) -> Callable:
    """
    Dependency factory for role-based access control (any of the roles)

    Usage:
        @app.get("/staff")
        async def staff_endpoint(
            user: TokenData = Depends(require_any_role("Admin", "Manager", "Staff"))
        ):
            return {"message": "Staff access granted"}

    Args:
        *roles: Role names, user must have at least one

    Returns:
        Dependency function that validates user has at least one required role
    """
    async def check_roles(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if not any(role in current_user.roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(roles)}"
            )
        return current_user

    return check_roles


def require_all_roles(*roles: str) -> Callable:
    """
    Dependency factory for role-based access control (all roles required)

    Usage:
        @app.get("/super-admin")
        async def super_admin_endpoint(
            user: TokenData = Depends(require_all_roles("Admin", "SuperUser"))
        ):
            return {"message": "Super admin access granted"}

    Args:
        *roles: Role names, user must have all of them

    Returns:
        Dependency function that validates user has all required roles
    """
    async def check_roles(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if not all(role in current_user.roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All of these roles required: {', '.join(roles)}"
            )
        return current_user

    return check_roles


# Alias for backward compatibility with your example
def usePermission(role: str) -> Callable:
    """
    Alias for require_role to match your example usage

    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: TokenData = Depends(usePermission("Admin"))):
            return {"message": "Admin access granted"}

    Args:
        role: Role name that user must have

    Returns:
        Dependency function that validates user has required role
    """
    return require_role(role)


async def get_current_user_with_sync(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TokenData:
    """
    Get current user and automatically sync organization and user data to database

    This dependency will:
    1. Validate token and extract user data (via get_current_user)
    2. Sync organization to database (create if not exists, update if changed)
    3. Sync user to database (create if not exists, update if changed)

    Usage:
        @app.get("/profile")
        async def get_profile(current_user: TokenData = Depends(get_current_user_with_sync)):
            # Organization and user are automatically synced to database
            return {
                "user_id": current_user.user.user_id,
                "organization_id": current_user.organization_id
            }

    Args:
        current_user: Token data from get_current_user dependency
        db: Database session

    Returns:
        TokenData: The current user token data (after sync)
    """
    # Import here to avoid circular import
    from app.services.auth_sync_service import sync_auth_data

    try:
        # Sync organization and user to database
        await sync_auth_data(db, current_user)
        return current_user
    except Exception as e:
        # Log error with full traceback for debugging
        import traceback
        print(f"ERROR: Failed to sync auth data to database")
        print(f"Error details: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")

        # Re-raise the error so user can see what went wrong
        # Comment this out in production if you want auth to work even if sync fails
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync user data to database: {str(e)}"
        )


def require_role_with_sync(required_role: str) -> Callable:
    """
    Role-based guard with automatic database sync

    Combines role checking with automatic sync of organization and user to database.

    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: TokenData = Depends(require_role_with_sync("Admin"))):
            # User has been validated, role checked, and synced to database
            return {"message": "Admin access granted"}

    Args:
        required_role: Role name that user must have

    Returns:
        Dependency function that validates role and syncs to database
    """
    async def check_role_and_sync(
        current_user: TokenData = Depends(get_current_user_with_sync)
    ) -> TokenData:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required for this operation"
            )
        return current_user

    return check_role_and_sync


def usePermissionWithSync(role: str) -> Callable:
    """
    Alias for require_role_with_sync with automatic database sync

    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: TokenData = Depends(usePermissionWithSync("Admin"))):
            # User validated, role checked, and automatically synced to database
            return {"message": "Admin access granted"}

    Args:
        role: Role name that user must have

    Returns:
        Dependency function that validates role and syncs to database
    """
    return require_role_with_sync(role)
