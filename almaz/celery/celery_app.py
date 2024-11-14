import os
from datetime import timedelta

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery("sales_data_service", broker=os.environ.get('REDIS_URL'), backend=os.environ.get('REDIS_URL'))

celery_app.conf.beat_schedule = {
    "fetch-sales-data-daily": {
        "task": "almaz.celery.tasks.fetch_sales_data",
        "schedule": timedelta(seconds=1),
    },
}
celery_app.conf.timezone = "UTC"

celery_app.autodiscover_tasks(["almaz.celery.tasks"])


