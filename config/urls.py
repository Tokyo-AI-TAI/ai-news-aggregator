# ruff: noqa
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from news_aggregator.dashboard.views import home
from news_aggregator.feed_service.views import add_feed

urlpatterns = [
    # Root path shows nothing for now
    path("", TemplateView.as_view(template_name="pages/blank.html"), name="root"),
    # Protected routes
    path("home/", login_required(home), name="home"),
    path("add_feed/", login_required(add_feed), name="add_feed"),
    path(
        "about/",
        login_required(TemplateView.as_view(template_name="pages/about.html")),
        name="about",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("news_aggregator.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Feed management - protected
    path("feeds/", include("news_aggregator.dashboard.urls", namespace="dashboard")),
    path(
        "feeds/service/",
        include("news_aggregator.feed_service.urls", namespace="feed_service"),
    ),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
