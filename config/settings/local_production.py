from .production import *  # noqa

# Override problematic production settings
SECURE_PROXY_SSL_HEADER = None
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Use standard cookie names
SESSION_COOKIE_NAME = "sessionid"
CSRF_COOKIE_NAME = "csrftoken"

# Disable compression for local testing
# COMPRESS_ENABLED = False
# COMPRESS_OFFLINE = False

# Use local storage for static files
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Optional: Enable Celery tasks
CELERY_TASK_ALWAYS_EAGER = False
