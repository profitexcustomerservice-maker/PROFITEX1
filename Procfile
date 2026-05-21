web: daphne -b 0.0.0.0 -p 8000 novaprofit.asgi:application
worker: celery -A novaprofit worker -l info
beat: celery -A novaprofit beat -l info
