from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    # Auth
    path('auth/register/', api_views.api_register, name='register'),
    path('auth/login/', api_views.api_login, name='login'),
    path('auth/logout/', api_views.api_logout, name='logout'),
    path('auth/phone/request-otp/', api_views.api_phone_request_otp, name='phone_request_otp'),
    path('auth/phone/verify-otp/', api_views.api_phone_verify_otp, name='phone_verify_otp'),
    path('auth/phone/register/', api_views.api_phone_register, name='phone_register'),

    # Profile
    path('profile/', api_views.api_my_profile, name='my_profile'),
    path('profile/update/', api_views.api_update_profile, name='update_profile'),
    path('profile/<str:username>/', api_views.api_public_profile, name='public_profile'),

    # Voyages
    path('voyages/search/', api_views.api_search_voyages, name='search_voyages'),
    path('voyages/mine/', api_views.api_my_voyages, name='my_voyages'),
    path('voyages/create/', api_views.api_create_voyage, name='create_voyage'),
    path('voyages/<int:voyage_id>/update/', api_views.api_update_voyage, name='update_voyage'),
    path('voyages/<int:voyage_id>/delete/', api_views.api_delete_voyage, name='delete_voyage'),
    path('voyages/<int:voyage_id>/termine/', api_views.api_mark_termine, name='mark_termine'),

    # Demandes
    path('demandes/mine/', api_views.api_my_demandes, name='my_demandes'),
    path('demandes/create/', api_views.api_create_demande, name='create_demande'),
    path('demandes/<int:demande_id>/delete/', api_views.api_delete_demande, name='delete_demande'),

    # Matches
    path('matches/', api_views.api_my_matches, name='my_matches'),
    path('matches/<int:match_id>/validate/', api_views.api_validate_match, name='validate_match'),
    path('matches/<int:match_id>/refuse/', api_views.api_refuse_match, name='refuse_match'),

    # Reviews
    path('reviews/', api_views.api_my_reviews, name='my_reviews'),
    path('reviews/create/', api_views.api_create_review, name='create_review'),

    # Notifications
    path('notifications/', api_views.api_notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', api_views.api_mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', api_views.api_mark_all_notifications_read, name='mark_all_read'),

    # Messaging
    path('conversation/<int:correspondance_id>/', api_views.api_conversation, name='conversation'),
    path('conversation/<int:correspondance_id>/send/', api_views.api_send_message, name='send_message'),

    # Dashboard
    path('dashboard/', api_views.api_dashboard, name='dashboard'),

    # Payments
    path('payments/', api_views.api_my_payments, name='my_payments'),
    path('payments/create/', api_views.api_create_payment, name='create_payment'),
    path('payments/<int:payment_id>/confirm/', api_views.api_confirm_payment, name='confirm_payment'),

    # Wallet (Driver Commission System)
    path('wallet/balance/', api_views.api_wallet_balance, name='wallet_balance'),
    path('wallet/topup/request/', api_views.api_request_topup, name='request_topup'),
    path('wallet/topup/<int:payment_id>/confirm/', api_views.api_confirm_topup, name='confirm_topup'),
    path('wallet/transactions/', api_views.api_wallet_transactions, name='wallet_transactions'),
]
