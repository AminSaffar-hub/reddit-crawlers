import os
from functools import lru_cache

from dotenv import load_dotenv
from kombu import Queue

load_dotenv()


def route_task(name, args, kwargs, options, task=None, **kw):
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "celery"}


class BaseConfig:
    broker_url: str = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend: str = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    CELERY_TASK_QUEUES: list = (
        Queue("crawling"),
        Queue("processing"),
        Queue("storage"),
        Queue("media"),
    )

    CELERY_TASK_ROUTES = (route_task,)
    imports = ("celery_tasks.tasks",)

    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    timezone = "UTC"
    worker_prefetch_multiplier = 1

    CELERY_TASK_ACKS_LATE = True
    CELERY_TASK_REJECT_ON_WORKER_LOST = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 20

    worker_hijack_root_logger = False
    worker_log_color = True
    worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
    worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s"

    SELENIUM_HUB_URL = os.environ.get(
        "SELENIUM_HUB_URL", "http://localhost:4444/wd/hub"
    )

    MINIO_HOST = os.environ.get("MINIO_HOST", "localhost")
    MINIO_PORT = os.environ.get("MINIO_PORT", 9000)
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

    SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER", "user")
    SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD", "password")
    SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT", "account")
    SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA", "schema")
    SNOWFLAKE_STAGE = os.environ.get("SNOWFLAKE_STAGE", "stage")
    SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "database")


class DevelopmentConfig(BaseConfig):
    CELERYD_LOG_LEVEL = "INFO"


class ProductionConfig(BaseConfig):
    CELERYD_LOG_LEVEL = "INFO"


@lru_cache()
def get_settings():
    config_cls_dict = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    config_name = os.environ.get("CELERY_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()


settings = get_settings()
