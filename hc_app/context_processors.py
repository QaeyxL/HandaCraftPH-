from hc_app.models import CartItem, UserProfile
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
