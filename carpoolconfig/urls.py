from django.contrib import admin
from django.urls import path, include

handler404 = 'covoiturage.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('covoiturage.urls')), # On délègue TOUT à l'application
]
