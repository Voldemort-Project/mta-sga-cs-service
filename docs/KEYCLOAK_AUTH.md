# Keycloak Authentication & Authorization

Dokumentasi untuk menggunakan authentication dan authorization dengan Keycloak di sga-cs-service.

## 📋 Overview

Service ini menggunakan Keycloak sebagai Identity Provider (IdP) dengan JWT Bearer token authentication. Sistem ini menyediakan:

1. **Validasi Token** - Memvalidasi JWT token dari Keycloak
2. **Role-based Access Control (RBAC)** - Guard berdasarkan role user
3. **Permission-based Access Control** - Guard berdasarkan permission
4. **User Data Extraction** - Extract informasi user dari token

## ⚠️ Important: Keycloak Version Compatibility

URL configuration depends on your Keycloak version:

**Keycloak 17 and older (with `/auth` prefix):**
```env
KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech/auth
```

**Keycloak 18+ (without `/auth` prefix):**
```env
KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech
```

Our implementation automatically uses JWKS endpoint with fallback to realm info for maximum compatibility.

## 🔧 Configuration

Tambahkan konfigurasi berikut di file `.env`:

```env
# Keycloak Configuration
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=sga-cs-service
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_VERIFY_SSL=true

# JWT Settings
JWT_ALGORITHM=RS256
JWT_AUDIENCE=sga-cs-service  # Optional, defaults to client_id
```

## 📦 Dependencies

Dependencies sudah ditambahkan di `pyproject.toml`:

```toml
"python-jose[cryptography]>=3.3.0",
"cryptography>=41.0.0",
```

Install dependencies:

```bash
# Using uv (recommended)
uv pip install -e .

# Using pip
pip install -e .
```

## 🎯 Usage

### 1. Basic Authentication - Token Validation

Endpoint yang hanya memerlukan token valid:

```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.schemas.auth import TokenData

router = APIRouter()

@router.get("/protected")
async def protected_endpoint(current_user: TokenData = Depends(get_current_user)):
    """Requires valid JWT token"""
    return {
        "organization_id": current_user.organization_id,
        "organization_name": current_user.organization_name,
        "user": {
            "user_id": current_user.user.user_id,
            "name": current_user.user.name,
            "email": current_user.user.email,
            "username": current_user.user.username,
        }
    }
```

### 2. Role-Based Access Control

#### Single Role Required

```python
from fastapi import APIRouter, Depends
from app.core.security import require_role, usePermission
from app.schemas.auth import TokenData

router = APIRouter()

# Method 1: Using require_role
@router.get("/admin")
async def admin_endpoint(current_user: TokenData = Depends(require_role("Admin"))):
    """Requires 'Admin' role"""
    return {"message": "Admin access granted"}

# Method 2: Using usePermission (alias)
@router.get("/admin-alt")
async def admin_alt(current_user: TokenData = Depends(usePermission("Admin"))):
    """Requires 'Admin' role - using alias"""
    return {"message": "Admin access granted"}
```

#### Multiple Roles (Any)

User harus memiliki **salah satu** dari role yang disebutkan:

```python
from app.core.security import require_any_role

@router.get("/staff")
async def staff_endpoint(
    current_user: TokenData = Depends(require_any_role("Admin", "Manager", "Staff"))
):
    """Requires Admin OR Manager OR Staff role"""
    return {"message": "Staff access granted"}
```

#### Multiple Roles (All)

User harus memiliki **semua** role yang disebutkan:

```python
from app.core.security import require_all_roles

@router.get("/super-admin")
async def super_admin(
    current_user: TokenData = Depends(require_all_roles("Admin", "SuperUser"))
):
    """Requires Admin AND SuperUser roles"""
    return {"message": "Super admin access granted"}
```

### 3. Permission-Based Access Control

```python
from app.core.security import require_permission

@router.get("/sensitive")
async def sensitive_endpoint(
    current_user: TokenData = Depends(require_permission("read:sensitive"))
):
    """Requires 'read:sensitive' permission"""
    return {"message": "Permission granted"}
```

### 4. Get User Information

```python
@router.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user information"""
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
```

## 📊 Token Data Structure

Data yang di-extract dari token:

```python
class TokenData(BaseModel):
    organization_id: str   # Organization ID
    organization_name: str # Nama organisasi
    user: UserInfo        # Informasi user
    roles: list[str]      # List role user
    permissions: list[str] # List permission user
    exp: int              # Token expiration timestamp

class UserInfo(BaseModel):
    user_id: str      # User ID (from sub claim)
    name: str         # Full name
    given_name: str   # First name
    family_name: str  # Last name
    username: str     # Username
    email: str        # Email address
```

## 🔐 How It Works

### Token Validation Flow

1. Client mengirim request dengan header: `Authorization: Bearer <token>`
2. `HTTPBearer` security scheme extract token dari header
3. `validate_token()` dependency:
   - Fetch JWKS (JSON Web Key Set) dari Keycloak `/protocol/openid-connect/certs` endpoint
   - Fallback ke realm info endpoint jika JWKS gagal
   - Decode dan validate JWT signature
   - Verify token expiration
   - Audience verification disabled by default (untuk kompatibilitas dengan berbagai Keycloak setup)
4. `get_current_user()` dependency:
   - Extract user data dari decoded token
   - Extract roles dari `realm_access.roles` dan `resource_access.{client}.roles`
   - Extract permissions dari `authorization.permissions`
   - Return `TokenData` object

### Role/Permission Check Flow

1. Token divalidasi dan user data di-extract (via `get_current_user`)
2. Guard function (`require_role`, `require_permission`, dll) mengecek:
   - Apakah user memiliki role/permission yang required
   - Jika tidak, raise `HTTP 403 Forbidden`
   - Jika ya, return `TokenData` untuk digunakan di endpoint

## 🧪 Testing

### Manual Testing dengan cURL

```bash
# Get token from Keycloak
TOKEN=$(curl -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=sga-cs-service" \
  -d "client_secret=your-secret" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testpass" | jq -r '.access_token')

# Call protected endpoint
curl -X GET "http://localhost:8000/api/v1/example/protected" \
  -H "Authorization: Bearer $TOKEN"

# Call admin endpoint
curl -X GET "http://localhost:8000/api/v1/example/admin" \
  -H "Authorization: Bearer $TOKEN"
```

### Testing dengan Python

```python
import httpx

# Get token
token_response = httpx.post(
    "http://localhost:8080/realms/master/protocol/openid-connect/token",
    data={
        "client_id": "sga-cs-service",
        "client_secret": "your-secret",
        "grant_type": "password",
        "username": "testuser",
        "password": "testpass",
    }
)
token = token_response.json()["access_token"]

# Call protected endpoint
response = httpx.get(
    "http://localhost:8000/api/v1/example/protected",
    headers={"Authorization": f"Bearer {token}"}
)
print(response.json())
```

## 🚨 Error Responses

### 401 Unauthorized

Token invalid, expired, atau tidak ada:

```json
{
  "detail": "Could not validate credentials: Signature has expired"
}
```

### 403 Forbidden

User tidak memiliki role/permission yang required:

```json
{
  "detail": "Role 'Admin' required for this operation"
}
```

### 503 Service Unavailable

Tidak bisa connect ke Keycloak:

```json
{
  "detail": "Could not connect to Keycloak: Connection refused"
}
```

## 📝 Available Dependencies

| Dependency | Description | Usage |
|------------|-------------|-------|
| `validate_token` | Validasi token JWT | Low-level, biasanya tidak dipakai langsung |
| `get_current_user` | Validasi token + extract user data | Basic authentication |
| `require_role(role)` | Require specific role | Single role guard |
| `usePermission(role)` | Alias untuk `require_role` | Single role guard (alternative) |
| `require_any_role(*roles)` | Require any of the roles | Multiple roles (OR) |
| `require_all_roles(*roles)` | Require all roles | Multiple roles (AND) |
| `require_permission(perm)` | Require specific permission | Permission-based guard |

## 🔄 Customization

### Custom Organization Field

Jika Keycloak Anda menggunakan field custom untuk organization, edit `app/core/security.py`:

```python
# In get_current_user function, modify:
organization_name = (
    token_payload.get("your_custom_org_field") or
    token_payload.get("organization_name") or
    token_payload.get("organization") or
    ""
)
```

### Custom Role Extraction

Jika struktur role berbeda, edit bagian role extraction:

```python
# In get_current_user function, modify:
realm_roles = token_payload.get("realm_access", {}).get("roles", [])
# Add your custom role extraction logic here
```

## 🐛 Troubleshooting

Jika mengalami masalah (seperti 405 Method Not Allowed, 401 Unauthorized, dll), lihat:
- **[KEYCLOAK_TROUBLESHOOTING.md](./KEYCLOAK_TROUBLESHOOTING.md)** - Panduan troubleshooting lengkap

## 📚 References

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [JWT.io](https://jwt.io/) - JWT debugger
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [Keycloak Troubleshooting](./KEYCLOAK_TROUBLESHOOTING.md) - Error solutions

## 💡 Tips

1. **Caching Public Key**: Public key di-cache setelah pertama kali di-fetch untuk menghindari request berulang ke Keycloak
2. **Token Expiration**: Token expiration di-verify otomatis oleh `python-jose`
3. **SSL Verification**: Set `KEYCLOAK_VERIFY_SSL=false` untuk development/testing saja
4. **Role Naming**: Gunakan naming convention yang konsisten untuk role (e.g., PascalCase: Admin, Manager)
5. **Permission Format**: Gunakan format `resource:action` untuk permission (e.g., `users:read`, `posts:write`)
