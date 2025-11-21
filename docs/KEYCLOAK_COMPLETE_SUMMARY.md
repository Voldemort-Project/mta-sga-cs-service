# Keycloak Authentication - Complete Summary

## ✅ Status: WORKING

Sistem authentication Keycloak sudah berfungsi dengan format token yang sesuai dengan Keycloak setup Anda.

## 🎯 Fitur yang Berhasil Diimplementasikan

### 1. ✅ Validasi Token
- Menggunakan JWKS endpoint (`/protocol/openid-connect/certs`)
- Fallback ke realm info endpoint jika JWKS gagal
- Verifikasi JWT signature menggunakan public key Keycloak
- Verifikasi token expiration

### 2. ✅ Role-Based Guards
```python
# Single role
@router.get("/admin")
async def admin(user: TokenData = Depends(usePermission("admin_hotel"))):
    pass

# Multiple roles (any)
@router.get("/staff")
async def staff(user: TokenData = Depends(require_any_role("admin_hotel", "manager"))):
    pass

# Multiple roles (all)
@router.get("/super")
async def super_admin(user: TokenData = Depends(require_all_roles("admin", "super"))):
    pass
```

### 3. ✅ Token Data Extraction

Format data yang di-extract sesuai dengan struktur token Keycloak Anda:

```json
{
  "organization_id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1",
  "organization_name": "DevHotel",
  "user": {
    "user_id": "6b6915dd-1f56-446b-ba46-3abfb532f9cd",
    "name": "admin Dev hotel",
    "given_name": "admin",
    "family_name": "Dev hotel",
    "username": "admin@dev-hotels123.com",
    "email": "admin@dev-hotels123.com"
  },
  "roles": ["admin_hotel", "offline_access", "default-roles-claim-mind", "uma_authorization"],
  "permissions": [],
  "exp": 1763753926
}
```

## 📊 Token Structure (Your Keycloak)

Struktur token dari Keycloak Anda:

```json
{
  "sub": "6b6915dd-1f56-446b-ba46-3abfb532f9cd",
  "name": "admin Dev hotel",
  "given_name": "admin",
  "family_name": "Dev hotel",
  "preferred_username": "admin@dev-hotels123.com",
  "email": "admin@dev-hotels123.com",
  "organization": {
    "DevHotel": {
      "id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1"
    }
  },
  "realm_access": {
    "roles": [
      "offline_access",
      "default-roles-claim-mind",
      "admin_hotel",
      "uma_authorization"
    ]
  },
  "exp": 1763753926
}
```

## 🔄 Extraction Mapping

| Token Field | Extracted To | Notes |
|-------------|--------------|-------|
| `sub` | `user.user_id` | User ID |
| `name` | `user.name` | Full name |
| `given_name` | `user.given_name` | First name |
| `family_name` | `user.family_name` | Last name |
| `preferred_username` | `user.username` | Username (email in your case) |
| `email` | `user.email` | Email address |
| `organization` (first key) | `organization_name` | "DevHotel" |
| `organization.{key}.id` | `organization_id` | Organization UUID |
| `realm_access.roles` | `roles` | Array of role strings |
| `exp` | `exp` | Token expiration timestamp |

## ⚙️ Configuration

File `.env` Anda (berdasarkan error sebelumnya):

```env
# Keycloak Configuration
KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech/auth
KEYCLOAK_REALM=claim-mind
KEYCLOAK_CLIENT_ID=sga-cs-service
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_VERIFY_SSL=true

# JWT Settings
JWT_ALGORITHM=RS256
```

## 🚀 Usage Examples

### Basic Protected Endpoint

```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.schemas.auth import TokenData

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    """Get user profile - requires valid token"""
    return {
        "organization_id": current_user.organization_id,
        "organization_name": current_user.organization_name,
        "user_id": current_user.user.user_id,
        "email": current_user.user.email,
        "roles": current_user.roles
    }
```

### Role-Based Protection

```python
from app.core.security import usePermission

@router.get("/hotel-admin")
async def hotel_admin_only(
    current_user: TokenData = Depends(usePermission("admin_hotel"))
):
    """Only users with 'admin_hotel' role can access"""
    return {"message": f"Welcome hotel admin: {current_user.user.name}"}
```

### Access User & Organization IDs

```python
@router.post("/create-booking")
async def create_booking(
    booking_data: dict,
    current_user: TokenData = Depends(get_current_user)
):
    """Create booking with user and organization context"""

    # Access user ID
    user_id = current_user.user.user_id

    # Access organization ID
    org_id = current_user.organization_id

    # Use in your business logic
    booking = {
        "user_id": user_id,
        "organization_id": org_id,
        "user_email": current_user.user.email,
        "organization_name": current_user.organization_name,
        **booking_data
    }

    return {"booking": booking}
```

## 🧪 Testing

### 1. Get Token from Keycloak

```bash
curl -X POST "https://auth.v2.dev.mta.tech/auth/realms/claim-mind/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=web" \
  -d "client_secret=YOUR_SECRET" \
  -d "grant_type=password" \
  -d "username=admin@dev-hotels123.com" \
  -d "password=YOUR_PASSWORD"
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "expires_in": 7200,
  "refresh_token": "eyJhbGc...",
  "token_type": "Bearer"
}
```

### 2. Test Protected Endpoint

```bash
TOKEN="your-access-token-here"

curl -X GET "http://localhost:8000/api/v1/example/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "organization_id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1",
  "organization_name": "DevHotel",
  "user": {
    "user_id": "6b6915dd-1f56-446b-ba46-3abfb532f9cd",
    "name": "admin Dev hotel",
    "given_name": "admin",
    "family_name": "Dev hotel",
    "username": "admin@dev-hotels123.com",
    "email": "admin@dev-hotels123.com"
  },
  "roles": ["admin_hotel", "offline_access", "default-roles-claim-mind", "uma_authorization"],
  "permissions": []
}
```

### 3. Test Role-Based Endpoint

```bash
# Should succeed if user has 'admin_hotel' role
curl -X GET "http://localhost:8000/api/v1/example/admin" \
  -H "Authorization: Bearer $TOKEN"
```

## 📁 Files Structure

```
app/
├── core/
│   ├── config.py           # Keycloak configuration
│   └── security.py         # Token validation & guards
├── schemas/
│   └── auth.py            # TokenData & UserInfo schemas
└── api/
    └── v1/
        └── protected_example.py  # Example protected endpoints

docs/
├── KEYCLOAK_AUTH.md                    # Complete documentation
├── KEYCLOAK_AUTH_QUICKREF.md          # Quick reference
├── KEYCLOAK_TROUBLESHOOTING.md        # Troubleshooting guide
├── KEYCLOAK_FIX_SUMMARY.md            # Fix for 405 error
├── KEYCLOAK_TOKEN_FORMAT_UPDATE.md    # Token format update
└── KEYCLOAK_COMPLETE_SUMMARY.md       # This file
```

## 🔐 Security Features

- ✅ JWT signature verification menggunakan Keycloak public key
- ✅ Token expiration validation
- ✅ JWKS caching untuk performance
- ✅ Fallback mechanism untuk reliability
- ✅ Role-based access control (RBAC)
- ✅ Permission-based access control
- ✅ SSL/TLS support

## 📝 Important Notes

### Organization Data Structure

Token Keycloak Anda menggunakan struktur organization yang unik:

```json
"organization": {
  "DevHotel": {
    "id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1"
  }
}
```

Sistem akan:
1. Extract organization name dari **first key** (`"DevHotel"`)
2. Extract organization ID dari **value.id** (`"d59a4464-be0e-4516-8f8c-ca7d8fd907b1"`)

### Roles

Roles diambil dari `realm_access.roles`. Untuk check role, gunakan exact name:

```python
# Correct
Depends(usePermission("admin_hotel"))

# Wrong (case sensitive!)
Depends(usePermission("Admin_Hotel"))  # Won't work
Depends(usePermission("ADMIN_HOTEL"))  # Won't work
```

### Token Expiration

Token Anda expire dalam 7200 seconds (2 hours). Pastikan handle token refresh di client side.

## 🎉 Summary

Sistem Keycloak authentication sudah **fully working** dengan:

1. ✅ Token validation via JWKS endpoint
2. ✅ Organization ID & name extraction
3. ✅ User ID (from sub) & details extraction
4. ✅ Role-based guards (`usePermission`, `require_role`, dll)
5. ✅ Format data sesuai dengan struktur token Keycloak Anda

## 📚 Documentation

- **[KEYCLOAK_AUTH.md](./KEYCLOAK_AUTH.md)** - Dokumentasi lengkap
- **[KEYCLOAK_AUTH_QUICKREF.md](./KEYCLOAK_AUTH_QUICKREF.md)** - Quick reference
- **[KEYCLOAK_TROUBLESHOOTING.md](./KEYCLOAK_TROUBLESHOOTING.md)** - Troubleshooting
- **[KEYCLOAK_TOKEN_FORMAT_UPDATE.md](./KEYCLOAK_TOKEN_FORMAT_UPDATE.md)** - Token format details

## 🚀 Next Steps

1. ✅ Dependencies installed
2. ✅ Configuration completed
3. ✅ Token validation working
4. ✅ Data extraction working
5. 🎯 **Ready to use!**

Mulai gunakan authentication di endpoints Anda! 🎉
