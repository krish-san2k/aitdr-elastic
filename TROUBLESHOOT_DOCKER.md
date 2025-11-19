# 🐳 Docker Setup Troubleshooting

## Problem: "Cannot connect to Docker daemon"

**Root Cause**: Docker Desktop is not running

### Solution

#### macOS

**Option 1: Start Docker Desktop Manually**
1. Open Finder
2. Go to Applications
3. Find "Docker.app"
4. Double-click to start
5. Wait for "Docker is running" message in menu bar

**Option 2: Start from Terminal**
```bash
# If Docker Desktop installed in /Applications
open /Applications/Docker.app

# Wait 30-60 seconds for startup
# You'll see Docker icon in menu bar when ready
```

**Option 3: Check if Docker is Running**
```bash
# This should work once Docker is running
docker --version
docker run hello-world

# If still failing, try:
docker ps
```

**Option 4: Restart Docker**
```bash
# If Docker is stuck/frozen
osascript -e 'quit app "Docker"'
sleep 2
open /Applications/Docker.app
```

---

### Verify Docker is Running

Once started, test with:

```bash
# Should show Docker version
docker --version

# Should show Docker info
docker ps

# Should run a test container
docker run --rm hello-world
```

Expected output:
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

---

## Problem: Docker Compose Warning About `version`

**Status**: ✅ **FIXED** - Already removed from your file

The `version: '3.8'` line in docker-compose.yml is now removed. This is correct for modern Docker Compose (v2+).

---

## Now Try Again

Once Docker is running:

```bash
cd /Users/krishna/Desktop/CareerGrowth/Coding/aitdr-elastic

# Verify Docker is working
docker ps

# Then run the startup script
bash scripts/quickstart.sh
```

---

## If Docker Still Won't Start

### Try These Steps

1. **Force quit Docker**
   ```bash
   pkill -9 com.docker.backend
   pkill -9 Docker
   ```

2. **Wait 5 seconds, then restart**
   ```bash
   sleep 5
   open /Applications/Docker.app
   ```

3. **Check Docker logs**
   ```bash
   # Logs are usually in:
   cat ~/Library/Logs/Docker.log
   ```

4. **Restart Docker daemon**
   ```bash
   # Click Docker menu icon → Restart
   ```

---

## Common macOS Docker Issues

### Issue: "Docker Desktop needs privileged helper"
**Solution**: Open Docker, enter password when prompted

### Issue: "Cannot allocate memory"
**Solution**: 
- Docker Desktop → Preferences → Resources
- Increase memory allocation
- Recommended: 4-8 GB

### Issue: "Cannot connect to Docker"
**Solution**:
- Docker Desktop → Preferences → Reset
- Click "Reset to factory defaults"
- Restart computer
- Start Docker again

---

## Alternative: Check System Resources

```bash
# Check available RAM
vm_stat

# Check disk space
df -h

# Check CPU
sysctl hw.ncpu

# Recommended: 4GB+ RAM, 50GB+ disk
```

---

## Once Docker is Running

```bash
# Navigate to project
cd /Users/krishna/Desktop/CareerGrowth/Coding/aitdr-elastic

# Copy environment
cp infra/env.example .env

# Start the stack
bash scripts/quickstart.sh
```

This will:
✅ Check Docker is running  
✅ Build all images  
✅ Start all services  
✅ Create indices  
✅ Show URLs  

---

## Quick Reference

```bash
# Start Docker
open /Applications/Docker.app

# Verify it's running
docker ps

# View Docker Desktop
# Click Docker icon in menu bar (top-right)

# Start AITDR stack
bash scripts/quickstart.sh

# View logs
make logs

# Stop everything
make down
```

---

**Status**: Ready to start once Docker Desktop is running!

Good luck! 🚀
