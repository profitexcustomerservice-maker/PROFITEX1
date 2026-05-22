# Render Deployment Troubleshooting

## Issue: Service Hanging During Startup (20+ minutes)

### Step 1: Check Render Logs
1. Go to https://dashboard.render.com
2. Click your service "novaprofit"
3. Click "Logs" tab
4. Look for:
   - Last line of output (where it stopped)
   - Any error messages
   - Timeout errors

### Step 2: Identify the Culprit

**If stuck at "Collecting migrations..."**
- Database migration is hanging
- Solution: Modify build command to skip migrations initially

**If stuck at "Collecting static files..."**
- WhiteNoise is processing too many files
- Solution: Reduce static files or skip collection

**If stuck at "Downloading dependencies..."**
- Package installation slow on free tier
- Solution: Wait or reduce dependencies

### Step 3: Fix the Build Command

Update `render.yaml` build command to be more verbose:

```yaml
buildCommand: |
  echo "Step 1: Installing dependencies..."
  pip install -r requirements.txt
  echo "Step 2: Collecting static files..."
  python manage.py collectstatic --noinput --verbosity 0
  echo "Step 3: Running migrations..."
  python manage.py migrate --verbosity 0
  echo "Build complete!"
```

### Step 4: Disable Problematic Services

Temporarily in `render.yaml`, comment out Celery services:

```yaml
# - type: pserv
#   name: novaprofit-celery-worker
# - type: pserv
#   name: novaprofit-celery-beat
```

Deploy with just the web service first.

### Step 5: Test Minimal Config

Try this minimal `buildCommand`:

```yaml
buildCommand: |
  pip install -r requirements.txt
  python manage.py collectstatic --noinput
```

Skip migrations initially - run them manually via SSH.

### Step 6: SSH Into Service (Advanced)

In Render dashboard → your service → "Shell":
```bash
# Check if migrations are running
ps aux | grep manage.py

# Check disk space
df -h

# Check memory
free -h

# Check if stuck on migration
python manage.py migrate --verbosity 2
```

### Step 7: Rebuild Strategy

Try manual deployment with this order:

1. **Remove all services first**:
   - Delete web service
   - Keep database
   - Redeploy

2. **Or clear everything**:
   - Delete service completely
   - Delete database
   - Deploy fresh

3. **Or use alternative start command**:
   Instead of `daphne`, try:
   ```yaml
   startCommand: gunicorn novaprofit.wsgi:application --bind 0.0.0.0:10000 --timeout 120
   ```

## Files to Check

1. **render.yaml** - Build and start commands
2. **requirements.txt** - Ensure all dependencies specified
3. **novaprofit/settings.py** - Check DEBUG=False settings
4. **novaprofit/wsgi.py** - WSGI app configuration

## Quick Restart

In Render Dashboard → Manual Deploy → "Clear build cache and deploy"

This forces a fresh rebuild.
