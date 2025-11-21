# Keycloak Authentication Implementation Summary

## 📁 Files Created/Modified

### 1. Core Configuration
- **`app/core/config.py`** - Added Keycloak and JWT settings
- **`app/core/security.py`** - NEW: Security utilities and dependencies

### 2. Schemas
- **`app/schemas/auth.py`** - NEW: Authentication schemas (TokenData, UserInfo)

### 3. Examples
- **`app/api/v1/protected_example.py`** - NEW: Example protected endpoints

### 4. Documentation
- **`docs/KEYCLOAK_AUTH.md`** - Complete documentation
- **`docs/KEYCLOAK_AUTH_QUICKREF.md`** - Quick reference guide

### 5. Dependencies
- **`pyproject.toml`** - Added `python-jose[cryptography]` and `cryptography`

## ✨ Features Implemented

### 1. Token Validation ✅
```python
from app.core.security import validate_token

# Automatically validates:
# - JWT signature using Keycloak public key
# - Token expiration
# - Token audience
```

### 2. Role-Based Guards ✅
```python
from app.core.security import require_role, usePermission

# Single role
@app.get("/admin")
async def admin(user: TokenData = Depends(require_role("Admin"))):
    pass

# Alternative syntax (your example)
@app.get("/admin")
async def admin(user: TokenData = Depends(usePermission("Admin"))):
    pass
```

### 3. Multiple Role Guards ✅
```python
from app.core.security import require_any_role, require_all_roles

# Any role (OR logic)
@app.get("/staff")
async def staff(user: TokenData = Depends(require_any_role("Admin", "Manager"))):
    pass

# All roles (AND logic)
@app.get("/super")
async def super_admin(user: TokenData = Depends(require_all_roles("Admin", "SuperUser"))):
    pass
```

### 4. Permission-Based Guards ✅
```python
from app.core.security import require_permission

@app.get("/sensitive")
async def sensitive(user: TokenData = Depends(require_permission("read:sensitive"))):
    pass
```

### 5. User Data Extraction ✅
```python
from app.core.security import get_current_user
from app.schemas.auth import TokenData

@app.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user)):
    return {
        "organization_name": current_user.organization_name,
        "user": {
            "name": current_user.user.name,
            "given_name": current_user.user.given_name,
            "username": current_user.user.username,
            "email": current_user.user.email
        }
    }
```

## 🎯 How to Use

### Step 1: Install Dependencies

```bash
# Using uv (recommended)
uv pip install -e .

# Using pip
pip install -e .
```

### Step 2: Configure Environment

Create/update `.env` file:

```env
# Keycloak Configuration
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=sga-cs-service
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_VERIFY_SSL=true

# JWT Settings (optional)
JWT_ALGORITHM=RS256
JWT_AUDIENCE=sga-cs-service
```

### Step 3: Use in Your Endpoints

```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_user, usePermission
from app.schemas.auth import TokenData

router = APIRouter()

# Basic authentication
@router.get("/protected")
async def protected(current_user: TokenData = Depends(get_current_user)):
    return {"message": f"Hello {current_user.user.name}"}

# Role-based (matching your example)
@router.get("/admin")
async def admin_only(current_user: TokenData = Depends(usePermission("Admin"))):
    return {"message": "Admin access granted"}
```

### Step 4: Test the Implementation

See example endpoints in `app/api/v1/protected_example.py`

Register the example router in your main router:

```python
# In app/api/router.py or app/main.py
from app.api.v1.protected_example import router as example_router

app.include_router(example_router, prefix="/api/v1")
```

## 🔧 Architecture

### Dependency Injection Flow

```
HTTP Request with Bearer Token
         ↓
    HTTPBearer (FastAPI)
         ↓
    validate_token()
    - Fetch Keycloak public key
    - Decode JWT
    - Verify signature, expiration, audience
         ↓
    get_current_user()
    - Extract user info
    - Extract roles & permissions
    - Return TokenData
         ↓
    require_role() / usePermission()
    - Check if user has required role
    - Return TokenData or raise 403
         ↓
    Your Endpoint Handler
```

### Token Data Structure

```python
class TokenData:
    organization_name: str
    user: UserInfo
        - name: str
        - given_name: str
        - username: str
        - email: str
    roles: list[str]
    permissions: list[str]
    sub: str  # User ID
    exp: int  # Expiration
```

## 🚀 Available Guards

| Guard | Description | Example |
|-------|-------------|---------|
| `get_current_user` | Basic auth, extract user data | `Depends(get_current_user)` |
| `require_role("Admin")` | Single role required | `Depends(require_role("Admin"))` |
| `usePermission("Admin")` | Alias for require_role | `Depends(usePermission("Admin"))` |
| `require_any_role("A", "B")` | Any of the roles (OR) | `Depends(require_any_role("Admin", "Manager"))` |
| `require_all_roles("A", "B")` | All roles (AND) | `Depends(require_all_roles("Admin", "SuperUser"))` |
| `require_permission("read:x")` | Permission-based | `Depends(require_permission("read:users"))` |

## 📝 Token Format Expected

Your Keycloak token should contain:

```json
{
  "sub": "user-uuid",
  "name": "John Doe",
  "given_name": "John",
  "preferred_username": "johndoe",
  "email": "john@example.com",
  "organization_name": "Acme Corp",
  "realm_access": {
    "roles": ["Admin", "User"]
  },
  "resource_access": {
    "sga-cs-service": {
      "roles": ["Manager"]
    }
  },
  "authorization": {
    "permissions": [
      {"rsname": "read:users"},
      {"rsname": "write:users"}
    ]
  },
  "exp": 1234567890,
  "aud": "sga-cs-service"
}
```

## 🔐 Security Features

1. ✅ **JWT Signature Verification** - Using Keycloak public key
2. ✅ **Token Expiration Check** - Automatic expiration validation
3. ✅ **Audience Verification** - Ensures token is for this service
4. ✅ **SSL/TLS Support** - Configurable SSL verification
5. ✅ **Public Key Caching** - Reduces Keycloak requests
6. ✅ **Role & Permission Checks** - Fine-grained access control

## 🧪 Testing

Get a token from Keycloak:

```bash
TOKEN=$(curl -s -X POST \
  "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=sga-cs-service" \
  -d "client_secret=your-secret" \
  -d "grant_type=password" \
  -d "username=admin" \
  -d "password=admin" | jq -r '.access_token')
```

Test protected endpoint:

```bash
curl -X GET "http://localhost:8000/api/v1/example/protected" \
  -H "Authorization: Bearer $TOKEN"
```

Test admin endpoint:

```bash
curl -X GET "http://localhost:8000/api/v1/example/admin" \
  -H "Authorization: Bearer $TOKEN"
```

## 📚 Documentation

- **Complete Guide**: [KEYCLOAK_AUTH.md](./KEYCLOAK_AUTH.md)
- **Quick Reference**: [KEYCLOAK_AUTH_QUICKREF.md](./KEYCLOAK_AUTH_QUICKREF.md)
- **Example Code**: `app/api/v1/protected_example.py`

## 🎨 Customization

### Custom Organization Field

If your Keycloak uses different field names, edit `app/core/security.py`:

```python
# In get_current_user function
organization_name = (
    token_payload.get("your_custom_field") or
    token_payload.get("organization_name") or
    ""
)
```

### Custom Role Extraction

Modify role extraction logic in `get_current_user` function as needed.

## ✅ Requirements Met

- [x] Validasi token dari Keycloak
- [x] Guard dengan input role/permission (usePermission)
- [x] Extract data dalam format yang diminta:
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
- [x] Dependency injection pattern (seperti database)
- [x] Dokumentasi lengkap
- [x] Contoh penggunaan

## 🚀 Next Steps

1. Install dependencies: `uv pip install -e .`
2. Configure `.env` with your Keycloak settings
3. Import and use guards in your endpoints
4. Test with example endpoints
5. Customize as needed for your use case

Semua fungsi sudah siap digunakan! 🎉
