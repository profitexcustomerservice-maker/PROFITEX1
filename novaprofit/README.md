# Profitex Platform (Optimized Django Version)

A clean fintech-style earning platform built with Django, DRF, Celery, Redis, and Channels.

## Features
- User registration and JWT login
- Admin-controlled tasks, plans, deposits, withdrawals
- Media-enabled task uploads (image/video)
- Wallet balance tracking and transaction history
- Automatic activity reward engine
- Real-time balance and notification updates
- Simple Django templates UI

## Setup
1. Create a Python environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Copy environment file:
   ```powershell
   copy .env.example .env
   ```
4. Update `.env` values as needed.
   For OTP emails, configure either Gmail SMTP credentials or a real SendGrid sender.
5. Run migrations:
   ```powershell
   python manage.py migrate
   ```
6. Create a superuser:
   ```powershell
   python manage.py createsuperuser
   ```
7. Start services:
   - Redis server
   - Celery worker and beat
   - Django development server

## Development commands
```powershell
python manage.py runserver
celery -A novaprofit worker -l info
celery -A novaprofit beat -l info
python test_email.py
```

## Deployment Notes
- Use MySQL in production by setting `DATABASE_URL` appropriately.
- Set `DEBUG=False` and configure `ALLOWED_HOSTS`.
- Use a production ASGI server (e.g. Daphne) with Channels support.
- Run Redis, Celery, and Django via supervisor/systemd.
- Serve static files via a CDN or web server and configure media storage.
- For Docker deployment, use `docker-compose.prod.yml` with `web`, `redis`, `db`, `celery`, and `celery-beat` services.

## Project Structure
- `accounts`: custom user model, auth, admin registration
- `core`: task and plan management
- `wallet`: balance, transactions, deposits, withdrawals
- `notifications`: notifications and websocket updates

## Notes
- Media files are stored under `/media/`
- Websocket endpoint: `/ws/updates/`
- JWT auth endpoints under `/api/auth/`
- Admin panel available at `/admin/`
- In local development without real email credentials, OTP emails are printed in the runserver terminal.
