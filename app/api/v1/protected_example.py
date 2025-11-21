"""Example router demonstrating authentication and authorization usage"""
from fastapi import APIRouter, Depends
from app.core.security import (
    get_current_user,
    get_current_user_with_sync,
    require_role,
    require_role_with_sync,
    require_permission,
    require_any_role,
    require_all_roles,
    usePermission,
    usePermissionWithSync,
)
from app.schemas.auth import TokenData

router = APIRouter(prefix="/example", tags=["Example - Protected Endpoints"])


@router.get("/public")
async def public_endpoint():
    """Public endpoint - no authentication required"""
    return {"message": "This is a public endpoint"}


@router.get("/protected")
async def protected_endpoint(current_user: TokenData = Depends(get_current_user_with_sync)):
    """Protected endpoint - requires valid token"""
    return {
        "message": "This is a protected endpoint",
        "organization_id": current_user.organization_id,
        "organization_name": current_user.organization_name,
        "user": {
            "user_id": current_user.user.user_id,
            "name": current_user.user.name,
            "email": current_user.user.email,
            "username": current_user.user.username,
        }
    }


@router.get("/admin")
async def admin_endpoint(current_user: TokenData = Depends(require_role("Admin"))):
    """Admin only endpoint - requires 'Admin' role"""
    return {
        "message": "Welcome Admin!",
        "user": current_user.user.name,
        "roles": current_user.roles
    }


@router.get("/admin-alt")
async def admin_alt_endpoint(current_user: TokenData = Depends(usePermission("Admin"))):
    """Admin only endpoint - using usePermission alias"""
    return {
        "message": "Welcome Admin (via usePermission)!",
        "user": current_user.user.name,
        "roles": current_user.roles
    }


@router.get("/staff")
async def staff_endpoint(
    current_user: TokenData = Depends(require_any_role("Admin", "Manager", "Staff"))
):
    """Staff endpoint - requires any of: Admin, Manager, or Staff role"""
    return {
        "message": "Welcome staff member!",
        "user": current_user.user.name,
        "role_matched": [r for r in ["Admin", "Manager", "Staff"] if r in current_user.roles]
    }


@router.get("/super-admin")
async def super_admin_endpoint(
    current_user: TokenData = Depends(require_all_roles("Admin", "SuperUser"))
):
    """Super admin endpoint - requires both 'Admin' AND 'SuperUser' roles"""
    return {
        "message": "Welcome Super Admin!",
        "user": current_user.user.name,
        "roles": current_user.roles
    }


@router.get("/with-permission")
async def permission_endpoint(
    current_user: TokenData = Depends(require_permission("read:sensitive"))
):
    """Permission-based endpoint - requires 'read:sensitive' permission"""
    return {
        "message": "Permission granted",
        "user": current_user.user.name,
        "permissions": current_user.permissions
    }


@router.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user information from token (no DB sync)"""
    return {
        "organization_id": current_user.organization_id,
        "organization_name": current_user.organization_name,
        "user": {
            "user_id": current_user.user.user_id,
            "name": current_user.user.name,
            "given_name": current_user.user.given_name,
            "family_name": current_user.user.family_name,
            "username": current_user.user.username,
            "email": current_user.user.email,
        },
        "roles": current_user.roles,
        "permissions": current_user.permissions,
    }


@router.get("/me-with-sync")
async def get_me_with_sync(current_user: TokenData = Depends(get_current_user_with_sync)):
    """
    Get current user information and auto-sync to database

    This endpoint will:
    1. Validate token
    2. Extract user data
    3. Automatically sync organization to database (create/update)
    4. Automatically sync user to database (create/update)
    """
    return {
        "message": "User data synced to database",
        "organization_id": current_user.organization_id,
        "organization_name": current_user.organization_name,
        "user": {
            "user_id": current_user.user.user_id,
            "name": current_user.user.name,
            "given_name": current_user.user.given_name,
            "family_name": current_user.user.family_name,
            "username": current_user.user.username,
            "email": current_user.user.email,
        },
        "roles": current_user.roles,
        "permissions": current_user.permissions,
    }


@router.get("/admin-with-sync")
async def admin_with_sync(current_user: TokenData = Depends(usePermissionWithSync("admin_hotel"))):
    """
    Admin endpoint with automatic database sync

    Requires 'admin_hotel' role and automatically syncs user data to database
    """
    return {
        "message": "Admin access granted (with DB sync)",
        "user": current_user.user.name,
        "organization": current_user.organization_name,
        "roles": current_user.roles
    }
