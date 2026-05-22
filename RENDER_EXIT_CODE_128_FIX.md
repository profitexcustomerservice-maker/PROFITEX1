# Quick Render Deployment Fix

## If deployment still shows "exit code 128":

### Check 1: Verify DATABASE_URL is Set

1. Go to **Render Dashboard** → **novaprofit** (your web service)
2. Click **Environment** tab
3. Look for `DATABASE_URL` in the list
4. If it's NOT there, add it:
   - Click **Add Environment Variable**
   - NAME: `DATABASE_URL`
   - VALUE: `postgresql://novaprofit_db_user:KP7hK1ZdZAmhuBSH1dMxpmjcdtg12rHW@dpg-d87q5vcm0tmc73830tng-a/novaprofit_db`
   - Click **Save**

### Check 2: Verify Other Required Variables

Make sure these are ALL set in Environment:

```
DEBUG = False
DJANGO_SECRET_KEY = (your secret key - run: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
ALLOWED_HOSTS = novaprofit-1.onrender.com
SECURE_SSL_REDIRECT = True
CORS_ALLOWED_ORIGINS = https://novaprofit-1.onrender.com
CSRF_TRUSTED_ORIGINS = https://novaprofit-1.onrender.com
EMAIL_HOST_USER = profitexcustomerservice@gmail.com
EMAIL_HOST_PASSWORD = (your Gmail app password)
```

### Check 3: Deploy Again

1. Click **Manual Deploy** button
2. Select **Deploy latest commit**
3. Wait 3-5 minutes

### Check 4: View Logs

If still failing:
1. Click **Logs** tab
2. Look for error messages like:
   - `could not connect to database` → DATABASE_URL not set
   - `DJANGO_SECRET_KEY not found` → Missing secret key
   - `OperationalError` → Database connection failed

### Alternative: Clear Cache and Redeploy

If still stuck:
1. Click **Manual Deploy**
2. **Clear build cache and deploy**
3. Wait for fresh build

This forces a complete rebuild from scratch.

## Still Not Working?

If it still fails after these steps:
1. Note the exact error from the Logs
2. SSH into the service (if available in paid tier)
3. Run: `python manage.py migrate` manually

For now, focus on making sure:
✅ DATABASE_URL is set
✅ DJANGO_SECRET_KEY is set  
✅ DEBUG = False
✅ Click Manual Deploy
