# Render Deployment Checklist

## Current Status
✅ Docker build: SUCCESS
✅ Dependencies: Installed  
❌ Deployment: FAILED (exit code 128 - missing database)

## What To Do Now

### Step 1: Create PostgreSQL Database (REQUIRED)

In Render Dashboard:
1. Click **"New"** button (top right)
2. Select **"PostgreSQL"**
3. Fill in:
   - **Name**: `novaprofit-db` (or your preference)
   - **PostgreSQL Version**: 15
   - **Region**: Oregon (same as web service)
   - **Plan**: Free
4. Click **"Create Database"**
5. Wait 2-3 minutes for it to initialize
6. When ready, copy the **Internal Database URL**

### Step 2: Connect Database to Web Service

In Render Dashboard → **novaprofit** web service:
1. Click **"Environment"**
2. Add environment variable:
   - **NAME**: `DATABASE_URL`
   - **VALUE**: (paste the Internal Database URL from PostgreSQL service)
3. Click **"Save"**

### Step 3: Deploy

1. Click **"Manual Deploy"** → **"Deploy latest"**
2. Wait for deployment (should take 2-3 minutes)
3. Check logs - you should see Django startup messages

### Step 4: Run Initial Setup (if needed)

If deployment still fails, SSH into service:
1. Render Dashboard → **novaprofit** service
2. Click **"Shell"** tab
3. Run:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Step 5: Verify

Once deployed, test these URLs:
- ✅ `https://novaprofit-1.onrender.com/` (should see homepage)
- ✅ `https://novaprofit-1.onrender.com/admin/` (should see login)
- ✅ `https://novaprofit-1.onrender.com/login/` (should see login form)

## Environment Variables Needed

Make sure these are all set:

### Database
- `DATABASE_URL` = (from PostgreSQL service)

### Django
- `DJANGO_SECRET_KEY` = (your secret key)
- `DEBUG` = False
- `ALLOWED_HOSTS` = novaprofit-1.onrender.com

### Security
- `SECURE_SSL_REDIRECT` = True
- `CORS_ALLOWED_ORIGINS` = https://novaprofit-1.onrender.com
- `CSRF_TRUSTED_ORIGINS` = https://novaprofit-1.onrender.com

### Email
- `EMAIL_HOST_USER` = profitexcustomerservice@gmail.com
- `EMAIL_HOST_PASSWORD` = (Gmail app password)

### Redis (Optional - for now)
- `REDIS_URL` = (leave empty for now, we'll add later)

## Troubleshooting

### If deployment still fails:
1. Check logs in Render Dashboard
2. Look for errors like:
   - "could not connect to database" → Create PostgreSQL service
   - "DJANGO_SECRET_KEY not set" → Add environment variable
   - "ALLOWED_HOSTS" → Update ALLOWED_HOSTS in environment

### If can't access admin:
1. Run in Shell: `python manage.py createsuperuser`
2. Create admin user
3. Try login at `/admin/`

## Next Steps (After Deployment)

1. ✅ Create PostgreSQL database
2. ✅ Connect to web service
3. ✅ Verify deployment successful
4. ⬜ Create superuser account
5. ⬜ Test login functionality
6. ⬜ Add Redis (for real-time features)
7. ⬜ Add Celery workers (for background tasks)
8. ⬜ Configure email sending
9. ⬜ Set up monitoring
