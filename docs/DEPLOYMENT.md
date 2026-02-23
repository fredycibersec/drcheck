# Deployment Guide - Home Server Setup

This guide explains how to deploy the Domain Reputation Checker webapp on a home server for standalone operation.

## Prerequisites

- Python 3.8 or higher
- Ubuntu/Debian Linux (or similar)
- Root/sudo access
- Network access for API calls to threat intelligence sources

## Deployment Options

### Option 1: Simple Standalone (Development/Testing)

**Best for**: Quick setup, testing, single-user access

```bash
# Navigate to the app directory
cd /home/aramirez/pentest/OSINT/Domain-Reputation-WebApp

# Install dependencies
pip3 install -r requirements.txt

# Run the development server
python3 app.py
```

Access at: `http://your-server-ip:5000`

**Limitations**:
- Not suitable for production
- Single-threaded
- No auto-restart on crash
- Debug mode enabled

---

### Option 2: Production with Gunicorn + Nginx (Recommended)

**Best for**: Production use, multiple users, reliable operation

#### Step 1: Install Gunicorn

```bash
pip3 install gunicorn
```

#### Step 2: Create systemd service

Create `/etc/systemd/system/domain-reputation.service`:

```ini
[Unit]
Description=Domain Reputation Checker Web Application
After=network.target

[Service]
Type=notify
User=aramirez
Group=aramirez
WorkingDirectory=/home/aramirez/pentest/OSINT/Domain-Reputation-WebApp
Environment="PATH=/home/aramirez/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="VIRUSTOTAL_API_KEY=your_vt_key_here"
Environment="ABUSEIPDB_API_KEY=your_abuseipdb_key_here"
Environment="URLSCAN_API_KEY=your_urlscan_key_here"
Environment="ABUSECH_API_KEY=your_abusech_key_here"
ExecStart=/usr/local/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 wsgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note**: Replace API keys with your actual keys, or source them from your shell profile.

#### Step 3: Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable domain-reputation
sudo systemctl start domain-reputation
sudo systemctl status domain-reputation
```

#### Step 4: Install and configure Nginx

```bash
sudo apt update
sudo apt install nginx
```

Create `/etc/nginx/sites-available/domain-reputation`:

```nginx
server {
    listen 80;
    server_name your-server-ip;  # or your.domain.com

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /static {
        alias /home/aramirez/pentest/OSINT/Domain-Reputation-WebApp/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/domain-reputation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Access at: `http://your-server-ip`

---

### Option 3: Docker Container (Isolated & Portable)

**Best for**: Easy deployment, portability, containerized environments

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--timeout", "120", "wsgi:app"]
```

Build and run:

```bash
# Build image
docker build -t domain-reputation-checker .

# Run container
docker run -d \
  --name domain-reputation \
  -p 5000:5000 \
  -e VIRUSTOTAL_API_KEY="your_key" \
  -e ABUSEIPDB_API_KEY="your_key" \
  -e URLSCAN_API_KEY="your_key" \
  -e ABUSECH_API_KEY="your_key" \
  --restart unless-stopped \
  domain-reputation-checker
```

Access at: `http://your-server-ip:5000`

---

## Security Considerations

### 1. Firewall Configuration

```bash
# Allow HTTP (if using Nginx)
sudo ufw allow 80/tcp

# Or allow Flask directly (development only)
sudo ufw allow 5000/tcp

# Enable firewall
sudo ufw enable
```

### 2. API Key Management

**DO NOT** hardcode API keys in files. Use one of these methods:

**Option A**: Environment variables in systemd service (recommended)
**Option B**: Load from shell profile (.zshrc, .bashrc)
**Option C**: Use a `.env` file (never commit to git)

### 3. HTTPS Setup (Optional but Recommended)

If exposing to internet, use Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.com
```

### 4. Access Control

For internal network only:
- Configure firewall to only allow local network access
- Use Nginx basic auth for additional protection

```nginx
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:5000;
}
```

---

## Monitoring & Maintenance

### View Logs

```bash
# Application logs
sudo journalctl -u domain-reputation -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services

```bash
# Restart application
sudo systemctl restart domain-reputation

# Restart Nginx
sudo systemctl restart nginx
```

### Update Application

```bash
cd /home/aramirez/pentest/OSINT/Domain-Reputation-WebApp
git pull  # if using git
sudo systemctl restart domain-reputation
```

---

## Performance Tuning

### Gunicorn Workers

Rule of thumb: `(2 * CPU_cores) + 1`

For a 4-core server: `--workers 9`

### Timeout Settings

API calls can take time. Adjust timeouts:

```bash
# In systemd service
--timeout 120  # 2 minutes

# In Nginx config
proxy_read_timeout 120s;
```

### Caching

The CLI tool has built-in caching (24 hours). Cache file location:
`~/.domain_reputation_cache.db`

---

## Network Access Requirements

The app needs outbound internet access to:
- VirusTotal API (virustotal.com)
- AbuseIPDB API (abuseipdb.com)
- URLScan API (urlscan.io)
- MalwareBazaar API (abuse.ch)
- AlienVault OTX (otx.alienvault.com)
- Other threat intel sources

Ensure your firewall allows outbound HTTPS (port 443).

---

## Troubleshooting

### Service won't start

```bash
sudo journalctl -u domain-reputation -n 50
```

Check for:
- Missing dependencies
- Wrong Python path
- Invalid API keys
- Permission issues

### App is slow

- Check API key quotas/rate limits
- Increase timeout values
- Add more Gunicorn workers
- Check network connectivity

### 502 Bad Gateway (Nginx)

- Ensure gunicorn is running: `sudo systemctl status domain-reputation`
- Check gunicorn port matches Nginx config
- Review logs: `sudo journalctl -u domain-reputation`

---

## Quick Reference

| Setup | Command | Access URL |
|-------|---------|------------|
| Development | `python3 app.py` | http://localhost:5000 |
| Production (Gunicorn) | `systemctl start domain-reputation` | http://server-ip |
| With Nginx | `systemctl start nginx` | http://server-ip:80 |
| Docker | `docker run -p 5000:5000 ...` | http://server-ip:5000 |

---

## Summary

✅ **Yes, the webapp is fully prepared for standalone home server deployment!**

Choose your deployment method based on:
- **Development/Testing**: Option 1 (Simple standalone)
- **Production/Multi-user**: Option 2 (Gunicorn + Nginx) ← **Recommended**
- **Containerized**: Option 3 (Docker)

All API keys are loaded from environment variables, so it works in any deployment scenario.
