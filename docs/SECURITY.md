# Security Features

This document outlines the security measures implemented in the Domain Reputation Checker webapp.

## Input Validation & Sanitization

### Comprehensive Input Validation

The `sanitize_input()` function performs multiple security checks:

#### 1. **Character Whitelist**
- Only allows: `a-z`, `0-9`, `.`, `-`, `_`
- Blocks all special characters that could enable injection attacks
- Prevents shell metacharacters: `;`, `&`, `|`, `` ` ``, `$`, `(`, `)`

#### 2. **Length Limits**
- Minimum: 3 characters
- Maximum: 256 characters
- Prevents buffer overflow and DoS attacks

#### 3. **Format Validation**
Input must match one of:
- **Valid Domain**: `example.com`, `sub.domain.co.uk`
  - Follows RFC 1035 domain naming conventions
  - Max 63 chars per label
- **Valid Hash**: MD5 (32 hex), SHA1 (40 hex), SHA256 (64 hex)
  - Only hexadecimal characters (0-9, a-f)

#### 4. **Malicious Pattern Detection**
Blocks common attack vectors:
```python
- Directory traversal: ".."
- Command injection: Leading "-" (flag injection)
- Shell injection: Shell metacharacters
- XSS attempts: "<script", "javascript:", "on*=" event handlers
```

#### 5. **Case Normalization**
- Converts all input to lowercase
- Prevents case-based bypass attempts

### Example Blocked Inputs

```bash
# Command Injection Attempts
; cat /etc/passwd           ❌ Blocked (semicolon)
`whoami`                    ❌ Blocked (backticks)
$(rm -rf /)                 ❌ Blocked (shell substitution)

# Directory Traversal
../../etc/passwd            ❌ Blocked (dots)
example.com/../etc          ❌ Blocked (dots)

# XSS Attempts
<script>alert(1)</script>   ❌ Blocked (special chars)
javascript:alert(1)         ❌ Blocked (javascript:)
onclick=alert(1)            ❌ Blocked (event handler)

# Invalid Formats
just_random_text            ❌ Blocked (not domain/hash)
exam ple.com                ❌ Blocked (space)
example.com/path            ❌ Blocked (slash)

# Valid Inputs
example.com                 ✅ Allowed (valid domain)
sub.domain.co.uk            ✅ Allowed (valid domain)
44d88612fea8a8f36de82e1... ✅ Allowed (valid MD5)
```

---

## Rate Limiting

### Global Limits
- **200 requests per day** per IP
- **50 requests per hour** per IP

### Endpoint-Specific Limits
- **`/api/check`**: 10 requests per minute
  - Prevents API abuse
  - Protects against DoS attacks
  - Respects upstream API rate limits

### Rate Limit Headers
Responses include:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1234567890
```

### When Limit Exceeded
```json
{
  "error": "429 Too Many Requests: 10 per 1 minute"
}
```

---

## Security Headers

All responses include security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
```

### What They Protect Against

| Header | Protection |
|--------|------------|
| `X-Content-Type-Options` | MIME type sniffing attacks |
| `X-Frame-Options` | Clickjacking (prevents embedding in iframe) |
| `X-XSS-Protection` | Reflected XSS attacks |
| `Strict-Transport-Security` | Forces HTTPS (in production) |
| `Content-Security-Policy` | XSS, injection, unauthorized resources |

---

## CORS Configuration

CORS is configured to allow cross-origin requests, but with restrictions:

```python
CORS(app)  # Allows specified origins only
```

For production, restrict to specific origins:
```python
CORS(app, origins=["https://yourdomain.com"])
```

---

## API Key Protection

### Environment Variables
- API keys are **never** hardcoded in source code
- Loaded from environment variables or shell profile
- Not exposed in API responses or client-side code

### Example Configuration
```bash
export VIRUSTOTAL_API_KEY="your_key_here"
export ABUSEIPDB_API_KEY="your_key_here"
```

---

## Error Handling

### Safe Error Messages
- Generic error messages for users
- Detailed errors logged server-side only
- Never expose:
  - Stack traces to client
  - File paths
  - API keys
  - Internal system info

### Example
```python
# Bad (exposes internals)
return jsonify({'error': f'File not found: /etc/app/config.ini'})

# Good (generic message)
return jsonify({'error': 'Configuration error'})
```

---

## Additional Security Measures

### 1. **No Direct Shell Execution**
- All API calls use Python libraries (requests, etc.)
- No `os.system()` or `subprocess` calls with user input
- Cannot execute arbitrary commands

### 2. **No SQL Injection**
- Uses SQLite with parameterized queries only
- No string concatenation for SQL
- Caching is safe from injection

### 3. **No File Upload**
- Application doesn't accept file uploads
- No risk of malicious file execution
- Only text input (domains/hashes)

### 4. **Logging & Monitoring**
- All requests logged with IP and timestamp
- Failed validation attempts logged
- Rate limit violations logged

### 5. **Resource Limits**
- Request timeout: 120 seconds
- Max workers: Configurable (default: 4)
- Prevents resource exhaustion

---

## Deployment Security Checklist

When deploying to production:

- [ ] Use HTTPS (Let's Encrypt/certbot)
- [ ] Configure firewall (UFW/iptables)
- [ ] Run as non-root user
- [ ] Set proper file permissions (750 for app, 640 for configs)
- [ ] Use strong systemd service isolation
- [ ] Configure Nginx/reverse proxy properly
- [ ] Enable fail2ban for brute force protection
- [ ] Regular security updates (`apt update && apt upgrade`)
- [ ] Monitor logs for suspicious activity
- [ ] Restrict CORS to specific origins
- [ ] Use environment-specific settings (debug=False in prod)
- [ ] Set up log rotation
- [ ] Consider IP whitelisting for internal use

---

## Vulnerability Reporting

If you discover a security vulnerability, please:

1. **DO NOT** create a public GitHub issue
2. Contact the maintainer privately
3. Provide detailed reproduction steps
4. Allow reasonable time for fix before disclosure

---

## Security Updates

Dependencies are regularly updated to patch known vulnerabilities:

```bash
# Check for outdated packages
pip list --outdated

# Update all dependencies
pip install -U -r requirements.txt
```

---

## Compliance

### Data Privacy
- No user data is stored permanently
- Caching is local (24 hours only)
- No tracking or analytics
- No PII collection

### API Usage
- Respects upstream API terms of service
- Implements rate limiting
- Proper attribution to data sources

---

## Testing Security

### Manual Testing
```bash
# Test injection attempts
curl -X POST http://localhost:5000/api/check \
  -H "Content-Type: application/json" \
  -d '{"domain": "test.com; whoami"}'
# Should return: "Invalid characters detected"

# Test rate limiting
for i in {1..15}; do
  curl -X POST http://localhost:5000/api/check \
    -H "Content-Type: application/json" \
    -d '{"domain": "test.com"}'
done
# After 10 requests: "429 Too Many Requests"
```

### Automated Security Scanning
```bash
# Install security scanner
pip install bandit safety

# Scan for vulnerabilities
bandit -r app.py
safety check -r requirements.txt
```

---

## Summary

✅ **Input Sanitization**: Comprehensive validation prevents injection attacks  
✅ **Rate Limiting**: Prevents abuse and DoS attacks  
✅ **Security Headers**: Protects against common web vulnerabilities  
✅ **API Key Protection**: Secrets never exposed  
✅ **Error Handling**: Safe error messages  
✅ **No Shell Execution**: Cannot run arbitrary commands  
✅ **HTTPS Ready**: Supports SSL/TLS in production  
✅ **Regular Updates**: Dependencies kept current  

The application follows security best practices and is hardened against common attack vectors.
