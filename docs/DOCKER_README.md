# Docker Deployment Guide

**Version:** 2.1.0 | **Updated:** January 28, 2026

## 🎉 What's New in v2.1.0

### Recent Improvements
- ✅ **URLVoid API** - 95% accuracy (requires APIVOID_KEY)
- ✅ **WHOIS Age Risk** - HIGH/MEDIUM/LOW risk indicators
- ✅ **VT Engines** - Lists security vendors that flagged threats
- ✅ **Attack Cards** - Beautiful formatting for AbuseIPDB attacks
- ✅ **Badge System** - Visual badges for categories & data
- ✅ **Expandable Lists** - Click "+X more" for full details

📖 **Full Details:** `RECENT_IMPROVEMENTS.md`

---

## 🐳 Quick Start

### Prerequisites
- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)
- API keys for threat intelligence sources

### 1. Setup Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit with your actual API keys
nano .env
```

### 2. Build and Run

```bash
# Using Make (recommended)
make up

# Or using docker-compose directly
docker-compose up -d
```

### 3. Access the Application

- **Web Interface**: http://localhost:5000
- **Health Check**: http://localhost:5000/ (should return 200 OK)

---

## 📋 Available Commands

### Using Makefile

```bash
make help        # Show all available commands
make build       # Build Docker image
make run         # Start containers
make stop        # Stop containers
make logs-f      # Follow logs
make shell       # Open shell in container
make restart     # Restart containers
make clean       # Remove containers and images
make clean-all   # Remove everything including volumes
```

### Using Docker Compose

```bash
# Build image
docker-compose build

# Start (detached)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart

# View status
docker-compose ps
```

---

## 🔧 Configuration

### API Keys

Set these in `.env` file or pass as environment variables:

**Required:**
```bash
VIRUSTOTAL_API_KEY=your_key
ABUSEIPDB_API_KEY=your_key
```

**Recommended (NEW!):**
```bash
APIVOID_KEY=your_key  # For improved URLVoid results
URLSCAN_API_KEY=your_key
ABUSECH_API_KEY=your_key
```

**Optional:**
```bash
IPAPI_ACCESS_KEY=your_key
IPDATA_API_KEY=your_key
ST_API_KEY=your_key
SHODAN_API_KEY=your_key
```

### Resource Limits

Edit `docker-compose.yml` to adjust:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
```

---

## 🚀 Production Deployment

### With Nginx Reverse Proxy

```bash
# Start with Nginx
make run-nginx

# Or
docker-compose --profile with-nginx up -d
```

Access at: `http://localhost` (port 80)

### Environment Variables for Production

```bash
FLASK_ENV=production
```

### Persistent Data

Cache data is stored in a Docker volume: `cache-data`

To backup:
```bash
docker run --rm -v domain-reputation-webapp_cache-data:/data \
  -v $(pwd):/backup ubuntu tar czf /backup/cache-backup.tar.gz /data
```

---

## 📊 Monitoring

### View Logs

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f webapp

# Last 100 lines
docker-compose logs --tail=100 webapp
```

### Health Check

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' domain-reputation-checker

# Or use make
make health
```

### Container Stats

```bash
docker stats domain-reputation-checker
```

---

## 🔍 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs webapp

# Check if ports are available
ss -tulpn | grep 5000

# Rebuild from scratch
make clean-all
make up
```

### API keys not working

```bash
# Verify environment variables are set
docker-compose exec webapp env | grep API_KEY

# Check if .env file is loaded
docker-compose config
```

### Import errors

```bash
# Check if CLI tool is accessible
docker-compose exec webapp ls -la /app/cli/

# Check Python path
docker-compose exec webapp python -c "import sys; print(sys.path)"

# Test import
docker-compose exec webapp python -c "from domain_reputation_checker import DomainReputationChecker; print('OK')"
```

### Performance issues

```bash
# Increase workers in docker-compose.yml
# Edit CMD in Dockerfile:
# --workers 8  # Increase from 4

# Or use environment variable
docker-compose up -d --scale webapp=2
```

---

## 🔒 Security

### Run as non-root

Already configured:
- User: `appuser` (UID 1000)
- No new privileges
- Read-only where possible

### Network Isolation

Containers run in isolated network:
```yaml
networks:
  domain-reputation-net:
    driver: bridge
```

### Secrets Management

Never commit `.env` file. Use Docker secrets in production:

```yaml
secrets:
  virustotal_key:
    file: ./secrets/virustotal_key.txt
```

---

## 🔄 Updates

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
make rebuild

# Or
docker-compose up -d --build
```

### Update Dependencies

```bash
# Edit requirements.txt
# Then rebuild
make clean
make up
```

---

## 📦 Image Management

### Build for Different Architectures

```bash
# AMD64
docker build --platform linux/amd64 -t domain-reputation-checker:amd64 .

# ARM64
docker build --platform linux/arm64 -t domain-reputation-checker:arm64 .
```

### Tag and Push (if using registry)

```bash
# Tag
docker tag domain-reputation-checker:latest registry.example.com/domain-reputation-checker:latest

# Push
docker push registry.example.com/domain-reputation-checker:latest
```

---

## 🧪 Testing

### Run Tests in Container

```bash
make test

# Or
docker-compose exec webapp python test_attack_reports.py
```

### Interactive Shell

```bash
make shell

# Inside container
python
>>> from domain_reputation_checker import DomainReputationChecker
>>> checker = DomainReputationChecker()
```

---

## 📈 Scaling

### Horizontal Scaling

```bash
# Run multiple instances
docker-compose up -d --scale webapp=3

# With load balancer
docker-compose --profile with-nginx up -d --scale webapp=3
```

### Vertical Scaling

Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'    # More CPUs
      memory: 2G   # More RAM
```

---

## 🗂️ Volume Management

### List Volumes

```bash
docker volume ls | grep domain-reputation
```

### Inspect Volume

```bash
docker volume inspect domain-reputation-webapp_cache-data
```

### Clean Volumes

```bash
# Remove all volumes (WARNING: deletes cache)
docker-compose down -v
```

---

## 🌐 Network Configuration

### Custom Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # External:Internal
```

### Custom Network

```yaml
networks:
  domain-reputation-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

---

## ✅ Best Practices

1. **Always use `.env` file** for API keys
2. **Regular backups** of cache volume
3. **Monitor logs** for errors
4. **Update regularly** for security patches
5. **Use health checks** for reliability
6. **Limit resources** to prevent runaway containers
7. **Use Nginx** for production deployments
8. **Enable HTTPS** with Let's Encrypt
9. **Rotate logs** to prevent disk fill
10. **Test before deploying** updates

---

## 📝 Examples

### Basic Deployment

```bash
# 1. Clone repository
git clone <repo>
cd Domain-Reputation-WebApp

# 2. Setup environment
cp .env.example .env
# Edit .env with your keys

# 3. Deploy
make up

# 4. Verify
curl http://localhost:5000
```

### Production Deployment with Nginx

```bash
# 1. Setup SSL certificates
mkdir ssl
# Copy your SSL certs to ssl/

# 2. Configure Nginx
cp nginx.conf.example nginx.conf
# Edit nginx.conf

# 3. Deploy
make run-nginx

# 4. Test
curl https://yourdomain.com
```

### Development Mode

```bash
# Mount local code for live editing
docker-compose -f docker-compose.dev.yml up
```

---

## 🆘 Support

### Check Container Status

```bash
docker-compose ps
```

### Restart Everything

```bash
make restart
```

### Complete Reset

```bash
make clean-all
make up
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Flask Production Guide](https://flask.palletsprojects.com/en/latest/deploying/)

---

**🎉 Your Domain Reputation Checker is now running in Docker!**

For issues or questions, check the logs first: `make logs-f`
