"""
localhub_config/urls.py — project-level URL configuration.

NOTE (Step 7 fix): Django's built-in admin site is now mounted at
"django-admin/" instead of "admin/". It used to live at "admin/",
which swallowed every request under that prefix — including this
app's own /admin/item/<pk>/approve/ and
/admin/withdrawal/<pk>/process/ routes (see core/urls.py). Django
tries django.contrib.admin's URLconf first, and that URLconf 404s
internally on any sub-path it doesn't recognise rather than falling
through to core.urls, so those two routes were completely
unreachable until this moved.

If you have the Django admin bookmarked at /admin/, update that
bookmark to /django-admin/.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="login", permanent=False)),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
