from hc_app.models import CartItem, UserProfile, Product
from .models import Category   # edit22 - added

def cart_item_count(request):
    if request.user.is_authenticated:
        return {'cart_count': CartItem.objects.filter(user=request.user).count()}
    return {'cart_count': 0}

def user_profile(request):
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        return {'user_profile': profile}
    return {'user_profile': None}

def categories_processor(request):   # edit22 - added
    return {"categories": Category.objects.all()}


def is_seller_processor(request):
    """Adds `is_seller` to template context for showing seller-only UI.

    A user is considered a seller if they are staff or they have at least one Product.
    """
    is_seller = False
    if request.user.is_authenticated:
        try:
            if request.user.is_staff:
                is_seller = True
            else:
                profile = UserProfile.objects.filter(user=request.user).first()
                is_seller = bool(profile and getattr(profile, 'is_seller', False))
        except Exception:
            is_seller = False
    return {'is_seller': is_seller}
