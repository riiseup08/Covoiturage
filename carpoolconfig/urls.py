from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from covoiturage.ussd.views import ussd_callback

handler404 = "covoiturage.views.custom_404"

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/", include("covoiturage.api.urls")),
    path("ussd/", ussd_callback, name="ussd_callback"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("analytics/", include("covoiturage.analytics_urls")),
    path("", include("covoiturage.urls")),
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
