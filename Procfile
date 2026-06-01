web: gunicorn novaprofit.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4 --threads 4 --timeout 120 --access-logfile - --error-logfile -
worker: celery -A novaprofit worker -l info --concurrency=3
beat: celery -A novaprofit beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
