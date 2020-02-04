import importlib

from celery import Celery
from flask import Flask
from flask_restful import Api

from semantive.libs.extensions import db, migrate
from semantive.settings.config import CONFIGS


def create_app(register_stuffs=True):
    app = Flask(__name__)
    app.config.from_object(CONFIGS)
    register_extensions(app)
    if register_stuffs:
        register_models(app)
        register_views(app)
    return app


def create_celery():
    app = create_app(False)
    celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

        def after_return(self, *args, **kwargs):
            db.session.remove()

    celery.Task = ContextTask

    return celery


def register_extensions(app):
    db.init_app(app)


def register_models(app):
    for model in ["scraper"]:
        mod = importlib.import_module("semantive.apps.{}.models".format(model))
    migrate.init_app(app, mod.db)


def register_views(app):
    from semantive.apps.scraper.views import ResourceInfo, ResourceAdder, ResourceDownloader
    api = Api(app=app)
    api.add_resource(ResourceInfo, "/api/resource/info/<task_id>")
    api.add_resource(ResourceAdder, "/api/resource/add/<path:url>")
    api.add_resource(ResourceDownloader, "/api/resource/download/<url>/<data_type>")
