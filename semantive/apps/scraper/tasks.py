import os
import tarfile

import requests
from celery.signals import after_task_publish
from flask import current_app as app

from semantive.app_celery import celery
from semantive.apps.scraper.models import Url
from semantive.libs.extensions import db
from semantive.libs.helpers import parse_data_from_url, ParsedUrlData
from semantive.libs.helpers import save_orm_to_db


@celery.task(bind=True, autoretry_for=(Exception,), exponential_backoff=2, retry_kwargs={'max_retries': 2},
             retry_jitter=False)
def get_data_from_url(_, url: str):
    url_instance = Url(url=url.encode("utf-8"))
    db.session.add(url_instance)
    save_orm_to_db()
    try:
        parsed_data: ParsedUrlData = parse_data_from_url(url_instance)
    except requests.exceptions.MissingSchema:
        return f"Invalid URL: {url}"

    add_to_db_parsed_data.delay(parsed_data)
    compress_pictures.delay(url_instance.url)
    return "Task finished"


@celery.task
def add_to_db_parsed_data(parsed_data: ParsedUrlData):
    parsed_data.save_to_db(db)
    return "Task finished"


@celery.task
def compress_pictures(url):
    picture_dir = app.config.get("PICTURE_FOLDER")
    with tarfile.open(os.path.join(picture_dir, f'{url}.tar'), 'w') as tar:
        tar.add(os.path.join(picture_dir, url))
    return f"Archive {url}.tar created"


@after_task_publish.connect
def update_sent_state(sender=None, headers=None, **kwargs):
    task = celery.tasks.get(sender)
    backend = task.backend if task else celery.backend
    backend.store_result(headers['id'], None, "SENT")
