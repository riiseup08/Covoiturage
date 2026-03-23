"""
Simple in-memory rate limiting middleware for critical endpoints.
No external dependency required. Uses Django's cache framework.

For production with multiple workers, switch to Redis-backed cache.
"""
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
import time


# Rate limit rules: path_prefix -> (max_requests, window_seconds)
RATE_LIMITS = {
    '/accounts/phone/login/': (5, 300),       # 5 requests per 5 min
    '/accounts/phone/register/': (5, 300),     # 5 requests per 5 min
    '/accounts/phone/verify/': (10, 300),      # 10 attempts per 5 min
    '/accounts/phone/resend/': (3, 600),       # 3 resends per 10 min
    '/accounts/login/': (10, 300),             # 10 login attempts per 5 min
    '/accounts/register/': (5, 300),           # 5 registrations per 5 min
    '/accounts/password_reset/': (3, 600),     # 3 resets per 10 min
    '/geo/forward/': (30, 60),                 # 30 geocode per min
    '/geo/reverse/': (30, 60),                 # 30 reverse per min
}


def _get_client_ip(request):
    """Extract client IP from request, handling proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


class RateLimitMiddleware:
    """Rate limit specific endpoints by client IP using Django cache."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only rate limit POST requests (and GET for geocoding)
        for path_prefix, (max_requests, window) in RATE_LIMITS.items():
            if request.path.startswith(path_prefix):
                if request.method == 'POST' or path_prefix.startswith('/geo/'):
                    ip = _get_client_ip(request)
                    cache_key = f"ratelimit:{path_prefix}:{ip}"
                    hit_count = cache.get(cache_key, 0)

                    if hit_count >= max_requests:
                        if request.headers.get('Accept', '').startswith('application/json'):
                            return JsonResponse(
                                {'error': 'Trop de tentatives. Réessayez plus tard.'},
                                status=429
                            )
                        return _rate_limit_html_response(request, window)

                    cache.set(cache_key, hit_count + 1, window)
                break

        return self.get_response(request)


def _rate_limit_html_response(request, wait_seconds):
    """Return an HTML 429 response."""
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    minutes = max(1, wait_seconds // 60)
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trop de tentatives - Covoit.Africa</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{ --color-earth: #D95D39; --color-bg: #FAF6ED; --color-night: #1A1A1A; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ background: var(--color-bg); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }}
        .container {{ text-align: center; max-width: 420px; background: white; padding: 50px 40px; border-radius: 12px; box-shadow: 0 15px 35px rgba(0,0,0,0.05); }}
        .icon {{ font-size: 64px; margin-bottom: 20px; }}
        h1 {{ font-size: 24px; font-weight: 800; margin-bottom: 12px; color: var(--color-night); }}
        p {{ color: #666; font-size: 15px; line-height: 1.6; }}
        a {{ display: inline-block; margin-top: 24px; padding: 14px 28px; background: var(--color-earth); color: white; border-radius: 8px; text-decoration: none; font-weight: 700; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">&#9203;</div>
        <h1>Trop de tentatives</h1>
        <p>Pour prot&eacute;ger votre compte, veuillez patienter <strong>{minutes} minute(s)</strong> avant de r&eacute;essayer.</p>
        <a href="/">Retour &agrave; l'accueil</a>
    </div>
</body>
</html>"""
    return HttpResponse(html, status=429, content_type='text/html')
