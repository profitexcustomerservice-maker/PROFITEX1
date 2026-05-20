# PROFITEX PLATFORM - DEPLOYMENT GUIDE

## Overview
PROFITEX PLATFORM is a complete fintech-like earning system with task-based earning, admin-controlled plans, media tasks, automatic wallet increment engine, and real-time updates.

## System Architecture
- **Backend**: Django 5.0 + Django REST Framework
- **Database**: SQLite (development) / MySQL (production)
- **Authentication**: JWT (SimpleJWT)
- **Background Tasks**: Celery + Redis
- **Real-time**: Django Channels (WebSocket)
- **File Storage**: Django Media System

## Quick Start

### 1. Environment Setup
```bash
# Clone and navigate to project
cd novaprofit

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your settings
```

### 2. Database Setup
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Start Services
```bash
# Start Django server
python manage.py runserver

# Start Celery worker (in separate terminal)
celery -A novaprofit worker -l info

# Start Celery beat scheduler (in separate terminal)
celery -A novaprofit beat -l info

# Start Redis (if not running)
redis-server
```

## Access Points

### User Interface
- **Login/Register**: http://127.0.0.1:8000/login/
- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Tasks**: http://127.0.0.1:8000/tasks_page/
- **Plans**: http://127.0.0.1:8000/plans_page/
- **Wallet**: http://127.0.0.1:8000/wallet/

### Admin Interface
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Default Admin**: admin@profitex.com / admin123

### API Endpoints
- **Authentication**: 
  - POST /api/auth/register/
  - POST /api/auth/login/
  - GET /api/auth/me/
- **Tasks**: GET/POST /api/tasks/
- **Plans**: GET/POST /api/plans/
- **User Tasks**: GET/POST /api/user-tasks/
- **User Plans**: GET/POST /api/user-plans/
- **Transactions**: GET /api/transactions/
- **Deposits**: GET/POST /api/deposits/
- **Withdrawals**: GET/POST /api/withdrawals/
- **Notifications**: GET /api/notifications/

## Features Verification

### 1. User Registration & Login
- Users can register with email and password
- Automatic wallet creation on registration
- JWT authentication for API access

### 2. Task System
- Admin can create tasks with rewards
- Users can view and complete tasks
- Automatic wallet credit on task completion
- Media support (images/videos)

### 3. Plan System
- Admin can create subscription plans
- Users can join plans (wallet deduction)
- Plan duration and reward tracking

### 4. Wallet System
- Automatic balance updates
- Transaction logging
- Deposit/withdrawal requests
- Admin approval system

### 5. Real-time Updates
- WebSocket notifications
- Live balance updates
- Real-time task completion feedback

### 6. Background Tasks
- Activity rewards every 5 minutes
- Anti-abuse protection
- Automatic user tracking

## Production Deployment

### Environment Variables
```bash
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=mysql://user:pass@host:port/dbname
REDIS_URL=redis://host:port/0
DATABASE_SSL_REQUIRE=True
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

### Docker Deployment
```bash
# Build the production image
docker compose -f docker-compose.prod.yml build

# Create and start services
docker compose -f docker-compose.prod.yml up -d

# Run migrations and collect static files
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate
docker compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput
```

### Database Setup (MySQL)
```bash
# Create database
CREATE DATABASE profitex CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create user
CREATE USER 'profitex'@'%' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON profitex.* TO 'profitex'@'%';
FLUSH PRIVILEGES;
```

### Web Server (Nginx)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location /static/ {
        alias /path/to/project/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/project/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Process Manager (Gunicorn)
```bash
# Install
pip install gunicorn

# Run
gunicorn novaprofit.wsgi:application --bind 127.0.0.1:8000
```

### Systemd Services
```ini
# /etc/systemd/system/profitex.service
[Unit]
Description=Profitex Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/novaprofit
ExecStart=/path/to/venv/bin/gunicorn novaprofit.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Security Considerations
- Use strong SECRET_KEY
- Enable HTTPS in production
- Configure CORS properly
- Regular security updates
- Database connection encryption
- File upload validation

## Monitoring & Maintenance
- Log monitoring
- Database backups
- Performance monitoring
- Error tracking
- User activity monitoring

## Troubleshooting
- Check Django logs: `python manage.py runserver --verbosity=2`
- Verify Celery: `celery -A novaprofit inspect active`
- Test Redis: `redis-cli ping`
- Database connectivity: `python manage.py dbshell`

## Support
- Check admin panel for system status
- Monitor transaction logs
- Review user activity
- Check Celery task execution
