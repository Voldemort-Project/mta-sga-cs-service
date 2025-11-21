# Keycloak Auto-Sync to Database

## 📋 Overview

Sistem authentication sekarang mendukung automatic synchronization dari data token Keycloak ke database. Setiap kali user authenticate, organization dan user data akan otomatis di-sync ke database.

## 🎯 Fitur

### 1. **Organization Auto-Sync**
- Jika organization sudah ada (by ID): Update name jika berubah
- Jika organization belum ada: Create new organization dengan ID dari Keycloak

### 2. **User Auto-Sync**
- Jika user sudah ada (by ID): Update name, email, organization jika berubah
- Jika user belum ada: Create new user dengan ID dari Keycloak
- Automatically assign default role ("Keycloak User")

## 🔧 How It Works

### Data Flow

```
1. User sends request with Bearer token
         ↓
2. Token validated & data extracted
         ↓
3. [AUTO-SYNC] Organization synced to DB
         ↓
4. [AUTO-SYNC] User synced to DB
         ↓
5. Request handled by your endpoint
```

### Database Mapping

#### Organization
```python
# From Keycloak Token
{
  "organization": {
    "DevHotel": {
      "id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1"
    }
  }
}

# To Database (organizations table)
{
  "id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1",  # UUID from Keycloak
  "name": "DevHotel",
  "address": null,
  "created_at": "2024-01-20T10:00:00",
  "updated_at": "2024-01-20T10:00:00"
}
```

#### User
```python
# From Keycloak Token
{
  "sub": "6b6915dd-1f56-446b-ba46-3abfb532f9cd",
  "name": "admin Dev hotel",
  "email": "admin@dev-hotels123.com",
  "preferred_username": "admin@dev-hotels123.com"
}

# To Database (users table)
{
  "id": "6b6915dd-1f56-446b-ba46-3abfb532f9cd",  # UUID from sub
  "org_id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1",
  "role_id": "<default-role-id>",  # Auto-assigned "Keycloak User" role
  "name": "admin Dev hotel",
  "email": "admin@dev-hotels123.com",
  "phone": null,
  "id_card_number": null,
  "division_id": null,
  "created_at": "2024-01-20T10:00:00",
  "updated_at": "2024-01-20T10:00:00"
}
```

## 🚀 Usage

### Option 1: Auto-Sync (Recommended)

Gunakan dependencies dengan suffix `_with_sync` untuk automatic database sync:

```python
from fastapi import APIRouter, Depends
from app.core.security import (
    get_current_user_with_sync,
    usePermissionWithSync,
    require_role_with_sync
)
from app.schemas.auth import TokenData

router = APIRouter()

# Basic authentication with auto-sync
@router.get("/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user_with_sync)):
    """
    User authenticated & automatically synced to database
    """
    return {
        "user_id": current_user.user.user_id,
        "organization_id": current_user.organization_id,
        "name": current_user.user.name
    }

# Role-based with auto-sync
@router.get("/admin")
async def admin_only(current_user: TokenData = Depends(usePermissionWithSync("admin_hotel"))):
    """
    Requires 'admin_hotel' role + automatic sync to database
    """
    return {"message": "Admin access granted"}

# Alternative syntax
@router.get("/manager")
async def manager_only(current_user: TokenData = Depends(require_role_with_sync("Manager"))):
    """
    Requires 'Manager' role + automatic sync to database
    """
    return {"message": "Manager access granted"}
```

### Option 2: Manual Sync

Jika ingin kontrol manual kapan sync terjadi:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.core.database import get_db
from app.services.auth_sync_service import sync_auth_data
from app.schemas.auth import TokenData

router = APIRouter()

@router.post("/create-booking")
async def create_booking(
    booking_data: dict,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manual control over when to sync data
    """
    # Manually sync when needed
    organization, user = await sync_auth_data(db, current_user)

    # Use synced data
    booking = {
        "user_id": str(user.id),
        "organization_id": str(organization.id),
        **booking_data
    }

    return {"booking": booking}
```

### Option 3: No Sync

Untuk endpoints yang tidak memerlukan database access:

```python
from app.core.security import get_current_user, usePermission

# Token validation only, no DB sync
@router.get("/quick-check")
async def quick_check(current_user: TokenData = Depends(get_current_user)):
    """
    Fast authentication without database overhead
    """
    return {"authenticated": True}

# Role check without DB sync
@router.get("/admin-quick")
async def admin_quick(current_user: TokenData = Depends(usePermission("admin_hotel"))):
    """
    Role validation without database sync
    """
    return {"admin": True}
```

## 📊 Dependencies Comparison

| Dependency | Token Validation | Role Check | DB Sync | Use Case |
|------------|------------------|------------|---------|----------|
| `get_current_user` | ✅ | ❌ | ❌ | Fast read-only operations |
| `get_current_user_with_sync` | ✅ | ❌ | ✅ | Need user data in DB |
| `usePermission("role")` | ✅ | ✅ | ❌ | Role check without DB |
| `usePermissionWithSync("role")` | ✅ | ✅ | ✅ | Role check + ensure user in DB |
| `require_role("role")` | ✅ | ✅ | ❌ | Alternative syntax, no DB |
| `require_role_with_sync("role")` | ✅ | ✅ | ✅ | Alternative syntax + DB sync |

## 🔄 Sync Logic

### Organization Sync

```python
# Check if exists by ID
existing_org = await db.get(Organization, org_uuid)

if existing_org:
    # Update if name changed
    if existing_org.name != new_name:
        existing_org.name = new_name
        await db.commit()
else:
    # Create new organization
    new_org = Organization(
        id=org_uuid,  # Use Keycloak UUID
        name=org_name,
        address=None
    )
    db.add(new_org)
    await db.commit()
```

### User Sync

```python
# Check if exists by ID
existing_user = await db.get(User, user_uuid)

if existing_user:
    # Update if data changed
    if existing_user.name != new_name:
        existing_user.name = new_name
    if existing_user.email != new_email:
        existing_user.email = new_email
    await db.commit()
else:
    # Get or create default role
    default_role = await get_or_create_default_role(db)

    # Create new user
    new_user = User(
        id=user_uuid,  # Use Keycloak UUID (from sub)
        org_id=org_uuid,
        role_id=default_role.id,
        name=user_name,
        email=user_email,
        phone=None,
        id_card_number=None,
        division_id=None
    )
    db.add(new_user)
    await db.commit()
```

## ⚙️ Default Role

Sistem automatically membuat dan assign default role untuk Keycloak users:

```python
Role:
  name: "Keycloak User"
  description: "Default role for users authenticated via Keycloak"
```

Role ini di-create otomatis saat pertama kali ada user baru dari Keycloak.

## 🎯 Best Practices

### 1. Gunakan Auto-Sync untuk Endpoints yang Butuh DB

```python
# ✅ Good: Need to save data to DB
@router.post("/create-request")
async def create_request(
    request_data: dict,
    current_user: TokenData = Depends(get_current_user_with_sync)
):
    # User guaranteed to exist in DB
    # Can use current_user.user.user_id as foreign key
    pass
```

### 2. Skip Sync untuk Read-Only Operations

```python
# ✅ Good: Just checking authentication
@router.get("/status")
async def get_status(current_user: TokenData = Depends(get_current_user)):
    # Faster, no DB overhead
    return {"authenticated": True}
```

### 3. Use Role Guards dengan Sync untuk Admin Operations

```python
# ✅ Good: Admin operations usually need DB access
@router.post("/admin/settings")
async def update_settings(
    settings: dict,
    current_user: TokenData = Depends(usePermissionWithSync("admin_hotel"))
):
    # Admin user ensured to exist in DB
    pass
```

## 🚨 Error Handling

Auto-sync dirancang fault-tolerant:

```python
try:
    # Attempt to sync to database
    await sync_auth_data(db, current_user)
except Exception as e:
    # Log error but don't fail authentication
    logger.warning(f"Failed to sync auth data: {e}")
    # Request continues even if sync fails
```

**Behavior:**
- ✅ Authentication tetap berhasil meski DB sync gagal
- ⚠️ Warning di-log untuk monitoring
- 🔄 Sync akan retry di request berikutnya

## 🧪 Testing Auto-Sync

### 1. Test Basic Sync

```bash
TOKEN="your-token-here"

# Call endpoint with auto-sync
curl -X GET "http://localhost:8000/api/v1/example/me-with-sync" \
  -H "Authorization: Bearer $TOKEN"

# Check database
psql -d cs_service -c "SELECT id, name FROM organizations;"
psql -d cs_service -c "SELECT id, name, email FROM users;"
```

### 2. Test Update Sync

```bash
# Change user name in Keycloak, get new token, call again
# Should update user name in database

curl -X GET "http://localhost:8000/api/v1/example/me-with-sync" \
  -H "Authorization: Bearer $NEW_TOKEN"

# Verify update
psql -d cs_service -c "SELECT id, name, updated_at FROM users WHERE id='<user-uuid>';"
```

### 3. Test Role Guard with Sync

```bash
# User with admin_hotel role
curl -X GET "http://localhost:8000/api/v1/example/admin-with-sync" \
  -H "Authorization: Bearer $TOKEN"

# Should sync user to DB AND check role
```

## 📝 Database Schema Requirements

Pastikan migrations sudah dijalankan untuk tables berikut:

### Organizations Table
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    address VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    role_id UUID REFERENCES roles(id) NOT NULL,
    name VARCHAR NOT NULL,
    email VARCHAR,
    phone VARCHAR,
    id_card_number VARCHAR,
    division_id UUID REFERENCES divisions(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Roles Table
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔍 Monitoring

Log messages untuk monitoring sync status:

```python
# Success
"Organization synced: id=<uuid>, name=<name>"
"User synced: id=<uuid>, name=<name>"

# Creation
"Organization created: id=<uuid>, name=<name>"
"User created: id=<uuid>, name=<name>"

# Update
"Organization updated: id=<uuid>, old_name=<old>, new_name=<new>"
"User updated: id=<uuid>, fields=[name, email]"

# Error
"Warning: Failed to sync auth data to database: <error>"
```

## 💡 Tips

1. **Performance**: Auto-sync adds ~10-20ms overhead per request
2. **Consistency**: UUIDs dari Keycloak digunakan sebagai primary keys
3. **Idempotent**: Safe to call multiple times, akan update jika ada perubahan
4. **Fault Tolerant**: Authentication tidak gagal meski DB sync error
5. **First Login**: Default role "Keycloak User" otomatis dibuat dan di-assign

## 📚 Related Documentation

- **[KEYCLOAK_AUTH.md](./KEYCLOAK_AUTH.md)** - Authentication basics
- **[KEYCLOAK_COMPLETE_SUMMARY.md](./KEYCLOAK_COMPLETE_SUMMARY.md)** - Complete overview
- **[KEYCLOAK_TOKEN_FORMAT_UPDATE.md](./KEYCLOAK_TOKEN_FORMAT_UPDATE.md)** - Token format details

---

✅ **Auto-sync ready to use!** Pilih dependencies yang sesuai dengan kebutuhan endpoint Anda.
