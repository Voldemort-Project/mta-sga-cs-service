# Debugging Auto-Sync Issues

## 🐛 User Tidak Ter-insert ke Database

### Langkah Debugging

#### 1. Check Logs dengan Detail

Sekarang service sudah ada verbose logging. Cek terminal output saat call endpoint:

```bash
# Call endpoint with sync
curl -X GET "http://localhost:8000/api/v1/example/me-with-sync" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected logs:
```
[AuthSync] Starting sync for user: 6b6915dd-1f56-446b-ba46-3abfb532f9cd, org: d59a4464-be0e-4516-8f8c-ca7d8fd907b1
[AuthSync] Syncing organization: DevHotel (d59a4464-be0e-4516-8f8c-ca7d8fd907b1)
[AuthSync] Organization exists, checking for updates...
[AuthSync] Organization up to date
[AuthSync] Organization synced successfully: DevHotel
[AuthSync] Syncing user: admin Dev hotel (6b6915dd-1f56-446b-ba46-3abfb532f9cd)
[AuthSync] User not found, creating new user...
[AuthSync] Getting or creating default role...
[AuthSync] Default role found: Keycloak User (xxx-xxx-xxx)
[AuthSync] Creating user with data:
  - id: 6b6915dd-1f56-446b-ba46-3abfb532f9cd
  - org_id: d59a4464-be0e-4516-8f8c-ca7d8fd907b1
  - role_id: xxx-xxx-xxx
  - name: admin Dev hotel
  - email: admin@dev-hotels123.com
[AuthSync] User added to session, committing...
[AuthSync] Commit successful, refreshing...
[AuthSync] User created successfully: 6b6915dd-1f56-446b-ba46-3abfb532f9cd
[AuthSync] User synced successfully: admin Dev hotel
```

#### 2. Cek Error Message

Jika ada error, sekarang akan muncul dengan full traceback:

```
ERROR: Failed to sync auth data to database
Error details: <error message>
Traceback: <full traceback>
```

Response akan return HTTP 500 dengan detail error.

#### 3. Common Issues & Solutions

##### Issue 1: Organization ID Empty/Invalid

**Error:**
```
ValueError: badly formed hexadecimal UUID string
```

**Cause:** `organization_id` di token kosong atau format tidak valid.

**Check Token:**
```bash
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .organization
```

Expected:
```json
{
  "DevHotel": {
    "id": "d59a4464-be0e-4516-8f8c-ca7d8fd907b1"
  }
}
```

**Solution:** Pastikan token memiliki organization data dengan format yang benar.

##### Issue 2: Role Table Empty

**Error:**
```
IntegrityError: null value in column "role_id" violates not-null constraint
```

**Cause:** Default role "Keycloak User" gagal dibuat.

**Check:**
```sql
SELECT * FROM roles WHERE name = 'Keycloak User';
```

**Solution:** Create role manually:
```sql
INSERT INTO roles (id, name, description, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'Keycloak User',
  'Default role for users authenticated via Keycloak',
  NOW(),
  NOW()
);
```

##### Issue 3: Foreign Key Constraint

**Error:**
```
ForeignKeyViolationError: insert or update on table "users" violates foreign key constraint
```

**Cause:** Organization belum ada di database.

**Check Organization:**
```sql
SELECT * FROM organizations WHERE id = 'd59a4464-be0e-4516-8f8c-ca7d8fd907b1';
```

**Solution:** Pastikan organization sync berjalan dulu sebelum user sync. Service sudah handle ini secara otomatis.

##### Issue 4: UUID Format Mismatch

**Error:**
```
DataError: invalid input syntax for type uuid
```

**Cause:** ID dari Keycloak bukan format UUID yang valid.

**Debug:**
```python
# Check token data
print(f"Org ID: {token_data.organization_id}")
print(f"User ID: {token_data.user.user_id}")

# Try to parse
import uuid
org_uuid = uuid.UUID(token_data.organization_id)
user_uuid = uuid.UUID(token_data.user.user_id)
```

**Solution:** Pastikan Keycloak mengirim UUID yang valid.

##### Issue 5: Database Connection

**Error:**
```
asyncpg.exceptions.CannotConnectNowError: cannot connect to database
```

**Cause:** Database tidak running atau koneksi gagal.

**Check:**
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Or use Python
python -c "
import asyncio
from app.core.database import async_engine

async def test():
    async with async_engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connected!')

asyncio.run(test())
"
```

**Solution:** Start database atau fix connection string.

#### 4. Manual Testing

Test sync function secara langsung:

```python
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.schemas.auth import TokenData, UserInfo
from app.services.auth_sync_service import sync_auth_data

async def test_sync():
    # Create test token data
    token_data = TokenData(
        organization_id="d59a4464-be0e-4516-8f8c-ca7d8fd907b1",
        organization_name="DevHotel",
        user=UserInfo(
            user_id="6b6915dd-1f56-446b-ba46-3abfb532f9cd",
            name="Test User",
            given_name="Test",
            family_name="User",
            username="test@example.com",
            email="test@example.com"
        ),
        roles=["admin_hotel"],
        permissions=[],
        exp=9999999999
    )

    async with AsyncSessionLocal() as db:
        try:
            org, user = await sync_auth_data(db, token_data)
            print(f"✅ Organization: {org.name} ({org.id})")
            print(f"✅ User: {user.name} ({user.id})")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

# Run test
asyncio.run(test_sync())
```

#### 5. Check Database Directly

Setelah call endpoint, cek database:

```sql
-- Check organizations
SELECT id, name, created_at FROM organizations
WHERE id = 'd59a4464-be0e-4516-8f8c-ca7d8fd907b1';

-- Check users
SELECT id, name, email, org_id, role_id, created_at FROM users
WHERE id = '6b6915dd-1f56-446b-ba46-3abfb532f9cd';

-- Check roles
SELECT id, name FROM roles WHERE name = 'Keycloak User';

-- Check relationships
SELECT
  u.id as user_id,
  u.name as user_name,
  o.name as org_name,
  r.name as role_name
FROM users u
LEFT JOIN organizations o ON u.org_id = o.id
LEFT JOIN roles r ON u.role_id = r.id
WHERE u.id = '6b6915dd-1f56-446b-ba46-3abfb532f9cd';
```

#### 6. Enable SQL Echo for Debugging

Temporarily enable SQL logging:

```python
# In app/core/config.py
db_echo: bool = True  # Change to True
```

This will show all SQL queries in console.

## 🔧 Quick Fixes

### Reset and Recreate Tables

If tables are corrupted:

```bash
# Backup first!
pg_dump cs_service > backup.sql

# Drop and recreate
alembic downgrade base
alembic upgrade head
```

### Manually Insert Test Data

```sql
-- Insert test organization
INSERT INTO organizations (id, name, created_at, updated_at)
VALUES (
  'd59a4464-be0e-4516-8f8c-ca7d8fd907b1',
  'DevHotel',
  NOW(),
  NOW()
) ON CONFLICT (id) DO NOTHING;

-- Insert default role
INSERT INTO roles (id, name, description, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'Keycloak User',
  'Default role for users authenticated via Keycloak',
  NOW(),
  NOW()
) ON CONFLICT (name) DO NOTHING;

-- Get role ID
SELECT id FROM roles WHERE name = 'Keycloak User';

-- Insert test user (replace <role-id> with actual ID from above)
INSERT INTO users (id, org_id, role_id, name, email, created_at, updated_at)
VALUES (
  '6b6915dd-1f56-446b-ba46-3abfb532f9cd',
  'd59a4464-be0e-4516-8f8c-ca7d8fd907b1',
  '<role-id>',
  'admin Dev hotel',
  'admin@dev-hotels123.com',
  NOW(),
  NOW()
) ON CONFLICT (id) DO NOTHING;
```

## 📋 Debugging Checklist

- [ ] Database is running and accessible
- [ ] Migrations are up to date (`alembic upgrade head`)
- [ ] Token has valid `organization` data with `id` field
- [ ] Token has valid `sub` claim (UUID format)
- [ ] `roles` table has at least one role
- [ ] Check terminal for `[AuthSync]` log messages
- [ ] Check for error traceback in terminal
- [ ] Verify UUIDs are valid format
- [ ] Test database connection directly
- [ ] Check foreign key constraints
- [ ] Enable `db_echo=True` to see SQL queries

## 🚨 Emergency: Disable Auto-Sync

If auto-sync is causing issues, temporarily disable it:

```python
# In app/core/security.py, change get_current_user_with_sync:

try:
    await sync_auth_data(db, current_user)
    return current_user
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()

    # Return without sync instead of raising error
    return current_user  # ← Change: don't raise, just return
```

Or use non-sync dependencies:
```python
# Instead of:
Depends(get_current_user_with_sync)

# Use:
Depends(get_current_user)
```

## 💡 Production vs Development

### Development (Current)
- Raises error if sync fails
- Verbose logging to console
- Shows full traceback

### Production (Recommended)
```python
# In app/core/security.py
try:
    await sync_auth_data(db, current_user)
    return current_user
except Exception as e:
    # Log to proper logger instead of print
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to sync auth data: {e}", exc_info=True)

    # Return user without sync (don't fail auth)
    return current_user
```

## 📞 Still Not Working?

1. Share the exact error message and traceback
2. Share relevant logs with `[AuthSync]` prefix
3. Share output of these queries:
   ```sql
   SELECT COUNT(*) FROM organizations;
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM roles;
   ```
4. Share token data (organization and sub fields)
5. Test with manual script above

---

Updated with verbose logging and better error reporting! 🔍
