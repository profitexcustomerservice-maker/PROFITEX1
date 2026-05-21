# RENDER Deployment Guide

## Overview
This guide explains how to deploy the Nova Profit system on Render (https://render.com).

## Prerequisites
- Render account (https://dashboard.render.com/register)
- GitHub repository with this code
- Domain name (optional, Render provides free subdomain)

## Deployment Steps

### 1. Connect GitHub to Render
1. Go to https://dashboard.render.com
2. Click "New" → "Web Service"
3. Select "Build and deploy from a Git repository"
4. Connect your GitHub account
5. Select the `novaprofit` repository

### 2. Configure Web Service
The `render.yaml` file in the repository root will automatically configure:
- **Environment**: Python
- **Build Command**: Installs dependencies and runs migrations
- **Start Command**: Starts Daphne ASGI server on port 10000
- **Instance**: Free tier (with auto-scaling)

### 3. Set Environment Variables
In the Render dashboard, go to your service's **Environment** tab and add these variables:

#### Required Variables
```
DJANGO_SECRET_KEY=<generate-a-random-secret-key>
DEBUG=False
ALLOWED_HOSTS=novaprofit.onrender.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

#### Email Configuration (choose one)
**Option A: Gmail SMTP**
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-specific-password>
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Option B: SendGrid (Recommended for Production)**
```
SENDGRID_API_KEY=<your-sendgrid-api-key>
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_USE_SENDGRID_BACKEND=True
```

#### CORS Configuration
```
CORS_ALLOWED_ORIGINS=https://novaprofit.onrender.com
CSRF_TRUSTED_ORIGINS=https://novaprofit.onrender.com
```

#### Optional: Admin Credentials
```
ADMIN_EMAIL=admin@yoursystem.com
ADMIN_PASSWORD=<secure-password>
```

### 4. Database Setup
The `render.yaml` includes PostgreSQL (free tier). After deployment:

1. Connect to the PostgreSQL database:
   ```
   # Use the DATABASE_URL provided by Render
   psql <DATABASE_URL>
   ```

2. If needed, manually create superuser:
   ```
   # SSH into your Render service
   python manage.py createsuperuser
   ```

### 5. Verification

After deployment completes:

1. **Test the application**:
   - Navigate to `https://novaprofit.onrender.com`
   - Test login at `/login/`
   - Access admin at `/admin/`

2. **Check logs**:
   - Render dashboard → Logs tab
   - Monitor for any errors

3. **Monitor services**:
   - Web service status
   - Redis connection
   - Celery worker and beat scheduler

## Services Included

### Web Service
- **Name**: novaprofit
- **Builds from**: render.yaml
- **Port**: 10000
- **ASGI**: Daphne
- **Auto-restart**: Yes

### Database
- **Type**: PostgreSQL
- **Version**: 15
- **Plan**: Free tier
- **Backups**: Daily (retention: 7 days)

### Redis
- **Type**: Redis
- **Purpose**: 
  - Message broker for Celery
  - Channel layer for WebSockets
  - Cache backend
- **Plan**: Free tier

### Celery Worker
- **Purpose**: Process background tasks
- **Concurrency**: 2 workers (free tier limitation)
- **Tasks**:
  - Activity rewards (every 5 minutes)
  - User balance updates
  - Transaction processing

### Celery Beat
- **Purpose**: Schedule periodic tasks
- **Scheduler**: Django Celery Beat
- **Tasks** configured in `novaprofit/settings.py`

## Important Notes

### Static Files
- Collected during build using WhiteNoise
- Served with gzip compression
- Stored in `staticfiles/` directory

### Media Files
- Uploaded to `media/` directory
- **Warning**: Free tier Render services have ephemeral storage (deleted on restart)
- **Solution for production**: Use external storage (AWS S3, Cloudinary, etc.)

### Scaling
The free tier of Render includes:
- Auto-sleep after 15 min of inactivity
- Auto-wake on first request
- Suitable for development/testing only

For production, upgrade to paid plans for:
- Always-on services
- Better performance
- Guaranteed uptime

## SSL/HTTPS
- Automatically enabled
- Free SSL certificate via Let's Encrypt
- Certificate auto-renews

## Custom Domain
1. In Render dashboard → Settings
2. Add custom domain
3. Add CNAME DNS record pointing to Render
4. Update `ALLOWED_HOSTS` in environment variables

## Troubleshooting

### Build Failures
- Check build logs in Render dashboard
- Ensure all requirements are in `requirements.txt`
- Verify Python version compatibility

### Runtime Errors
- Check service logs in Render dashboard
- Verify environment variables are set correctly
- Check database connection with `python manage.py dbshell`

### WebSocket Issues
- Ensure Redis is connected properly
- Check Channels configuration
- Verify CORS and CSRF settings

### Email Not Sending
- Verify `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
- For Gmail: Use App Password, not regular password
- Check Render logs for SMTP errors
- Consider using SendGrid for better deliverability

## Deployment Checklist

- [ ] Fork/clone repository on GitHub
- [ ] Connect GitHub to Render
- [ ] Set all required environment variables
- [ ] Configure custom domain (if using)
- [ ] Test login functionality
- [ ] Test email/OTP flow
- [ ] Test task completion and rewards
- [ ] Monitor Redis and Celery in logs
- [ ] Set up monitoring/alerts
- [ ] Document database connection string

## Advanced Configuration

### Database Optimization
```
CONN_MAX_AGE=600  # Connection pooling (seconds)
DATABASE_POOL_SIZE=5
```

### Celery Configuration
```
CELERY_TASK_SOFT_TIME_LIMIT=300  # 5 minutes
CELERY_TASK_TIME_LIMIT=600  # 10 minutes hard limit
```

### Cache Configuration
```
CACHE_MIDDLEWARE_SECONDS=300
CACHE_MIDDLEWARE_ANONYMOUS_ONLY=True
```

## Monitoring & Logs

Monitor these key metrics:
- HTTP response times
- Database query performance
- Celery task completion rate
- Redis memory usage
- Email delivery status

## Support & Resources

- Render Documentation: https://render.com/docs
- Django Documentation: https://docs.djangoproject.com
- Channels Documentation: https://channels.readthedocs.io
- Celery Documentation: https://docs.celeryproject.io

## Next Steps

1. Deploy to Render
2. Create initial test data
3. Configure admin users
4. Set up monitoring
5. Test all core features
6. Plan scaling strategy
