from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'covoiturage'

urlpatterns = [
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest'),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='service_worker'),
    path('', views.landing_view, name='landing'),
    path('dashboard/', views.home_view, name='dashboard'),
    path('search/', views.search_trajets, name='search_trajets'),
    path('accounts/register/', views.register_view, name='register'),
    
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
    
    path('add_voyage/', views.add_voyage, name='add_voyage'),
    path('add_demande/', views.add_demande, name='add_demande'),
    
    path('edit_voyage/<int:voyage_id>/', views.edit_voyage, name='edit_voyage'),
    path('delete_voyage/<int:voyage_id>/', views.delete_voyage, name='delete_voyage'),
    
    path('edit_demande/<int:demande_id>/', views.edit_demande, name='edit_demande'),
    path('delete_demande/<int:demande_id>/', views.delete_demande, name='delete_demande'),
    
    path('validate_correspondance/<int:correspondance_id>/', views.validate_correspondance, name='validate_correspondance'),
    path('refuse_correspondance/<int:correspondance_id>/', views.refuse_correspondance, name='refuse_correspondance'),
    path('cancel_correspondance/<int:correspondance_id>/', views.cancel_correspondance, name='cancel_correspondance'),
    path('voyage/<int:voyage_id>/termine/', views.mark_voyage_termine, name='mark_voyage_termine'),
    path('avis/', views.avis_list_view, name='avis_list'),
    path('avis/voyage/<int:voyage_id>/user/<int:user_id>/', views.add_avis_view, name='add_avis'),
    path('geo/forward/', views.geocode_forward, name='geocode_forward'),
    path('geo/reverse/', views.geocode_reverse, name='geocode_reverse'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.notifications_mark_read, name='notifications_mark_read'),
    path('notifications/mark_all_read/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
    
    # Messagerie
    path('conversation/<int:correspondance_id>/', views.conversation_view, name='conversation'),
]