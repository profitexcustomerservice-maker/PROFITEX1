from django.core.cache import cache
from .models import SocialLink

SOCIAL_LINK_CACHE_TIMEOUT = 300


def social_links(request):
    """Add social links to template context."""
    cache_key = 'social_links_active'
    links = cache.get(cache_key)
    if links is None:
        links = list(SocialLink.objects.filter(is_active=True).order_by('order', 'name'))
        cache.set(cache_key, links, SOCIAL_LINK_CACHE_TIMEOUT)
    return {
        'social_links': links
    }