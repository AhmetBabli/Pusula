# 🛡️ Security & Configuration Guide

## Environment Setup

### Development Setup
```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt
pip install -r requirements-dev.txt

# 3. Generate security keys
python -c "import secrets; print(secrets.token_hex(32))"  # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY

# 4. Create .env file (use .env.example as template)
cp .env.example .env
# Edit .env with your keys and API credentials

# 5. Run migrations/init
python -c "from backend.database import init_db; init_db()"
```

### Production Deployment
```bash
# Use PostgreSQL instead of SQLite
DATABASE_URL=postgresql://user:password@localhost:5432/kariyer_ajani
DATABASE_TYPE=postgresql

# Enable environment validation
DEBUG=false

# Use strong security keys (generate new ones)
SECRET_KEY=<generate-new-secret>
ENCRYPTION_KEY=<generate-new-fernet-key>

# Whitelist specific CORS origins (NO WILDCARDS)
ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com
```

## Security Features Implemented

### 🔐 Authentication & Authorization
- JWT token-based authentication
- Token expiration (24 hours default)
- Secure token generation using `secrets` module
- Bearer token validation

### 🚦 Rate Limiting
- Global rate limits: 100 requests/hour, 20 requests/minute
- Per-endpoint customizable limits available
- Protection against brute force attacks

### 🔍 Input Validation
- Pydantic validators on all request bodies
- Email validation
- Field length constraints
- List item validation

### 🛡️ Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Cache-Control: no-store

### 📝 Logging & Monitoring
- Centralized logging system
- Error tracking with file rotation
- Frontend error reporting to backend
- Structured error responses

### 🔄 Exception Handling
- Custom exception types:
  - `ValidationError`: Input validation failures
  - `AuthenticationError`: Auth failures
  - `AIServiceError`: AI service failures
  - `TimeoutError`: Request timeouts
  - `DatabaseError`: DB operation failures
- Graceful fallback mechanisms

## Secrets Management

### Never Commit:
- `.env` files with actual values
- API keys in code
- Database passwords
- Encryption keys

### Always Use:
- `.env.example` template with placeholder values
- Environment variables from deployment system
- Secret managers (e.g., AWS Secrets Manager, HashiCorp Vault)

### Rotation Schedule:
- Encryption keys: Never (recreate DB if needed)
- API keys: Every 6 months or when compromised
- JWT secret: When compromised
- Database passwords: Every 3 months

## Database Security

### SQLite (Development Only)
- In-memory testing mode
- File-based persistence
- ⚠️ NOT suitable for production

### PostgreSQL (Production)
- Connection pooling enabled
- Pre-connection validation
- Encrypted connections (SSL/TLS recommended)
- Backup and recovery procedures

## API Security

### Endpoint Protection
```python
from backend.rate_limiter import limiter

@router.get("/sensitive-endpoint")
@limiter.limit("5/minute")
def sensitive_endpoint():
    pass
```

### Request Size Limits
- Maximum 10 MB per request
- Configurable via `MAX_REQUEST_BODY_SIZE`

### CORS Configuration
- Development: All origins (`*`)
- Production: Specific whitelist only
- No credentials allowed in production CORS

## Testing Security

### Run Tests
```bash
pytest backend/tests/
pytest backend/tests/ --cov=backend  # With coverage
pytest -m "not slow"  # Exclude slow tests
```

### Check for Secrets in Code
```bash
# Using detect-secrets
detect-secrets scan
detect-secrets audit .secrets.baseline

# Using git-secrets hook
git secrets --install
```

## Monitoring & Maintenance

### Regular Maintenance Tasks
```bash
# Cleanup orphan database records
python backend/maintenance.py

# Verify constraints
python -c "from backend.maintenance import verify_constraints; verify_constraints()"

# Check environment readiness
python -c "from backend.env_validation import validate_production_readiness; print(validate_production_readiness())"
```

### Log Analysis
```bash
# View application logs
tail -f logs/application.log

# View error logs only
tail -f logs/errors.log

# Rotate logs manually (if needed)
logrotate -f /etc/logrotate.d/kariyer_ajani
```

## Deployment Checklist

- [ ] All `.env` secrets configured
- [ ] Database type set to PostgreSQL
- [ ] DEBUG=false in production
- [ ] CORS origins whitelist configured
- [ ] SSL/TLS certificates installed
- [ ] Secrets scanning passed
- [ ] All tests passing (`pytest`)
- [ ] Environment validation passed
- [ ] Database migrations applied
- [ ] Backups configured
- [ ] Monitoring/alerting setup
- [ ] Documentation updated

## Troubleshooting

### Common Issues

1. **"ENCRYPTION_KEY required"**
   - Generate key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - Add to `.env`

2. **Rate limit errors (429)**
   - Check global limits in `backend/rate_limiter.py`
   - Adjust per-endpoint limits as needed
   - Check for DDoS attacks

3. **Database connection errors**
   - Verify DATABASE_URL format
   - Check database server is running
   - Verify credentials and permissions

4. **Frontend error logging not working**
   - Check `/api/errors/log` endpoint is accessible
   - Verify CORS allows error logging endpoint
   - Check browser console for fetch errors

## Additional Resources

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Best Practices](https://docs.sqlalchemy.org/en/20/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Cryptography Library Docs](https://cryptography.io/)
