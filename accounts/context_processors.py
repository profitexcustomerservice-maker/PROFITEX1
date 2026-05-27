from .models import SocialLink

def social_links(request):
    """Add social links to template context"""
    return {
        'social_links': SocialLink.objects.filter(is_active=True).order_by('order', 'name')
    }