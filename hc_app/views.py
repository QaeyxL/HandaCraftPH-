from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from twilio.rest import Client
from django.contrib.auth.models import User  # edit22 - added
from .forms import RegisterForm, ProductForm, CheckoutForm, BuyerAddressForm
import requests, easypost
from .models import Quote  # edit22 - added
from random import choice
from .models import Product, Category, CartItem, ProductImage, Order, OrderItem, UserProfile
from django.http import JsonResponse
from decimal import Decimal
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from decouple import config  # edit22 - added 
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login

#twilio whatsapp message code template
def send_whatsapp_message(to_number, message_body):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    #number validation from twilio docs should start with +63 not 0
    if not to_number.startswith('+'):
        to_number = '+63' + to_number.lstrip('0')
    client.messages.create(
        #whatsapp/twilio api key +14155238886
        from_='whatsapp:+14155238886',
        to=f'whatsapp:{to_number}',
        body=message_body
    )

# edit22 - add
@login_required  
def message_user(request, user_id):
    recipient_profile = get_object_or_404(UserProfile, user__id=user_id)
    if request.method == "POST":
        body = request.POST.get("message")
        try:
            send_whatsapp_message(recipient_profile.contact_number, body)
            messages.success(request, f"Message sent to {recipient_profile.user.username}")
        except Exception as e:
            messages.error(request, f"Failed to send message: {e}")
    return redirect("hc_app:dashboard")

#Retrieve backup quotes when random quotes from API are unretrievable
def get_random_quote():
    backup_quotes = [
        {"content": "Keep going. You’re closer than you think.", "author": "Unknown"},
        {"content": "Small steps every day.", "author": "Unknown"},
        {"content": "Start where you are. Use what you have. Do what you can.", "author": "Arthur Ashe"},
        {"content": "It always seems impossible until it’s done.", "author": "Nelson Mandela"},
    ]
    try:
        #1. retrieve quote from api
        r = requests.get("https://api.quotable.io/random", timeout=3)
        r.raise_for_status()
        #2. store retrieved quotes in json format
        data = r.json()
        #3. iterate over quote content in JSON form and return content and author
        if "content" in data and "author" in data:
            return {"content": data["content"], "author": data["author"]}
    except Exception:
        pass
    #4 if everything else fails retrieve from backup quotes
    return choice(backup_quotes)

# --Registration code logic--
def register_view(request):
    #call quote api function
    quote = get_random_quote()
    '''
    to add:
    password validation: 1. at least 8 characters long 2. One capital letter
    Email: 1. Cannot reuse previously registered email (no duplicates)
    Contact no: 1. cannot reuse previously registered contact no (no duplicates)
    '''
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            #Email notif via django smtp after reg
            try:
                send_mail(
                    'Registration Successful',
                    f'Hi {user.username}, you have successfully registered!',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

            # Twilio-whatsapp notif after reg
            contact_number = form.cleaned_data.get('contact_number')
            #Twilio api will utilize contact_number from field to send a message
            if contact_number:
                try:
                    send_whatsapp_message(
                        contact_number,
                        #registration notif and contact number confirmation
                        f'Hi {user.username}, your registration was successful!'
                    )
                except Exception as e:
                    messages.warning(request, f'WhatsApp message failed: {e}')

            messages.success(request, 'Registration successful! You can now log in.')
            #if redirect-- hc_app:<page_name>
            return redirect('hc_app:login')   
    else:
        form = RegisterForm()
        #if render (hc_app/<appname.html>)
    return render(request, 'hc_app/register.html', {'form': form, 'quote': quote})

# -- Login logic code --
def login_view(request):
     #call quote api function
    quote = get_random_quote()
    #login validation
    if request.method == 'POST':
        #validate and retrieve credentials
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome, {username}!')
                return redirect('hc_app:home')   
        messages.error(request, 'Invalid credentials')
    else:
        form = AuthenticationForm()
    return render(request, 'hc_app/login.html', {'form': form, 'quote': quote})

# --- Home view ---
@login_required
def home_view(request):
    return render(request, 'hc_app/home.html')

@login_required
def sell(request):
    success = False
    if request.method == 'POST':
        print(request.FILES)
        form = ProductForm(request.POST, request.FILES)
        images = request.FILES.getlist('images')

        if form.is_valid() and images:
            product = form.save(commit=False)
            product.seller = request.user
            product.save()

            for image in request.FILES.getlist('images'):
                ProductImage.objects.create(product=product, image=image)

            success = True
            form = ProductForm()

    else:
        form = ProductForm()

    user_products = Product.objects.filter(seller=request.user)
    return render(request,'hc_app/sell.html',
        {'form': form, 
         'success': success, 
         'user_products': user_products}
    )

# edit22 - remove def catalog(request):
    products = Product.objects.all()
    return render(request, 'hc_app/catalog.html', {'products': products})

def catalog(request):   # edit22 - edited
    products = Product.objects.all()
    category = request.GET.get("category")
    if category:
        products = products.filter(category__name=category)

    # Provide categories to populate the filter dropdown
    categories = Category.objects.all()

    # Sorting support
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    return render(request, 'hc_app/catalog.html', {
        'products': products,
        'categories': categories,
        'active_category': category or ''
    })

def product_detail(request, pk):
    product = Product.objects.get(id=pk)
    # related products: same category, exclude current
    related = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'hc_app/product_detail.html', {'product': product, 'related_products': related})

def edit_product(request, pk):
    product = Product.objects.get(id=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('catalog')
    else:
        form = ProductForm(instance=product)
    return render(request, 'hc_app/edit_product.html', {'form': form})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    
    if request.method == 'POST':
        product.delete()
        return redirect('hc_app:sell') 

    return redirect('hc_app:sell')

def category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'hc_app/category_products.html', {'category': category, 'products': products})

def categories_list(request):   # edit22 - added
    # Prefetch products for each category to show previews
    categories = Category.objects.prefetch_related('product_set').all()
    return render(request, "hc_app/categories.html", {"categories": categories})

def home_view(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, 'hc_app/home.html', {
        'categories': categories,
        'products': products
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Support quantity parameter (from normal form POST or AJAX). Default to 1.
    try:
        qty = int(request.POST.get('quantity', 1))
    except Exception:
        qty = 1

    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if created:
        cart_item.quantity = max(1, qty)
    else:
        cart_item.quantity = cart_item.quantity + max(1, qty)
    cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
        count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({'count': count, 'item_quantity': cart_item.quantity})

    return redirect('hc_app:cart_view')

def category_products(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    products = Product.objects.filter(category=category)
    return render(
        request,
        'hc_app/category_products.html',
        {'products': products, 'category': category}
    )


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.seller != request.user:
        return redirect('hc_app:home') 

    product.delete()
    return redirect('hc_app:sell') 

@login_required
def my_listings(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, 'hc_app/my_listings.html', {'products': products})

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)

    total = 0
    for item in cart_items:
        total += item.product.price * item.quantity 

    return render(request, 'hc_app/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def update_cart(request, item_id):
    """Increase or decrease quantity of a cart item"""
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete() 
    return redirect('hc_app:cart_view')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    return redirect('hc_app:cart_view')


easypost.api_key = settings.EASYPOST_API_KEY

@login_required
def checkout_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    seller_totals = {}
    shipping_flat_rate = 100

    for item in cart_items:
        seller = item.product.seller
        if seller.id not in seller_totals:
            seller_totals[seller.id] = {
                "seller": seller,
                "items": [],
                "subtotal": 0,
                "shipping": shipping_flat_rate,
                "estimated_delivery": datetime.now().date() + timedelta(days=5),
            }
        seller_totals[seller.id]["items"].append(item)
        seller_totals[seller.id]["subtotal"] += item.product.price * item.quantity

    total_amount = sum(data["subtotal"] + data["shipping"] for data in seller_totals.values())
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST" and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = BuyerAddressForm(request.POST, instance=profile)
        payment_method = request.POST.get("payment_method", "Cash on Delivery")

        if form.is_valid():
            profile.save()
            for data in seller_totals.values():
                order = Order.objects.create(
                    buyer=request.user,
                    seller=data["seller"],
                    total=data["subtotal"] + data["shipping"],
                    shipping_cost=data["shipping"],
                    payment_method=payment_method,
                    status="Pending"
                )
                for item in data["items"]:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        subtotal=item.product.price * item.quantity
                    )
            cart_items.delete()
            return redirect("hc_app:order_confirmation")
        else:
            messages.error(request, "Please fill out all required fields.")
    else:
        form = BuyerAddressForm(instance=profile)

    return render(request, "hc_app/checkout.html", {
        "cart_items": cart_items,
        "seller_totals": seller_totals,
        "total_amount": total_amount,
        "form": form,
    })

@login_required
@csrf_exempt
def address_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []

    if query:
        try:
            results = easypost.Address.create(
                verify_strict=False,
                street1=query,
                city='',
                state='',
                zip='',
                country='US'
            )
            if hasattr(results, 'street1'):
                suggestions.append({
                    "street1": results.street1,
                    "city": results.city,
                    "state": results.state,
                    "zip_code": results.zip,
                    "country": results.country
                })
        except Exception as e:
            print("EasyPost error:", e)

    return JsonResponse({"suggestions": suggestions})

@login_required
def address_autocomplete(request):
    query = request.GET.get("q", "")
    if not query:
        return JsonResponse([], safe=False)

    try:
        addresses = easypost.Address.create(
            verify=["delivery"],
            street1=query,
            city="",
            state="",
            zip="",
            country="PH" 
        )
        suggestions = []
        for addr in addresses if isinstance(addresses, list) else [addresses]:
            suggestions.append({
                "street": addr.street1,
                "city": addr.city,
                "state": addr.state,
                "zip_code": addr.zip,
                "country": addr.country,
            })
        return JsonResponse(suggestions, safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)

@login_required
def dashboard_view(request):
    # Only allow store owners (UserProfile.is_seller) or staff to access this view
    profile = UserProfile.objects.filter(user=request.user).first()
    if not (request.user.is_staff or (profile and getattr(profile, 'is_seller', False))):
        messages.error(request, "Access denied: dashboard is for store owners only.")
        return redirect('hc_app:home')

    user_products = Product.objects.filter(seller=request.user)
    recent_orders = Order.objects.filter(seller=request.user).order_by('-created_at')[:10]    
    total_orders = Order.objects.filter(seller=request.user).count()
    total_customers = Order.objects.filter(seller=request.user).values('buyer').distinct().count()
    # dummy stats
    context = {
        "total_customers": total_customers,
        "total_orders": total_orders,
        "monthly_sales": [],
        "recent_orders": recent_orders,
        "user_products": user_products,   # edit22 - edited "user_products": request.user.products.all()
        "users": User.objects.exclude(id=request.user.id),   # edit22 - added
        "recent_quotes": Quote.objects.filter(seller=request.user).order_by("-created_at")[:20],  # edit22 - added
        }
    return render(request, "hc_app/dashboard.html", context)   # edit22 - add context


@login_required
def dashboard_stats(request):
    """Return basic dashboard stats for the logged-in seller as JSON.

    Response shape: { customersTotal: int, ordersCount: int }
    """
    total_orders = Order.objects.filter(seller=request.user).count()
    total_customers = Order.objects.filter(seller=request.user).values('buyer').distinct().count()
    return JsonResponse({
        'customersTotal': total_customers,
        'ordersCount': total_orders,
    })


@login_required
def dashboard_quotes(request, buyer_id):
    """Return quotes/messages sent by a given buyer to the logged-in seller."""
    qs = Quote.objects.filter(seller=request.user, buyer__id=buyer_id).order_by('-created_at')
    data = []
    for q in qs:
        data.append({
            'id': q.id,
            'buyer_username': q.buyer.username,
            'message': q.message,
            'product_id': q.product.id if q.product else None,
            'product_name': q.product.name if q.product else None,
            'created_at': q.created_at.isoformat(),
        })
    return JsonResponse({'quotes': data})


def _create_demo_user(username, password, email='', is_staff=False, is_superuser=False):
    UserModel = get_user_model()
    user, created = UserModel.objects.get_or_create(username=username, defaults={'email': email})
    if created:
        user.set_password(password)
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
    else:
        # ensure password and flags are up to date for demo
        user.set_password(password)
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
    return user


def demo_setup(request):
    """DEBUG-only: create demo admin, demo seller, products, orders and quotes.

    GET: render a simple confirmation page with next-step links.
    POST: (also supported) will (re)create demo data.
    """
    if not settings.DEBUG:
        return JsonResponse({'error': 'Demo only available in DEBUG mode.'}, status=403)

    # create demo users
    admin = _create_demo_user('demo_admin', 'demopass123', email='admin@example.com', is_staff=True, is_superuser=True)
    seller = _create_demo_user('demo_seller', 'sellerpass', email='seller@example.com')
    buyer = _create_demo_user('demo_buyer', 'buyerpass', email='buyer@example.com')

    # ensure profiles exist and mark seller as a store owner
    try:
        UserProfile.objects.get_or_create(user=seller, defaults={
            'contact_number': '+639171234567', 'street': 'Demo St', 'city': 'Manila', 'state': 'NCR', 'zip_code': '1000', 'is_seller': True
        })
        # also ensure buyer profile exists
        UserProfile.objects.get_or_create(user=buyer, defaults={
            'contact_number': '+639170000000', 'street': 'Buyer St', 'city': 'Manila', 'state': 'NCR', 'zip_code': '1001', 'is_seller': False
        })
    except Exception:
        pass

    # create category
    cat, _ = Category.objects.get_or_create(name='Demo Category')

    # create products
    prod1, _ = Product.objects.get_or_create(name='Demo Product 1', seller=seller, defaults={'price': 199.99, 'category': cat, 'description': 'Sample product', 'weight': 1})
    prod2, _ = Product.objects.get_or_create(name='Demo Product 2', seller=seller, defaults={'price': 299.99, 'category': cat, 'description': 'Sample product 2', 'weight': 2})

    # create an order from buyer to seller
    order, _ = Order.objects.get_or_create(buyer=buyer, seller=seller, defaults={'total': prod1.price, 'shipping_cost': 50, 'payment_method': 'COD', 'status': 'Pending'})
    # Ensure there is at least one order item
    OrderItem.objects.get_or_create(order=order, product=prod1, defaults={'quantity': 1, 'subtotal': prod1.price})

    # create a sample quote from buyer to seller
    Quote.objects.get_or_create(seller=seller, buyer=buyer, product=prod1, defaults={'message': 'Is this available?',})

    # Auto-login the demo seller and redirect to seller dashboard
    try:
        seller.backend = 'django.contrib.auth.backends.ModelBackend'
        auth_login(request, seller)
        messages.success(request, 'Demo seller logged in. Redirecting to dashboard...')
        return redirect('hc_app:dashboard')
    except Exception:
        # Fallback: render the demo info page if auto-login fails
        return render(request, 'hc_app/demo_setup.html', {
            'admin_username': 'demo_admin',
            'admin_password': 'demopass123',
            'seller_username': 'demo_seller',
            'seller_password': 'sellerpass',
            'buyer_username': 'demo_buyer',
            'buyer_password': 'buyerpass',
        })


def demo_login_admin(request):
    """Debug-only: log in the demo admin and redirect to admin index or seller dashboard.
    """
    if not settings.DEBUG:
        return JsonResponse({'error': 'Demo only available in DEBUG mode.'}, status=403)

    UserModel = get_user_model()
    try:
        admin = UserModel.objects.get(username='demo_admin')
    except UserModel.DoesNotExist:
        return redirect('hc_app:demo_setup')

    # Force-login admin
    admin.backend = 'django.contrib.auth.backends.ModelBackend'
    auth_login(request, admin)

    # Redirect to Django admin site by default (admin index)
    return redirect('/admin/')


@login_required
def delete_account(request):
    """Allow seller to delete their account (confirmation required).

    Only users with UserProfile.is_seller True or staff may delete via this path.
    """
    profile = UserProfile.objects.filter(user=request.user).first()
    # Only allow if store owner or staff
    if not (request.user.is_staff or (profile and getattr(profile, 'is_seller', False))):
        messages.error(request, "You don't have permission to delete this account.")
        return redirect('hc_app:home')

    # Show confirmation page and on POST send an email with a signed delete link.
    if request.method == 'POST':
        user = request.user
        payload = {'user_id': user.id}
        token = signing.dumps(payload)
        confirm_url = request.build_absolute_uri(
            reverse('hc_app:delete_confirm_account', args=[token])
        )

        # Try to send email; if not configured, render link on page as fallback
        email_sent = False
        try:
            send_mail(
                subject='Confirm account deletion',
                message=f'Click this link to permanently delete your account: {confirm_url}',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[user.email],
                fail_silently=False,
            )
            email_sent = True
        except Exception:
            email_sent = False

        return render(request, 'hc_app/delete_request_sent.html', {
            'email_sent': email_sent,
            'confirm_url': confirm_url,
        })

    return render(request, 'hc_app/confirm_delete_account.html')


@login_required
def delete_confirm_account(request, token):
    """Confirm deletion via signed token. Token expires after a reasonable time using max_age when loading.

    For safety, we verify the token and then delete the user.
    """
    try:
        data = signing.loads(token, max_age=60*60*24)  # 24 hours
        user_id = data.get('user_id')
    except signing.BadSignature:
        messages.error(request, 'Invalid or expired deletion link.')
        return redirect('hc_app:home')
    except signing.SignatureExpired:
        messages.error(request, 'Deletion link expired. Please request a new link.')
        return redirect('hc_app:home')

    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('hc_app:home')

    # Only allow deletion if the token user matches the currently logged-in user OR if token belongs to a user and current user is that same user (we'll log them out first)
    # If the request comes from a different session, we still allow deletion via token.
    try:
        # Log out current session if any
        auth_logout(request)
    except Exception:
        pass

    try:
        # Soft-archive instead of hard delete: mark user inactive and set profile archive fields
        user.is_active = False
        user.save()
        profile = UserProfile.objects.filter(user=user).first()
        if profile:
            profile.is_seller = False
            profile.is_archived = True
            profile.archived_at = timezone.now()
            profile.save()

        # record audit log
        try:
            from .models import AuditLog
            AuditLog.objects.create(
                target_user=user,
                action='archive',
                performed_by=None,
                details='Account archived via email confirmation link.'
            )
        except Exception:
            pass

        messages.success(request, 'Account archived (soft-deleted) successfully.')
    except Exception as e:
        messages.error(request, f'Failed to delete account: {e}')

    return render(request, 'hc_app/delete_confirmed.html')


@login_required
def deactivate_account(request):
    """Soft-deactivate seller account: sets is_active=False and clears is_seller.

    A deactivated user cannot log in until reactivated by admin.
    """
    profile = UserProfile.objects.filter(user=request.user).first()
    if not (request.user.is_staff or (profile and getattr(profile, 'is_seller', False))):
        messages.error(request, "You don't have permission to deactivate this account.")
        return redirect('hc_app:home')

    if request.method == 'POST':
        try:
            # mark user inactive and set profile.is_seller False (deactivation)
            request.user.is_active = False
            request.user.save()
            if profile:
                old_seller = profile.is_seller
                profile.is_seller = False
                profile.save()

            # audit log
            try:
                from .models import AuditLog
                AuditLog.objects.create(
                    target_user=request.user,
                    action='deactivate',
                    performed_by=request.user,
                    details='User initiated deactivation via account settings.'
                )
            except Exception:
                pass

            auth_logout(request)
            messages.success(request, 'Your account has been deactivated. Contact admin to reactivate.')
        except Exception as e:
            messages.error(request, f'Failed to deactivate account: {e}')
        return redirect('hc_app:home')

    return render(request, 'hc_app/confirm_deactivate_account.html')



@login_required
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('hc_app:cart_view')

    seller_orders = {}  
    shipping_flat_rate = 100  

    for item in cart_items:
        seller = item.product.seller
        if seller.id not in seller_orders:
            seller_orders[seller.id] = {
                "seller": seller,
                "items": [],
                "total": 0,
                "shipping_cost": shipping_flat_rate,
                "seller_address": getattr(getattr(seller, 'userprofile', None), 'contact_number', 'No address'),
            }

        subtotal = item.product.price * item.quantity
        seller_orders[seller.id]["items"].append({
            "product": item.product,
            "quantity": item.quantity,
            "subtotal": subtotal,
        })
        seller_orders[seller.id]["total"] += subtotal

    orders_list = []
    grand_total = 0

    for data in seller_orders.values():
        order = Order.objects.create(
            buyer=request.user,
            seller=data["seller"],
            total=data["total"],
            shipping_cost=data["shipping_cost"],
            payment_method="Mock Payment",
            status="Pending"
        )

        # Save each item
        for item in data["items"]:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                subtotal=item["subtotal"]
            )

        order.estimated_delivery = datetime.now().date() + timedelta(days=5)
        order.seller_address = data["seller_address"]
        orders_list.append(order)

        grand_total += data["total"] + data["shipping_cost"]

    cart_items.delete()

    context = {
        "orders": orders_list,
        "grand_total": grand_total,
    }

    return render(request, "hc_app/order_confirmation.html", context)

@login_required
def my_orders_view(request):
    orders = Order.objects.filter(buyer=request.user).order_by("-created_at")

    return render(request, "hc_app/my_orders.html", {
        "orders": orders
    })

@login_required     # edit22 - added
def send_quote(request, seller_id, product_id=None):
    seller = get_object_or_404(User, id=seller_id)
    product = Product.objects.filter(id=product_id).first() if product_id else None

    if request.method == "POST":
        msg = request.POST.get("message", "").strip()
        if msg:
            from .models import Quote
            Quote.objects.create(
                seller=seller,
                buyer=request.user,
                product=product,
                message=msg
            )
            messages.success(request, "Quote sent successfully.")
        else:
            messages.error(request, "Message cannot be empty.")

    # Redirect back to product detail if product_id was given
    if product_id:
        return redirect("hc_app:product_detail", pk=product_id)
    return redirect("hc_app:home")

@login_required
def order_confirmation_view(request):
    latest_order = (
        request.user.orders.all()
        .order_by("-created_at")
        .prefetch_related("items")
        .first()
    )

    if not latest_order:
        return render(request, "hc_app/order_confirmation.html", {
            "order": None,
            "message": "No recent order found.",
        })

    return render(request, "hc_app/order_confirmation.html", {
        "order": latest_order,
        "order_items": latest_order.items.all(),
    })

@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    if request.method == "POST":
        if order.status in ["Pending", "Processing"]:
            order.delete()
            messages.success(request, "Order deleted successfully.")
        else:
            messages.error(request, "You can only delete pending or processing orders.")
        return redirect('hc_app:orders')  
    return redirect('hc_app:orders')

@login_required
def update_order_status(request, order_id):    # edit22 - added
    order = get_object_or_404(Order, id=order_id, seller=request.user)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]:
            order.status = new_status
            order.save()
            messages.success(request, "Order status updated.")
        else:
            messages.error(request, "Invalid status.")
    return redirect("hc_app:dashboard")    # dashboard or orders?

@login_required
def search_view(request):   # edit22 - added
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    results = Product.objects.none()
    if q:
        results = Product.objects.filter(name__icontains=q) | Product.objects.filter(description__icontains=q)
    else:
        results = Product.objects.all()

    if category:
        results = results.filter(category__name=category)

    return render(request, 'hc_app/search_results.html', {
        'query': q,
        'results': results,
        'categories': Category.objects.all(),
        'active_category': category,
    })

