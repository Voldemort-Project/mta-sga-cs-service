# Keycloak Authentication - Troubleshooting

## 🔧 Perubahan Terbaru

### ✅ Fixed: 405 Method Not Allowed Error

**Problem:** Error 405 saat mengakses Keycloak untuk validasi token.

**Solution:** Menggunakan JWKS (JSON Web Key Set) endpoint yang lebih reliable:

```python
# Old approach (kadang bermasalah):
GET /realms/{realm}  # Realm info endpoint

# New approach (lebih reliable):
GET /realms/{realm}/protocol/openid-connect/certs  # JWKS endpoint
```

**Perubahan:**
1. Primary: Menggunakan JWKS endpoint
2. Fallback: Jika JWKS gagal, fallback ke realm info endpoint
3. Audience verification di-disable (banyak Keycloak setup tidak include `aud` claim)

## 🐛 Common Issues & Solutions

### 1. 405 Method Not Allowed

**Error Message:**
```json
{
  "detail": "Could not connect to Keycloak: Client error '405 Method Not Allowed' for url '...'"
}
```

**Possible Causes:**
- ✅ **FIXED**: Menggunakan JWKS endpoint sekarang
- Keycloak server misconfiguration
- URL path tidak sesuai dengan Keycloak version

**Check Your Configuration:**

```env
# Keycloak Older Versions (< 18) - with /auth prefix
KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech/auth

# Keycloak Newer Versions (>= 18) - without /auth prefix
KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech
```

**URLs Generated:**

Dengan config: `KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech/auth`
- JWKS: `https://auth.v2.dev.mta.tech/auth/realms/{realm}/protocol/openid-connect/certs`
- Realm Info: `https://auth.v2.dev.mta.tech/auth/realms/{realm}`

Dengan config: `KEYCLOAK_SERVER_URL=https://auth.v2.dev.mta.tech`
- JWKS: `https://auth.v2.dev.mta.tech/realms/{realm}/protocol/openid-connect/certs`
- Realm Info: `https://auth.v2.dev.mta.tech/realms/{realm}`

### 2. 401 Unauthorized - Token Invalid

**Error Message:**
```json
{
  "detail": "Could not validate credentials: Signature verification failed"
}
```

**Solutions:**

1. **Check Token Freshness:**
```bash
# Token might be expired, get a fresh one
TOKEN=$(curl -s -X POST \
  "${KEYCLOAK_SERVER_URL}/realms/${REALM}/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "grant_type=password" \
  -d "username=${USERNAME}" \
  -d "password=${PASSWORD}" | jq -r '.access_token')
```

2. **Verify JWT Algorithm:**
```env
# Make sure algorithm matches Keycloak configuration
JWT_ALGORITHM=RS256  # Most common
# or
JWT_ALGORITHM=HS256  # If using symmetric signing
```

3. **Decode Token to Inspect:**
```bash
# Use jwt.io or decode manually
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .
```

### 3. 401 Unauthorized - Audience Mismatch

**Error Message:**
```json
{
  "detail": "Could not validate credentials: Invalid audience"
}
```

**Solutions:**

1. **Check Token `aud` Claim:**
```bash
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .aud
```

2. **Update Configuration:**
```env
# Set JWT_AUDIENCE to match token's aud claim
JWT_AUDIENCE=account
# or
JWT_AUDIENCE=sga-cs-service
# or leave empty to use CLIENT_ID
```

3. **Note:** Current implementation disables audience verification by default for compatibility.

### 4. 403 Forbidden - Missing Role

**Error Message:**
```json
{
  "detail": "Role 'Admin' required for this operation"
}
```

**Solutions:**

1. **Check User Roles in Token:**
```bash
# Decode token and check roles
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq '.realm_access.roles'
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq '.resource_access'
```

2. **Verify Role Assignment in Keycloak:**
   - Go to Keycloak Admin Console
   - Users → Select User → Role Mappings
   - Assign required roles (realm or client roles)

3. **Check Role Name Exact Match:**
```python
# Role names are case-sensitive!
require_role("Admin")  # Not "admin" or "ADMIN"
```

### 5. 503 Service Unavailable - Cannot Connect

**Error Message:**
```json
{
  "detail": "Could not connect to Keycloak: ..."
}
```

**Solutions:**

1. **Check Keycloak is Running:**
```bash
curl -v ${KEYCLOAK_SERVER_URL}/realms/${REALM}
```

2. **Check SSL/TLS Configuration:**
```env
# For development/testing with self-signed certs
KEYCLOAK_VERIFY_SSL=false

# For production
KEYCLOAK_VERIFY_SSL=true
```

3. **Check Network/Firewall:**
```bash
# Test connectivity
telnet auth.v2.dev.mta.tech 443
# or
nc -zv auth.v2.dev.mta.tech 443
```

4. **Check DNS Resolution:**
```bash
nslookup auth.v2.dev.mta.tech
```

## 🧪 Debugging Tips

### Enable Debug Logging

Add to your code to see detailed errors:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### Test JWKS Endpoint Manually

```bash
# Should return JSON with keys array
curl -v "${KEYCLOAK_SERVER_URL}/realms/${REALM}/protocol/openid-connect/certs"
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

### Test Realm Info Endpoint

```bash
# Should return realm configuration
curl -v "${KEYCLOAK_SERVER_URL}/realms/${REALM}"
```

Expected response includes:
```json
{
  "realm": "claim-mind",
  "public_key": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...",
  "token-service": "...",
  ...
}
```

### Inspect Token Claims

```bash
# Install jwt-cli for easy inspection
# brew install mike-engel/jwt-cli/jwt-cli

jwt decode $TOKEN
```

Or use Python:
```python
import jwt
import json

token = "your-token-here"
# Decode without verification (for inspection only)
decoded = jwt.decode(token, options={"verify_signature": False})
print(json.dumps(decoded, indent=2))
```

### Test Authentication Flow End-to-End

```bash
#!/bin/bash

# Set variables
KEYCLOAK_SERVER_URL="https://auth.v2.dev.mta.tech/auth"
REALM="claim-mind"
CLIENT_ID="sga-cs-service"
CLIENT_SECRET="your-secret"
USERNAME="testuser"
PASSWORD="testpass"
API_URL="http://localhost:8000"

# 1. Get token
echo "=== Getting token from Keycloak ==="
TOKEN=$(curl -s -X POST \
  "${KEYCLOAK_SERVER_URL}/realms/${REALM}/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "grant_type=password" \
  -d "username=${USERNAME}" \
  -d "password=${PASSWORD}" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token"
  exit 1
fi

echo "✅ Token obtained"
echo "Token preview: ${TOKEN:0:50}..."

# 2. Decode token (inspection)
echo ""
echo "=== Token Claims ==="
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .

# 3. Test protected endpoint
echo ""
echo "=== Testing protected endpoint ==="
curl -X GET "${API_URL}/api/v1/example/protected" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq .

# 4. Test admin endpoint
echo ""
echo "=== Testing admin endpoint ==="
curl -X GET "${API_URL}/api/v1/example/admin" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq .
```

## 📝 Configuration Checklist

- [ ] `KEYCLOAK_SERVER_URL` includes or excludes `/auth` based on Keycloak version
- [ ] `KEYCLOAK_REALM` matches exactly (case-sensitive)
- [ ] `KEYCLOAK_CLIENT_ID` matches client configuration in Keycloak
- [ ] `KEYCLOAK_CLIENT_SECRET` is correct (for confidential clients)
- [ ] `KEYCLOAK_VERIFY_SSL` is `false` for dev with self-signed certs
- [ ] `JWT_ALGORITHM` matches Keycloak signature algorithm (usually RS256)
- [ ] User has required roles assigned in Keycloak
- [ ] Client has roles defined in Keycloak (if using client roles)
- [ ] Token service URLs are accessible from your application server

## 🔍 Quick Health Check

```python
# Add this endpoint for debugging
@router.get("/auth/health")
async def auth_health():
    """Check Keycloak connectivity"""
    import httpx
    from app.core.config import settings

    try:
        async with httpx.AsyncClient(verify=settings.keycloak_verify_ssl) as client:
            # Test JWKS endpoint
            jwks_url = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
            response = await client.get(jwks_url)
            response.raise_for_status()

            return {
                "status": "healthy",
                "keycloak_server": settings.keycloak_server_url,
                "realm": settings.keycloak_realm,
                "jwks_url": jwks_url,
                "jwks_keys_count": len(response.json().get("keys", []))
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "keycloak_server": settings.keycloak_server_url,
            "realm": settings.keycloak_realm,
        }
```

## 📚 Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [JWT.io Debugger](https://jwt.io/)
- [RFC 7517 - JSON Web Key (JWK)](https://tools.ietf.org/html/rfc7517)
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)

## 💡 Pro Tips

1. **Cache Public Keys**: Public keys are cached after first fetch to reduce Keycloak requests
2. **Token Expiration**: Tokens typically expire in 5-30 minutes, handle refresh tokens properly
3. **Role Naming**: Use consistent naming convention (PascalCase recommended)
4. **Development**: Use `KEYCLOAK_VERIFY_SSL=false` for local testing with self-signed certs
5. **Production**: Always use `KEYCLOAK_VERIFY_SSL=true` in production
6. **Monitoring**: Log authentication failures for security monitoring
7. **Rate Limiting**: Implement rate limiting on auth endpoints to prevent brute force

## 🚨 If All Else Fails

1. Check Keycloak server logs
2. Enable debug logging in your application
3. Use network inspection tools (Wireshark, mitmproxy)
4. Verify Keycloak client configuration in Admin Console
5. Test with Postman/Insomnia first to isolate the issue
6. Check firewall/security group rules
7. Verify time synchronization (JWT exp/nbf claims are time-sensitive)
