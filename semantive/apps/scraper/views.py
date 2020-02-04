import logging
import os
import urllib.parse
from io import StringIO

from flask import current_app as app
from flask import send_file, Response, stream_with_context
from flask_restful import Resource
from sqlalchemy.orm.exc import NoResultFound

from semantive.apps.scraper.models import Text, Url
from semantive.apps.scraper.tasks import get_data_from_url
from semantive.libs.extensions import db
from semantive.app_celery import celery
logging.basicConfig(level=logging.DEBUG)


class ResourceAdder(Resource):
    def get(self, url):
        if not url.startswith("http"):
            url = urllib.parse.urljoin("https://", url)
        result = get_data_from_url.delay(url)
        return result.task_id, 200


class ResourceInfo(Resource):
    def get(self, task_id):
        result = celery.AsyncResult(task_id)
        return f"{result.state if result.state != 'PENDING' else 'MISSING'}", 200


class ResourceDownloader(Resource):

    def get(self, url, data_type):
        print(data_type)
        if data_type == "picture":
            return self._return_picture(url)
        elif data_type == "text":
            return self._return_text(url)
        else:
            response = Response("Chose from: [picture|text]", 400)
        return response

    @staticmethod
    def _return_picture(url):
        try:
            filepath = os.path.join(app.config.get("PICTURE_FOLDER"), f'{url}.tar')
            return send_file(filepath, as_attachment=True)
        except FileNotFoundError:
            return f"Pictures was not found for '{url}'", 204

    @staticmethod
    def _return_text(url):
        try:
            url_id = db.session.query(
                Url.id
            ).filter(
                Url.url == url
            ).first()

            text_content = db.session.query(
                Text.text
            ).filter(
                Text.url_id == url_id
            ).first()
            response = Response(stream_with_context(next(line for line in StringIO(text_content))))
            response.headers['Content-Disposition'] = f'attachment; filename={url}.txt'
        except NoResultFound:
            return f"File not found for '{url}' URL contents.", 204
