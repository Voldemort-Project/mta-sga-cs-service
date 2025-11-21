# Token Data Format Update

## 📝 Perubahan Format Token Data

Berdasarkan struktur token Keycloak yang sebenarnya, format data telah disesuaikan.

## ✅ Format Token Keycloak Anda

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

## 📊 Format Data Yang Di-extract

### Before (Lama)
```json
{
  "organization_name": "",
  "user": {
    "name": "",
    "given_name": "",
    "username": "",
    "email": ""
  }
}
```

### After (Baru) ✅
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
  "roles": ["admin_hotel", "offline_access", ...],
  "permissions": [],
  "exp": 1763753926
}
```

## 🔄 Perubahan Schema

### `UserInfo` Schema

```python
class UserInfo(BaseModel):
    user_id: str          # NEW: User ID dari 'sub' claim
    name: str             # Full name
    given_name: str       # First name
    family_name: str      # NEW: Last name dari 'family_name' claim
    username: str         # Username dari 'preferred_username'
    email: str            # Email address
```

### `TokenData` Schema

```python
class TokenData(BaseModel):
    organization_id: str   # NEW: Organization ID dari organization.{org_name}.id
    organization_name: str # Organization name dari key di organization dict
    user: UserInfo        # User information
    roles: list[str]      # User roles
    permissions: list[str] # User permissions
    exp: int              # Token expiration
```

## 🔍 Extraction Logic

### Organization Data

Token memiliki struktur organization seperti ini:
```json
"organization": {
  "DevHotel": {
    "id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1"
  }
}
```

Extraction logic:
```python
organization_data = token_payload.get("organization", {})
if isinstance(organization_data, dict) and organization_data:
    # Get organization name from first key
    organization_name = list(organization_data.keys())[0]  # "DevHotel"

    # Get organization details
    org_details = organization_data.get(organization_name, {})

    # Extract organization ID
    organization_id = org_details.get("id", "")  # "d59a4464-be0e-4516-8f8c-ca7d8fd907b1"
```

### User Data

```python
user_id = token_payload.get("sub")  # User ID dari sub claim
name = token_payload.get("name")
given_name = token_payload.get("given_name")
family_name = token_payload.get("family_name")
username = token_payload.get("preferred_username")
email = token_payload.get("email")
```

### Roles

Roles diambil dari `realm_access.roles`:
```python
realm_roles = token_payload.get("realm_access", {}).get("roles", [])
# ["offline_access", "default-roles-claim-mind", "admin_hotel", "uma_authorization"]
```

## 📄 File yang Diupdate

1. ✅ `app/schemas/auth.py` - Updated `UserInfo` dan `TokenData` schemas
2. ✅ `app/core/security.py` - Updated `get_current_user()` extraction logic
3. ✅ `app/api/v1/protected_example.py` - Updated example endpoints
4. ✅ `docs/KEYCLOAK_AUTH.md` - Updated documentation
5. ✅ `docs/KEYCLOAK_AUTH_QUICKREF.md` - Updated quick reference

## 🎯 Usage Example

### Get Current User Data

```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.schemas.auth import TokenData

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    """Get user profile from token"""
    return {
        "organization": {
            "id": current_user.organization_id,
            "name": current_user.organization_name
        },
        "user": {
            "id": current_user.user.user_id,
            "name": current_user.user.name,
            "given_name": current_user.user.given_name,
            "family_name": current_user.user.family_name,
            "username": current_user.user.username,
            "email": current_user.user.email
        },
        "roles": current_user.roles
    }
```

### Response Example

```json
{
  "organization": {
    "id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1",
    "name": "DevHotel"
  },
  "user": {
    "id": "6b6915dd-1f56-446b-ba46-3abfb532f9cd",
    "name": "admin Dev hotel",
    "given_name": "admin",
    "family_name": "Dev hotel",
    "username": "admin@dev-hotels123.com",
    "email": "admin@dev-hotels123.com"
  },
  "roles": [
    "admin_hotel",
    "offline_access",
    "default-roles-claim-mind",
    "uma_authorization"
  ]
}
```

## 🧪 Testing

### Test dengan Example Endpoint

```bash
# Get your token first
TOKEN="your-token-here"

# Test /me endpoint
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
  "roles": ["admin_hotel", "offline_access", ...],
  "permissions": []
}
```

## 🔄 Migration Notes

Jika ada kode existing yang menggunakan format lama:

### Before
```python
user_id = current_user.sub  # ❌ Field 'sub' tidak ada lagi
org_name = current_user.organization_name  # ✅ Masih ada
```

### After
```python
user_id = current_user.user.user_id  # ✅ Sekarang di dalam user object
org_id = current_user.organization_id  # ✅ NEW: Organization ID tersedia
org_name = current_user.organization_name  # ✅ Masih ada
```

## 📋 Field Mapping

| Token Field | Schema Field | Notes |
|-------------|--------------|-------|
| `sub` | `user.user_id` | User ID |
| `name` | `user.name` | Full name |
| `given_name` | `user.given_name` | First name |
| `family_name` | `user.family_name` | Last name |
| `preferred_username` | `user.username` | Username |
| `email` | `user.email` | Email address |
| `organization.{key}` | `organization_name` | First key in organization dict |
| `organization.{key}.id` | `organization_id` | Organization ID |
| `realm_access.roles` | `roles` | User roles |
| `exp` | `exp` | Token expiration |

## ✅ Verified

- ✅ Organization ID extracted correctly
- ✅ Organization name extracted correctly
- ✅ User ID (from sub) extracted correctly
- ✅ User details (name, given_name, family_name, username, email) extracted correctly
- ✅ Roles extracted from realm_access.roles
- ✅ Token expiration extracted correctly
- ✅ Backward compatible dengan berbagai format organization

Format sekarang sudah sesuai dengan struktur token Keycloak Anda! 🎉
