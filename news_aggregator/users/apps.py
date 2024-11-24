import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "news_aggregator.users"
    verbose_name = _("Users")

    def ready(self):
        with contextlib.suppress(ImportError):
            import news_aggregator.users.signals  # noqa: F401
