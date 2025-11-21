# Keycloak Auth - Quick Reference

## 🚀 Quick Start

### 1. Setup Environment Variables

```env
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=sga-cs-service
KEYCLOAK_CLIENT_SECRET=your-secret
```

### 2. Import Dependencies

```python
from fastapi import APIRouter, Depends
from app.core.security import (
    get_current_user,
    require_role,
    usePermission,
    require_any_role,
    require_all_roles,
    require_permission,
)
from app.schemas.auth import TokenData
```

## 📋 Common Patterns

### Basic Protected Endpoint

```python
@router.get("/protected")
async def protected(current_user: TokenData = Depends(get_current_user)):
    return {"user": current_user.user.name}
```

### Admin Only

```python
@router.get("/admin")
async def admin(current_user: TokenData = Depends(require_role("Admin"))):
    return {"message": "Admin only"}

# Or using alias
@router.get("/admin")
async def admin(current_user: TokenData = Depends(usePermission("Admin"))):
    return {"message": "Admin only"}
```

### Multiple Roles (Any)

```python
@router.get("/staff")
async def staff(
    current_user: TokenData = Depends(require_any_role("Admin", "Manager", "Staff"))
):
    return {"message": "Staff area"}
```

### Multiple Roles (All)

```python
@router.get("/super")
async def super_admin(
    current_user: TokenData = Depends(require_all_roles("Admin", "SuperUser"))
):
    return {"message": "Super admin only"}
```

### Permission-Based

```python
@router.get("/sensitive")
async def sensitive(
    current_user: TokenData = Depends(require_permission("read:sensitive"))
):
    return {"message": "Sensitive data"}
```

## 📊 Token Data Format

```python
{
    "organization_id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1",
    "organization_name": "DevHotel",
    "user": {
        "user_id": "6b6915dd-1f56-446b-ba46-3abfb532f9cd",
        "name": "John Doe",
        "given_name": "John",
        "family_name": "Doe",
        "username": "johndoe",
        "email": "john@example.com"
    },
    "roles": ["Admin", "Manager"],
    "permissions": ["read:users", "write:users"],
    "exp": 1234567890
}
```

## 🔑 Get Token (Testing)

```bash
curl -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=sga-cs-service" \
  -d "client_secret=your-secret" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testpass"
```

## 📞 Call Protected Endpoint

```bash
curl -X GET "http://localhost:8000/api/v1/example/protected" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🚨 Error Codes

- **401 Unauthorized**: Token invalid/expired
- **403 Forbidden**: Missing required role/permission
- **503 Service Unavailable**: Cannot connect to Keycloak

## 📚 Full Documentation

See [KEYCLOAK_AUTH.md](./KEYCLOAK_AUTH.md) for complete documentation.
