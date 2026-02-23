# 📁 Project Structure

This document describes the organization of the Domain Reputation Checker Web Application.

## 📂 Directory Layout

```
Domain-Reputation-WebApp/
│
├── 🐍 Core Application Files
│   ├── app.py                    # Main Flask application
│   ├── wsgi.py                   # WSGI production server entry point
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template
│   ├── .gitignore                # Git ignore patterns
│   ├── Makefile                  # Docker convenience commands
│   └── README.md                 # Main documentation
│
├── 🎨 Frontend (templates/)
│   └── index.html                # Main web interface
│
├── 📦 Static Assets (static/)
│   ├── favicon.ico               # Browser icon
│   ├── favicon.png               # PNG version
│   └── favicon.svg               # Vector version
│
├── 🐳 Docker (docker/)
│   ├── Dockerfile                # Multi-stage production build
│   ├── docker-compose.yml        # Container orchestration
│   └── .dockerignore             # Build optimization
│
├── 📚 Documentation (docs/)
│   ├── README files
│   │   ├── QUICKSTART.md         # Quick getting started
│   │   ├── DEPLOYMENT.md         # Production deployment
│   │   ├── PROJECT_SUMMARY.md    # Project overview
│   │   └── PROJECT_STRUCTURE.md  # This file
│   │
│   ├── Docker Documentation
│   │   ├── DOCKER_README.md      # Complete Docker guide
│   │   └── DOCKER_SUMMARY.md     # Docker quick reference
│   │
│   ├── Security
│   │   ├── SECURITY.md           # Security features
│   │   └── SECURITY_ENHANCEMENTS.md # Security implementation
│   │
│   ├── Development
│   │   ├── FEATURES.md           # Feature list
│   │   ├── CHANGELOG.md          # Version history
│   │   ├── LATEST_UPDATES.md     # Recent changes
│   │   └── RESTART_WEBAPP.md     # Restart procedures
│   │
│
├── 🔧 Scripts (scripts/)
│   ├── build.sh                  # Docker build script
│   ├── run.sh                    # Development runner
│   └── verify_setup.sh           # Environment validator
│
└── 🧪 Tests (tests/)
    └── test_attack_reports.py    # Attack report tests
```

## 📄 File Descriptions

### Root Level Files

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application with routes, API endpoints, PDF generation |
| `wsgi.py` | Production WSGI server entry point for Gunicorn |
| `requirements.txt` | Python package dependencies |
| `.env.example` | Template for API keys and environment variables |
| `.gitignore` | Git ignore patterns (venv, cache, logs, etc.) |
| `Makefile` | Docker commands (make up, make logs-f, make stop, etc.) |
| `README.md` | Main project documentation and quick start |

### Templates Directory

| File | Purpose |
|------|---------|
| `index.html` | Single-page web application with dark theme UI |

### Static Directory

| File | Purpose |
|------|---------|
| `favicon.ico` | Browser tab icon (ICO format) |
| `favicon.png` | App icon (PNG format, 512x512) |
| `favicon.svg` | Vector icon (SVG format) |

### Docker Directory

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage production container build |
| `docker-compose.yml` | Service orchestration with volumes, networks, health checks |
| `.dockerignore` | Files to exclude from Docker build context |

### Documentation Directory (docs/)

#### Core Documentation
- **QUICKSTART.md** - Fast getting started guide for new users
- **DEPLOYMENT.md** - Production deployment instructions
- **PROJECT_SUMMARY.md** - High-level project overview
- **PROJECT_STRUCTURE.md** - This file (directory organization)

#### Docker Documentation
- **DOCKER_README.md** - Complete Docker deployment guide
- **DOCKER_SUMMARY.md** - Quick Docker reference and commands

#### Security Documentation
- **SECURITY.md** - Security features and best practices
- **SECURITY_ENHANCEMENTS.md** - Detailed security implementation

#### Development Documentation
- **FEATURES.md** - Complete feature list
- **CHANGELOG.md** - Version history and changes
- **LATEST_UPDATES.md** - Most recent updates
- **RESTART_WEBAPP.md** - Application restart procedures

### Scripts Directory

| Script | Purpose |
|--------|---------|
| `build.sh` | Custom Docker image build with CLI validation |
| `run.sh` | Local development server runner |
| `verify_setup.sh` | Environment and dependency checker |

### Tests Directory

| File | Purpose |
|------|---------|
| `test_attack_reports.py` | Tests for AbuseIPDB attack intelligence |

## 🔄 File Relationships

### Application Flow
```
User Browser
    ↓
templates/index.html (Frontend)
    ↓
app.py (Backend API)
    ↓
domain_reputation_checker.py (CLI Tool)
    ↓
External Threat Intel APIs
```

### Docker Build Flow
```
docker-compose.yml
    ↓
Dockerfile
    ↓
Builds from: Parent directory context
    ├── Domain-Reputation-WebApp/ (all app files)
    └── Domain-Reputation-Checker/domain_reputation_checker.py (CLI)
    ↓
Container Image: domain-reputation-checker:latest
```

### Development Workflow
```
1. Edit code in app.py or templates/
2. Test locally: python app.py
3. Build Docker: make build
4. Run container: make up
5. Check logs: make logs-f
6. Update docs/ as needed
```

## 📊 File Size Overview

| Directory/File | Typical Size |
|----------------|--------------|
| `app.py` | ~20KB |
| `templates/index.html` | ~15KB |
| `docs/` | ~50KB total |
| `static/` | ~5KB (icons) |
| `docker/` | ~4KB (configs) |
| `scripts/` | ~7KB total |
| Docker Image | ~450MB |
| venv/ | ~100MB |

## 🎯 Key Design Decisions

### Why Separate Directories?

1. **docker/** - Isolates containerization config from application code
2. **docs/** - Keeps documentation organized and discoverable
3. **scripts/** - Centralizes utility scripts, separate from app logic
4. **tests/** - Standard Python testing structure
5. **static/** - Web best practice for static assets
6. **templates/** - Flask convention for HTML templates

### Why Makefile at Root?

The Makefile references `docker/docker-compose.yml` but stays at the root for convenience:
```bash
make up    # Easier than: docker-compose -f docker/docker-compose.yml up
```

### Why .env.example at Root?

Environment variables are loaded at the application root level, so `.env` and `.env.example` belong there.

### Why Both docker-compose.yml and Makefile?

- **docker-compose.yml** - Complete configuration (services, volumes, networks)
- **Makefile** - Convenience wrapper with shorter commands

## 🔍 Finding Files Quickly

### Need to...
- **Change the UI?** → `templates/index.html`
- **Add API endpoint?** → `app.py`
- **Configure Docker?** → `docker/docker-compose.yml` or `docker/Dockerfile`
- **Update docs?** → `docs/`
- **Add script?** → `scripts/`
- **Set API keys?** → Copy `.env.example` to `.env`
- **Run tests?** → `tests/`
- **Deploy?** → `make up` (or see `docs/DEPLOYMENT.md`)

## 🚀 Quick Commands Reference

```bash
# Development
python app.py                          # Run locally
pip install -r requirements.txt        # Install deps

# Docker
make up                                # Build & start
make logs-f                            # Watch logs
make stop                              # Stop containers
make shell                             # Get shell in container

# Scripts
./scripts/run.sh                       # Dev server
./scripts/verify_setup.sh              # Check setup
./scripts/build.sh                     # Custom Docker build

# Documentation
cat README.md                          # Main docs
cat docs/QUICKSTART.md                 # Quick start
cat docs/DOCKER_README.md              # Docker guide
```

## 📝 Maintenance Notes

### When Adding New Features
1. Update `app.py` or relevant code files
2. Add tests to `tests/`
3. Update `docs/FEATURES.md`
4. Update `docs/CHANGELOG.md`
5. Rebuild Docker: `make rebuild`

### When Updating Documentation
- Keep `README.md` concise (overview + quick start)
- Detailed guides go in `docs/`
- Update `PROJECT_STRUCTURE.md` if adding directories

### When Modifying Docker
- Update `docker/Dockerfile` for build changes
- Update `docker/docker-compose.yml` for service changes
- Update `docs/DOCKER_README.md` with new instructions
- Rebuild: `make clean-all && make up`

## ✅ Organization Benefits

1. **Clear Separation** - Code, config, docs, and scripts are separate
2. **Easy Navigation** - Logical grouping makes files easy to find
3. **Scalability** - Structure supports growth (new features, tests, docs)
4. **Docker-Friendly** - Docker files isolated but accessible
5. **Git-Friendly** - .gitignore properly excludes generated files
6. **Team-Friendly** - Clear structure for multiple contributors
7. **Production-Ready** - Follows best practices for web applications

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview
- [Quick Start](QUICKSTART.md) - Getting started
- [Deployment](DEPLOYMENT.md) - Production deployment
- [Docker Guide](DOCKER_README.md) - Container deployment
- [Security](SECURITY.md) - Security features

---

**Last Updated**: January 23, 2026
**Structure Version**: 2.0 (Organized)
