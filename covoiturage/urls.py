from django.urls import path
from .views import (
    landing_view, home_view, register_view, profile_view, public_profile_view,
    add_voyage, add_demande, edit_voyage, delete_voyage,
    edit_demande, delete_demande, validate_correspondance, refuse_correspondance,
    cancel_correspondance, mark_voyage_termine, search_trajets,
    avis_list_view, add_avis_view
)

app_name = 'covoiturage'

urlpatterns = [
    path('', landing_view, name='landing'),
    path('dashboard/', home_view, name='dashboard'),
    path('search/', search_trajets, name='search_trajets'),
    path('accounts/register/', register_view, name='register'),
    
    path('profile/', profile_view, name='profile'),
    path('profile/<str:username>/', public_profile_view, name='public_profile'),
    
    path('add_voyage/', add_voyage, name='add_voyage'),
    path('add_demande/', add_demande, name='add_demande'),
    
    path('edit_voyage/<int:voyage_id>/', edit_voyage, name='edit_voyage'),
    path('delete_voyage/<int:voyage_id>/', delete_voyage, name='delete_voyage'),
    
    path('edit_demande/<int:demande_id>/', edit_demande, name='edit_demande'),
    path('delete_demande/<int:demande_id>/', delete_demande, name='delete_demande'),
    
    path('validate_correspondance/<int:correspondance_id>/', validate_correspondance, name='validate_correspondance'),
    path('refuse_correspondance/<int:correspondance_id>/', refuse_correspondance, name='refuse_correspondance'),
    path('cancel_correspondance/<int:correspondance_id>/', cancel_correspondance, name='cancel_correspondance'),
    path('voyage/<int:voyage_id>/termine/', mark_voyage_termine, name='mark_voyage_termine'),
    path('avis/', avis_list_view, name='avis_list'),
    path('avis/voyage/<int:voyage_id>/user/<int:user_id>/', add_avis_view, name='add_avis'),
]
