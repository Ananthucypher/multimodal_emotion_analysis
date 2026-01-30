# 🛠️ Setting Up Redis for MIRO on Windows

The error `Error 10061 connecting to localhost:6379` occurs because the **Redis server** is not running. MIRO uses Redis as a message broker to handle background video processing tasks.

Since you are on Windows, you have two easy options to get Redis running:

## Option 1: Use Memurai (Recommended for Windows)
Memurai is a native Windows port of Redis.
1. Download **Memurai Developer Edition** (Free) from: [https://www.memurai.com/get-memurai](https://www.memurai.com/get-memurai)
2. Install it. It runs as a Windows Service automatically.
3. That's it! Your Celery worker should now connect.

## Option 2: Use Redis for Windows (Open Source)
1. Download `Redis-x64-5.0.14.1.msi` from: [https://github.com/tporadowski/redis/releases](https://github.com/tporadowski/redis/releases)
2. Run the installer.
3. Ensure "Add the Redis installation folder to the PATH environment variable" is checked.
4. During installation, perform a default installation.

## Verification
After installing, open a new terminal and run:
```powershell
redis-cli ping
```
If it returns `PONG`, you are ready to go!

---

### Restarting the System
Once Redis is running:
1. Close your failing `celery` terminal.
2. Open a new terminal.
3. Run the worker command again:
   ```bash
   cd backend
   celery -A celery_config.celery_app worker --pool=solo --loglevel=info
   ```
