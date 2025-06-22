# PTT Home - Admin Setup

## Admin Authentication

The PTT Home API uses a configurable admin-only authentication system for backend access.

### Admin Credentials Configuration

Admin credentials are configurable via environment variables or settings:

**Default Credentials:**
- **Username:** `admin`
- **Email:** `admin@ptt-home.local`
- **Password:** `123`

**⚠️ SECURITY NOTICE: Change default password before deployment!**

### Configuration Methods

#### Method 1: Environment Variables (.env file)
Create a `.env` file in the homecam-api directory:
```bash
# Admin Credentials
ADMIN_USERNAME=your_admin_username
ADMIN_EMAIL=your_admin@example.com
ADMIN_PASSWORD=your_secure_password
```

#### Method 2: Direct Settings
Update `app/settings.py`:
```python
admin_username: str = "your_admin_username"
admin_email: str = "your_admin@example.com"
admin_password: str = "your_secure_password"
```

### Usage

#### FastAPI Docs Authentication
1. Visit http://localhost:8000/docs
2. Click the 🔒 "Authorize" button
3. Enter your configured admin credentials:
   - Username: (your configured username)
   - Password: (your configured password)
4. Click "Authorize"
5. Test protected endpoints

#### API Login
```bash
# Login to get token (using default credentials)
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=123"

# Use token for API calls
curl -H "Authorization: Bearer admin-jwt-token-ptt-home" \
  http://localhost:8000/camera/status
```

### Security Features

- **Configurable Credentials:** Set via environment variables
- **Single Admin Account:** Only one admin account is allowed
- **No Fallback:** Invalid credentials are immediately rejected
- **Logged Access:** All login attempts are logged

### For Regular Users

Regular users should use the frontend application with Clerk authentication. Backend API login is restricted to admin only.

### Production Deployment

**⚠️ IMPORTANT Steps for Production:**

1. **Change Default Password:**
   ```bash
   # Set strong password in .env
   ADMIN_PASSWORD=your_very_secure_password_here_2024
   ```

2. **Use Environment Variables:**
   ```bash
   # Copy example file
   cp env.example .env
   
   # Edit with your secure values
   nano .env
   ```

3. **Secure the .env file:**
   ```bash
   # Restrict access
   chmod 600 .env
   
   # Add to .gitignore (already included)
   echo ".env" >> .gitignore
   ```

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_USERNAME` | `admin` | Admin username for login |
| `ADMIN_EMAIL` | `admin@ptt-home.local` | Admin email for login |
| `ADMIN_PASSWORD` | `123` | Admin password (CHANGE THIS!) |

### Troubleshooting

- **401 Unauthorized:** Check username/password in your configuration
- **503 Service Unavailable:** Clerk service issues (production only)
- **501 Not Implemented:** Non-admin users trying to login

For support, contact the system administrator. 