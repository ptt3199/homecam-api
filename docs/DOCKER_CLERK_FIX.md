# Fixing Clerk Authentication in Docker

## Problem
The backend running in Docker cannot authenticate with Clerk because it can't connect to Clerk's JWKS (JSON Web Key Set) endpoint to fetch the public keys needed for JWT verification.

## Root Cause
Docker containers by default have limited network access and may face:
1. DNS resolution issues
2. Blocked outbound HTTPS connections
3. Missing CA certificates for SSL verification
4. Network isolation preventing external API calls

## Solutions Applied

### 1. Docker Network Configuration
Updated `docker-compose.yml` to include proper DNS resolution:
```yaml
dns:
  - 8.8.8.8
  - 8.8.4.4
```

### 2. CA Certificates
Added CA certificates to the Dockerfile for HTTPS support:
```dockerfile
# Network connectivity and HTTPS support
ca-certificates \
curl \
```

### 3. Environment Variables
Added streaming token secret to environment:
```yaml
environment:
  - STREAMING_TOKEN_SECRET=your-production-streaming-secret-change-this
```

### 4. Enhanced Error Handling
Improved error handling in `auth_ops.py` to provide better debugging information for network issues.

### 5. Network Diagnostic Tools
Added diagnostic endpoints and tools:
- `GET /health/network` - Test network connectivity
- `test_clerk_connectivity.py` - Standalone connectivity test script

## Debugging Steps

### Step 1: Test Basic Connectivity
```bash
# Start the container
docker-compose up -d

# Test the health endpoint
curl http://localhost:8020/health

# Test network connectivity
curl http://localhost:8020/health/network
```

### Step 2: Run Connectivity Test Inside Container
```bash
# Enter the container
docker-compose exec homecam-api bash

# Run the test script
python test_clerk_connectivity.py
```

### Step 3: Check DNS Resolution
```bash
# Inside the container
nslookup clerk.com
nslookup api.clerk.com
```

### Step 4: Test Manual HTTPS Request
```bash
# Inside the container
curl -v https://clerk.com
curl -v https://api.clerk.com
```

## Alternative Solutions

### Option A: Host Network Mode
If the above doesn't work, you can use host networking (less secure):
```yaml
services:
  homecam-api:
    network_mode: host
    # Remove ports section when using host mode
```

### Option B: Custom Docker Network
Create a custom bridge network:
```yaml
networks:
  homecam-network:
    driver: bridge
    
services:
  homecam-api:
    networks:
      - homecam-network
```

### Option C: Use Environment-Specific JWKS
For environments with strict network policies, you could:
1. Download JWKS manually
2. Store them in environment variables
3. Use them directly instead of fetching from Clerk

## Production Considerations

1. **Security**: Use strong `STREAMING_TOKEN_SECRET` in production
2. **Networking**: Configure proper firewall rules for outbound HTTPS
3. **Monitoring**: Monitor the `/health/network` endpoint
4. **Logging**: Check container logs for network errors:
   ```bash
   docker-compose logs homecam-api
   ```

## Testing the Fix

1. Deploy with the updated configuration:
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```

2. Test authentication with a valid Clerk JWT token:
   ```bash
   curl -H "Authorization: Bearer <jwt_token>" http://localhost:8020/camera/status
   ```

3. Check the logs for successful JWKS fetching:
   ```bash
   docker-compose logs homecam-api | grep JWKS
   ```

## Expected Behavior After Fix

- Container should successfully fetch JWKS from Clerk
- JWT tokens should verify properly
- Authentication should work end-to-end
- Network diagnostic endpoint should show successful connections

## If Issues Persist

1. Check if your network has a corporate proxy
2. Verify firewall rules allow outbound HTTPS on port 443
3. Consider using host network mode temporarily for testing
4. Check if DNS resolution works for Clerk domains 