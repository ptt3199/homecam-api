#!/bin/bash

# Setup Nginx + Let's Encrypt SSL for HomeCam API
# Usage: ./setup-nginx-ssl.sh your-domain.com your-email@example.com

set -e

DOMAIN="${1:-homecam.yourdomain.com}"
EMAIL="${2:-your-email@example.com}"
API_PORT="${3:-8020}"

echo "Setting up HTTPS for domain: $DOMAIN"
echo "Email for Let's Encrypt: $EMAIL"
echo "API running on port: $API_PORT"

# Update system
sudo apt update

# Install Nginx
sudo apt install -y nginx

# Install Certbot for Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/homecam-api > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect all HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL certificates (will be configured by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # CORS headers for video streaming
    add_header Access-Control-Allow-Origin "*";
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    
    # Handle preflight requests
    if (\$request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        add_header Access-Control-Max-Age 1728000;
        add_header Content-Type "text/plain; charset=utf-8";
        add_header Content-Length 0;
        return 204;
    }
    
    # Proxy to FastAPI application
    location / {
        proxy_pass http://127.0.0.1:$API_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings for video streaming
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Special handling for video feed
    location /video_feed {
        proxy_pass http://127.0.0.1:$API_PORT/video_feed;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # No buffering for video stream
        proxy_buffering off;
        proxy_cache off;
        
        # Extended timeouts for streaming
        proxy_connect_timeout 10s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/homecam-api /etc/nginx/sites-enabled/

# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

echo "Nginx configured. Now obtaining SSL certificate..."

# Obtain SSL certificate
sudo certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

# Test SSL renewal
sudo certbot renew --dry-run

echo "✅ HTTPS setup complete!"
echo "Your API is now available at: https://$DOMAIN"
echo ""
echo "Next steps:"
echo "1. Update your Vercel environment variable:"
echo "   NEXT_PUBLIC_API_URL=https://$DOMAIN"
echo "2. Make sure your domain DNS points to this server"
echo "3. Ensure port 80 and 443 are open in your firewall"
echo ""
echo "Test your API:"
echo "curl https://$DOMAIN/camera/status" 