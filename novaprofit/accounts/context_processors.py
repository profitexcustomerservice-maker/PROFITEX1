from .models import SocialLink

def social_links(request):
    """
    Context processor to make social links available in all templates.
    This allows the footer to display social links dynamically.
    """
    return {
        'social_links': SocialLink.objects.filter(is_active=True)
    }
