"""URL Configuration for Analytics Dashboard"""

from django.urls import path
from . import analytics_views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', analytics_views.analytics_dashboard, name='dashboard'),
    path('api/<str:data_type>/', analytics_views.analytics_api, name='api'),
]