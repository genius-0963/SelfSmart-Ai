# 🐳 Docker Installation Guide for SmartShelf AI

## Quick Installation Steps

### 1. Download Docker Desktop
- Visit: https://www.docker.com/products/docker-desktop/
- Download "Docker Desktop for Mac"
- Choose Apple Chip or Intel Chip based on your Mac

### 2. Install Docker Desktop
1. Open `Docker.dmg` from Downloads
2. Drag `Docker.app` to Applications folder
3. Open Docker.app from Applications
4. Follow setup wizard (may require system password)

### 3. Start Docker
- Docker Desktop will start automatically
- Wait for Docker whale icon in menu bar
- Takes 2-3 minutes to fully start

### 4. Verify Installation
```bash
# Check Docker is installed
docker --version

# Check Docker Compose
docker-compose --version

# Test Docker with hello-world
docker run hello-world
```

### 5. Deploy SmartShelf AI
```bash
# Navigate to project directory
cd /Users/subh/Desktop/selfsmart

# Run enhanced deployment
./scripts/deploy-enhanced.sh deploy
```

## Troubleshooting

### If Docker commands don't work:
1. Restart Docker Desktop
2. Restart Terminal
3. Check Docker status in menu bar

### If deployment fails:
1. Check Docker is running
2. Verify all ports are available
3. Check system resources

## Alternative: Manual Download Links

- **Docker Desktop for Mac (Apple Chip)**: https://desktop.docker.com/mac/main/arm64/Docker.dmg
- **Docker Desktop for Mac (Intel Chip)**: https://desktop.docker.com/mac/main/amd64/Docker.dmg

## After Installation

Once Docker is installed, you'll have access to:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090

## System Requirements

- **macOS 10.14 or newer**
- **4GB RAM minimum**
- **10GB free disk space**
- **Internet connection for initial setup**
