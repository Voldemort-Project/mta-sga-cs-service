# Test Auto-Sync Setelah Fix Migration

## ✅ Issue Resolved

**Problem:** Column `users.email` tidak ada di database
**Cause:** Migration `f8e96862b7ab_add_email_to_users` belum dijalankan
**Solution:** Run migration dengan `bash scripts/migrate.sh`

## 🧪 Testing Sekarang

### 1. Test Auto-Sync Endpoint

```bash
TOKEN="your-token-here"

curl -X GET "http://localhost:8000/api/v1/example/me-with-sync" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq .
```

### 2. Expected Logs

Check terminal server, seharusnya muncul:

```
[AuthSync] Starting sync for user: 6b6915dd-1f56-446b-ba46-3abfb532f9cd, org: d59a4464-be0e-4516-8f8c-ca7d8fd907b1
[AuthSync] Syncing organization: DevHotel (d59a4464-be0e-4516-8f8c-ca7d8fd907b1)
[AuthSync] Creating new organization: DevHotel (d59a4464-be0e-4516-8f8c-ca7d8fd907b1)
[AuthSync] Organization created successfully
[AuthSync] Organization synced successfully: DevHotel
[AuthSync] Syncing user: admin Dev hotel (6b6915dd-1f56-446b-ba46-3abfb532f9cd)
[AuthSync] User not found, creating new user...
[AuthSync] Getting or creating default role...
[AuthSync] Default role not found, creating...
[AuthSync] Default role created: Keycloak User (xxx-xxx-xxx)
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

### 3. Expected Response

```json
{
  "message": "User data synced to database",
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

### 4. Verify Database

```bash
# Connect to database
psql $DATABASE_URL

# Check organization created
SELECT id, name, created_at FROM organizations
WHERE id = 'd59a4464-be0e-4516-8f8c-ca7d8fd907b1';

# Check user created
SELECT id, name, email, org_id FROM users
WHERE id = '6b6915dd-1f56-446b-ba46-3abfb532f9cd';

# Check role created
SELECT id, name FROM roles WHERE name = 'Keycloak User';

# Check complete relationship
SELECT
  u.id as user_id,
  u.name as user_name,
  u.email as user_email,
  o.name as org_name,
  r.name as role_name,
  u.created_at
FROM users u
LEFT JOIN organizations o ON u.org_id = o.id
LEFT JOIN roles r ON u.role_id = r.id
WHERE u.id = '6b6915dd-1f56-446b-ba46-3abfb532f9cd';
```

Expected result:
```
 user_id                              | user_name         | user_email                   | org_name | role_name     | created_at
--------------------------------------+-------------------+------------------------------+----------+---------------+-------------------------
 6b6915dd-1f56-446b-ba46-3abfb532f9cd | admin Dev hotel   | admin@dev-hotels123.com      | DevHotel | Keycloak User | 2025-11-22 01:15:00
```

## 🎉 Success Criteria

- ✅ No errors in terminal
- ✅ `[AuthSync]` logs show successful sync
- ✅ API returns 200 with user data
- ✅ Organization exists in database
- ✅ User exists in database with email
- ✅ User linked to organization
- ✅ User has default role "Keycloak User"

## 🔄 Test Update Scenario

Call endpoint lagi dengan token yang sama:

```bash
curl -X GET "http://localhost:8000/api/v1/example/me-with-sync" \
  -H "Authorization: Bearer $TOKEN"
```

Expected logs:
```
[AuthSync] Organization exists, checking for updates...
[AuthSync] Organization up to date
[AuthSync] User exists, checking for updates...
[AuthSync] User up to date
```

Should be much faster karena hanya check, tidak insert.

## 📋 Migration History

```
Migration Timeline:
1. 3ea0be2086ab - initial_schema (tables created without email)
2. f8e96862b7ab - add_email_to_users (email column added) ← Just ran this!
```

## 💡 Lesson Learned

Always run `bash scripts/migrate-status.sh` before testing features that depend on database schema!

## 🚀 Ready to Test!

Sekarang auto-sync seharusnya bekerja dengan baik. User dan organization akan otomatis ter-insert ke database saat authenticate.
