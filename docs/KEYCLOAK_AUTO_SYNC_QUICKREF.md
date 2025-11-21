# Keycloak Auto-Sync - Quick Reference

## 🚀 Quick Start

### Option 1: Auto-Sync (Recommended)

Data organization dan user otomatis di-sync ke database:

```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_user_with_sync, usePermissionWithSync
from app.schemas.auth import TokenData

router = APIRouter()

# Basic auth + auto-sync
@router.get("/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user_with_sync)):
    return {"user_id": current_user.user.user_id}

# Role check + auto-sync
@router.get("/admin")
async def admin_only(current_user: TokenData = Depends(usePermissionWithSync("admin_hotel"))):
    return {"message": "Admin access"}
```

### Option 2: No Sync (Faster)

Hanya validasi token, tanpa database:

```python
from app.core.security import get_current_user, usePermission

# Token validation only
@router.get("/quick")
async def quick_check(current_user: TokenData = Depends(get_current_user)):
    return {"authenticated": True}

# Role check, no DB
@router.get("/admin-quick")
async def admin_quick(current_user: TokenData = Depends(usePermission("admin_hotel"))):
    return {"admin": True}
```

## 📊 Dependencies Cheatsheet

| Need | Use This | Example |
|------|----------|---------|
| Auth only | `get_current_user` | Read-only operations |
| Auth + DB sync | `get_current_user_with_sync` | Create/update data |
| Role check | `usePermission("role")` | Fast role validation |
| Role + DB sync | `usePermissionWithSync("role")` | Admin operations |

## 🔄 What Gets Synced?

### Organization
```
Keycloak → Database
id       → organizations.id
name     → organizations.name
```

### User
```
Keycloak → Database
sub      → users.id
name     → users.name
email    → users.email
org_id   → users.org_id
         → users.role_id (auto: "Keycloak User")
```

## 💡 When to Use Which?

**Use `_with_sync`:**
- ✅ Creating/updating records
- ✅ Need user in DB for foreign keys
- ✅ Admin operations
- ✅ Booking/request creation

**Use without sync:**
- ✅ Just checking authentication
- ✅ Read-only operations
- ✅ High-frequency requests
- ✅ No DB needed

## 🧪 Test It

```bash
TOKEN="your-token-here"

# Test auto-sync
curl -X GET "http://localhost:8000/api/v1/example/me-with-sync" \
  -H "Authorization: Bearer $TOKEN"

# Check DB
psql -d cs_service -c "SELECT * FROM users;"
```

## 📚 Full Documentation

See [KEYCLOAK_AUTO_SYNC.md](./KEYCLOAK_AUTO_SYNC.md) for complete guide.
