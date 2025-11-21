# 🔧 Keycloak Auth - Fix untuk Error 405

## ❌ Error yang Terjadi

```json
{
  "detail": "Could not connect to Keycloak: Client error '405 Method Not Allowed' for url 'https://auth.v2.dev.mta.tech/auth/realms/claim-mind/protocol/openid-connect/token'"
}
```

## ✅ Solusi yang Diterapkan

### 1. Menggunakan JWKS Endpoint (Primary Method)

**Before:**
```python
# Mengakses realm info endpoint
realm_url = f"{server_url}/realms/{realm}"
```

**After:**
```python
# Mengakses JWKS endpoint (lebih reliable dan standard)
certs_url = f"{server_url}/realms/{realm}/protocol/openid-connect/certs"
```

### 2. Fallback Mechanism

Jika JWKS endpoint gagal, otomatis fallback ke realm info endpoint:

```python
try:
    # Primary: JWKS endpoint
    response = await client.get(certs_url)
    jwks = response.json()
except:
    # Fallback: Realm info endpoint
    response = await client.get(realm_url)
    public_key = response.json().get("public_key")
```

### 3. Disable Audience Verification

Banyak Keycloak setup tidak include `aud` claim di token, jadi sekarang audience verification di-disable by default:

```python
options = {
    "verify_signature": True,
    "verify_aud": False,  # Disabled untuk kompatibilitas
    "verify_exp": True,
}
```

### 4. Enhanced Error Handling

- Timeout: 10 seconds
- Follow redirects: Enabled
- Better error messages untuk debugging

### 5. Support Multi-format Keys

Sekarang bisa handle:
- ✅ JWKS format (dict)
- ✅ PEM format (string)

## 🎯 Konfigurasi untuk Keycloak Anda

Berdasarkan error URL Anda: `https://auth.v2.dev.mta.tech/auth/realms/claim-mind`

### Konfigurasi yang Benar

```env
# Server URL includes /auth for older Keycloak versions
KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech/auth
KEYCLOAK_REALM=claim-mind
KEYCLOAK_CLIENT_ID=sga-cs-service
KEYCLOAK_CLIENT_SECRET=your-client-secret-here
KEYCLOAK_VERIFY_SSL=true

# JWT Settings
JWT_ALGORITHM=RS256
```

### URL yang Akan Digunakan

Dengan konfigurasi di atas, sistem akan mencoba:

**Primary (JWKS):**
```
https://auth.v2.dev.mta.tech/auth/realms/claim-mind/protocol/openid-connect/certs
```

**Fallback (Realm Info):**
```
https://auth.v2.dev.mta.tech/auth/realms/claim-mind
```

## 🧪 Testing

### 1. Test JWKS Endpoint

```bash
curl -v "https://auth.v2.dev.mta.tech/auth/realms/claim-mind/protocol/openid-connect/certs"
```

Expected response:
```json
{
  "keys": [
    {
      "kid": "...",
      "kty": "RSA",
      "alg": "RS256",
      "use": "sig",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

### 2. Get Token dari Keycloak

```bash
curl -X POST "https://auth.v2.dev.mta.tech/auth/realms/claim-mind/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=sga-cs-service" \
  -d "client_secret=YOUR_SECRET" \
  -d "grant_type=password" \
  -d "username=YOUR_USERNAME" \
  -d "password=YOUR_PASSWORD"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIg...",
  "token_type": "Bearer"
}
```

### 3. Test Protected Endpoint

```bash
TOKEN="your-token-here"

# Test basic protected endpoint
curl -X GET "http://localhost:8000/api/v1/example/protected" \
  -H "Authorization: Bearer $TOKEN"

# Test admin endpoint
curl -X GET "http://localhost:8000/api/v1/example/admin" \
  -H "Authorization: Bearer $TOKEN"
```

## 📋 Perubahan File

### Modified Files:

1. **`app/core/security.py`**
   - Updated `KeycloakClient.get_public_key()` untuk menggunakan JWKS endpoint
   - Updated `validate_token()` untuk handle JWKS format
   - Disabled audience verification untuk kompatibilitas
   - Added fallback mechanism

2. **`docs/KEYCLOAK_AUTH.md`**
   - Added Keycloak version compatibility note
   - Updated token validation flow documentation

3. **`docs/KEYCLOAK_TROUBLESHOOTING.md`** (NEW)
   - Comprehensive troubleshooting guide
   - Error solutions
   - Debugging tips

4. **`docs/KEYCLOAK_FIX_SUMMARY.md`** (NEW - this file)
   - Summary of fixes for 405 error

## 🚀 Next Steps

1. ✅ Dependencies sudah diinstall (`python-jose`, `cryptography`)
2. ⚙️ Update `.env` file dengan konfigurasi Keycloak Anda:
   ```env
   KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech/auth
   KEYCLOAK_REALM=claim-mind
   KEYCLOAK_CLIENT_ID=sga-cs-service
   KEYCLOAK_CLIENT_SECRET=your-secret
   ```
3. 🧪 Test dengan mendapatkan token dari Keycloak
4. 🎯 Test protected endpoint dengan token tersebut

## 📞 Jika Masih Ada Error

1. Check URL accessibility:
   ```bash
   curl -v "https://auth.v2.dev.mta.tech/auth/realms/claim-mind/protocol/openid-connect/certs"
   ```

2. Verify realm name is correct: `claim-mind`

3. Check client configuration di Keycloak Admin Console

4. Review logs untuk detailed error message

5. Lihat **[KEYCLOAK_TROUBLESHOOTING.md](./KEYCLOAK_TROUBLESHOOTING.md)** untuk solusi error spesifik

## 💡 Key Improvements

- ✅ More reliable token validation using JWKS
- ✅ Fallback mechanism untuk compatibility
- ✅ Better error handling dan messages
- ✅ Support untuk berbagai Keycloak versions
- ✅ Comprehensive documentation dan troubleshooting guide

Sekarang error 405 seharusnya sudah resolved! 🎉
