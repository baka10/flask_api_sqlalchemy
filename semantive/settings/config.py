import configparser

from os.path import abspath, dirname, pardir, join

CURRENT_DIR = abspath(dirname(__file__))
ROOT_DIR = abspath(join(CURRENT_DIR, pardir))

configfile = configparser.ConfigParser()
configfile.read(abspath(join(CURRENT_DIR, "secret.cfg")))


class Config:
    SECRET_KEY = configfile.get("env", "secret")
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://{}:{}@{}/semantive?charset=utf8mb4".format(
            configfile.get("db", "username"),
            configfile.get("db", "password"),
            configfile.get("db", "host"),
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 1800
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    CELERY_BROKER_URL = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL
    CELERY_DEFAULT_QUEUE = "semantive"
    CELERY_QUEUES = {
        CELERY_DEFAULT_QUEUE: {
            "exchange": CELERY_DEFAULT_QUEUE,
            "routing_key": CELERY_DEFAULT_QUEUE
        }
    }
    CELERY_TASK_RESULT_EXPIRES = 3600
    CELERY_IMPORTS = [
        "semantive.apps.scraper.tasks"
    ]
    CELERY_IGNORE_RESULT = False
    CELERY_TIMEZONE = "Europe/Warsaw"
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
    PICTURE_FOLDER = join(ROOT_DIR, "pictures")


class ProdConfig(Config):
    DEBUG = False
    DEBUG_TB_ENABLED = False


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_ENABLED = True
    SQLALCHEMY_ECHO = False


ENV = configfile.get("env", "env")
CONFIGS = {
    "prod": ProdConfig,
    "dev": DevConfig
}.get(ENV, DevConfig)
