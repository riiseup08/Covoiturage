"""Advanced Analytics Views for Covoiturage Platform"""

from django.shortcuts import render
from django.db.models import Count, Avg, Sum, F, Q, ExpressionWrapper, FloatField, Min, Max
from django.db.models.functions import TruncMonth, TruncWeek, ExtractHour, ExtractWeekDay
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import Voyage, Demande, Correspondance, Avis, Profile, User
import json


@login_required
def analytics_dashboard(request):
    """Main analytics dashboard with comprehensive statistics."""
    
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    
    # ========== KEY METRICS ==========
    total_voyages = Voyage.objects.count()
    total_demandes = Demande.objects.count()
    total_matches = Correspondance.objects.filter(is_validated=True).count()
    total_users = User.objects.count()
    
    # Active users (with voyages or demandes in last 30 days)
    active_drivers = Voyage.objects.filter(created_at__gte=last_30_days).values('conducteur').distinct().count()
    active_passengers = Demande.objects.filter(date_voyage__gte=last_30_days.date()).values('passager').distinct().count()
    
    # Revenue estimation (total potential earnings)
    total_revenue_potential = Voyage.objects.aggregate(
        total=Sum(F('prix_par_place') * F('places_disponibles'))
    )['total'] or 0
    
    recent_revenue = Voyage.objects.filter(created_at__gte=last_30_days).aggregate(
        total=Sum(F('prix_par_place') * F('places_disponibles'))
    )['total'] or 0
    
    # ========== TRIP TRENDS (Last 6 months) ==========
    six_months_ago = now - timedelta(days=180)
    monthly_trips = Voyage.objects.filter(created_at__gte=six_months_ago).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    monthly_labels = [t['month'].strftime('%B %Y') for t in monthly_trips]
    monthly_data = [t['count'] for t in monthly_trips]
    
    # ========== POPULAR ROUTES ==========
    popular_routes = Voyage.objects.values('ville_depart', 'ville_arrivee').annotate(
        trip_count=Count('id'),
        avg_price=Avg('prix_par_place'),
        total_seats=Sum('places_disponibles')
    ).order_by('-trip_count')[:10]
    
    routes_labels = [f"{r['ville_depart']} → {r['ville_arrivee']}" for r in popular_routes]
    routes_data = [r['trip_count'] for r in popular_routes]
    routes_prices = [float(r['avg_price'] or 0) for r in popular_routes]
    
    # ========== USER GROWTH ==========
    user_growth = User.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')[:12]
    
    user_labels = [u['month'].strftime('%b %Y') for u in user_growth]
    user_data = [u['count'] for u in user_growth]
    cumulative_users = []
    running_total = 0
    for count in user_data:
        running_total += count
        cumulative_users.append(running_total)
    
    # ========== RATING DISTRIBUTION ==========
    rating_distribution = Avis.objects.values('note').annotate(
        count=Count('id')
    ).order_by('note')
    
    rating_labels = [f"{r['note']} ⭐" for r in rating_distribution]
    rating_data = [r['count'] for r in rating_distribution]
    
    avg_rating = Avis.objects.aggregate(avg=Avg('note'))['avg'] or 0
    total_reviews = Avis.objects.count()
    
    # ========== TRUST SCORE DISTRIBUTION ==========
    trust_brackets = [
        (0, 25, 'Low (0-25)'),
        (26, 50, 'Medium (26-50)'),
        (51, 75, 'Good (51-75)'),
        (76, 100, 'Excellent (76-100)')
    ]
    
    trust_distribution = []
    for low, high, label in trust_brackets:
        count = Profile.objects.filter(trust_score__gte=low, trust_score__lte=high).count()
        trust_distribution.append({'label': label, 'count': count})
    
    trust_labels = [t['label'] for t in trust_distribution]
    trust_data = [t['count'] for t in trust_distribution]
    
    # ========== DRIVER VS PASSENGER RATIO ==========
    driver_count = Profile.objects.filter(is_driver=True).count()
    non_driver_count = Profile.objects.filter(is_driver=False).count()
    
    # ========== VERIFICATION STATUS ==========
    verification_stats = Profile.objects.values('verification_status').annotate(
        count=Count('id')
    )
    
    verification_labels = [v['verification_status'].replace('_', ' ').title() for v in verification_stats]
    verification_data = [v['count'] for v in verification_stats]
    
    # ========== MATCH SUCCESS RATE ==========
    total_correspondances = Correspondance.objects.count()
    successful_matches = Correspondance.objects.filter(
        is_validated=True,
        refus_conducteur=False,
        refus_passager=False
    ).count()
    match_success_rate = (successful_matches / total_correspondances * 100) if total_correspondances > 0 else 0
    
    # ========== PEAK HOURS ANALYSIS ==========
    # Use Python to extract hours (more compatible with SQLite)
    voyages_for_hours = list(Voyage.objects.values('id', 'date_depart'))
    hour_counts = {}
    for v in voyages_for_hours:
        if v['date_depart']:
            hour = v['date_depart'].hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    # Fill all hours 0-23
    hours_labels = [f"{h:02d}:00" for h in range(24)]
    hours_data = [hour_counts.get(h, 0) for h in range(24)]
    
    # ========== DAY OF WEEK ANALYSIS ==========
    # Use Python to extract day of week (more compatible with SQLite)
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    voyages_for_weekday = list(Voyage.objects.values('id', 'date_depart'))
    weekday_counts = {i: 0 for i in range(7)}  # 0=Monday, 6=Sunday
    for v in voyages_for_weekday:
        if v['date_depart']:
            # Python weekday: 0=Monday, 6=Sunday
            weekday_counts[v['date_depart'].weekday()] += 1
    
    weekday_data = [weekday_counts[i] for i in range(7)]
    
    # ========== TOP DRIVERS ==========
    top_drivers = User.objects.annotate(
        trip_count=Count('voyage', filter=Q(voyage__is_validated=True)),
        total_seats_offered=Sum('voyage__places_disponibles'),
        avg_rating=Avg('avis_recus__note')
    ).filter(trip_count__gt=0).order_by('-trip_count')[:5]
    
    top_drivers_data = [{
        'username': d.username,
        'trips': d.trip_count,
        'rating': round(d.avg_rating, 1) if d.avg_rating else 'N/A'
    } for d in top_drivers]
    
    # ========== BAGGAGE TYPE DISTRIBUTION ==========
    baggage_dist = Voyage.objects.values('type_bagage_accepte').annotate(
        count=Count('id')
    ).order_by('type_bagage_accepte')
    
    baggage_labels = {
        'petit': 'Small',
        'moyen': 'Medium', 
        'gros': 'Large',
        'tous': 'All Types'
    }
    baggage_chart_labels = [baggage_labels.get(b['type_bagage_accepte'], b['type_bagage_accepte']) for b in baggage_dist]
    baggage_data = [b['count'] for b in baggage_dist]
    
    # ========== PRICE ANALYSIS ==========
    price_stats = Voyage.objects.aggregate(
        avg_price=Avg('prix_par_place'),
        min_price=Min('prix_par_place'),
        max_price=Max('prix_par_place')
    )
    
    # Price ranges
    price_ranges = [
        (0, 10, '0-10€'),
        (11, 25, '11-25€'),
        (26, 50, '26-50€'),
        (51, 100, '51-100€'),
        (101, 10000, '100€+')
    ]
    
    price_distribution = []
    for low, high, label in price_ranges:
        count = Voyage.objects.filter(prix_par_place__gte=low, prix_par_place__lte=high).count()
        price_distribution.append({'label': label, 'count': count})
    
    price_dist_labels = [p['label'] for p in price_distribution]
    price_dist_data = [p['count'] for p in price_distribution]
    
    # ========== RECENT ACTIVITY ==========
    recent_voyages = Voyage.objects.select_related('conducteur').order_by('-created_at')[:5]
    recent_reviews = Avis.objects.select_related('auteur', 'utilisateur_note', 'voyage').order_by('-created_at')[:5]
    
    context = {
        # Key metrics
        'total_voyages': total_voyages,
        'total_demandes': total_demandes,
        'total_matches': total_matches,
        'total_users': total_users,
        'active_drivers': active_drivers,
        'active_passengers': active_passengers,
        'total_revenue_potential': total_revenue_potential,
        'recent_revenue': recent_revenue,
        'avg_rating': round(avg_rating, 2),
        'total_reviews': total_reviews,
        'match_success_rate': round(match_success_rate, 1),
        
        # Chart data - Monthly trips
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
        
        # Chart data - Popular routes
        'routes_labels': json.dumps(routes_labels),
        'routes_data': json.dumps(routes_data),
        'routes_prices': json.dumps(routes_prices),
        
        # Chart data - User growth
        'user_labels': json.dumps(user_labels),
        'user_data': json.dumps(user_data),
        'cumulative_users': json.dumps(cumulative_users),
        
        # Chart data - Ratings
        'rating_labels': json.dumps(rating_labels),
        'rating_data': json.dumps(rating_data),
        
        # Chart data - Trust scores
        'trust_labels': json.dumps(trust_labels),
        'trust_data': json.dumps(trust_data),
        
        # Chart data - Driver ratio
        'driver_count': driver_count,
        'non_driver_count': non_driver_count,
        
        # Chart data - Verification
        'verification_labels': json.dumps(verification_labels),
        'verification_data': json.dumps(verification_data),
        
        # Chart data - Peak hours
        'hours_labels': json.dumps(hours_labels),
        'hours_data': json.dumps(hours_data),
        
        # Chart data - Weekday
        'weekday_labels': json.dumps(day_names),
        'weekday_data': json.dumps(weekday_data),
        
        # Chart data - Baggage
        'baggage_labels': json.dumps(baggage_chart_labels),
        'baggage_data': json.dumps(baggage_data),
        
        # Chart data - Price distribution
        'price_dist_labels': json.dumps(price_dist_labels),
        'price_dist_data': json.dumps(price_dist_data),
        
        # Top drivers
        'top_drivers': top_drivers_data,
        
        # Price stats
        'avg_price': round(price_stats['avg_price'] or 0, 2),
        'min_price': price_stats['min_price'] or 0,
        'max_price': price_stats['max_price'] or 0,
        
        # Recent activity
        'recent_voyages': recent_voyages,
        'recent_reviews': recent_reviews,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def analytics_api(request):
    """API endpoint for real-time analytics updates."""
    from django.http import JsonResponse
    
    data_type = request.GET.get('type', 'overview')
    
    if data_type == 'overview':
        # Real-time overview stats
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        data = {
            'total_voyages': Voyage.objects.count(),
            'total_users': User.objects.count(),
            'recent_activity': Voyage.objects.filter(created_at__gte=last_hour).count(),
            'pending_matches': Correspondance.objects.filter(is_validated=False).count(),
            'timestamp': now.isoformat()
        }
    elif data_type == 'routes':
        # Popular routes for heatmap
        routes = Voyage.objects.values('ville_depart', 'ville_arrivee').annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        
        data = {
            'routes': list(routes)
        }
    else:
        data = {'error': 'Invalid data type'}
    
    return JsonResponse(data)