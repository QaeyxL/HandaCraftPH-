from hc_app.models import CartItem, UserProfile, Product
from .models import Category   # edit22 - added
from .utils import get_unique_categories

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
    # Use de-duplicated categories to avoid repeated names in menus
    return {"categories": get_unique_categories()}


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
                # Primary signal: explicit flag on the profile
                if profile and getattr(profile, 'is_seller', False):
                    is_seller = True
                else:
                    # Fallback: treat users who own products as sellers (helps deployments where flag wasn't set)
                    try:
                        is_seller = Product.objects.filter(seller=request.user).exists()
                    except Exception:
                        # If product lookup fails for any reason, keep conservative default
                        is_seller = False
        except Exception:
            is_seller = False
    return {'is_seller': is_seller}
