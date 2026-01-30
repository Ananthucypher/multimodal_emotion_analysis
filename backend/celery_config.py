import os
from celery import Celery

# Get Redis URL from env or default to 127.0.0.1 (safer for Windows than localhost)
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')

def make_celery(app_name=__name__):
    celery = Celery(
        app_name,
        broker=REDIS_URL,
        backend=REDIS_URL,
        include=['tasks']
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        # tailored for video processing tasks
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )
    
    return celery

celery_app = make_celery('miro_backend')
