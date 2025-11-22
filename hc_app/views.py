from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
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

    return render(request, 'hc_app/catalog.html', {
        'products': products,
        'categories': categories,
        'active_category': category or ''
    })

def product_detail(request, pk):
    product = Product.objects.get(id=pk)
    return render(request, 'hc_app/product_detail.html', {'product': product})

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
    categories = Category.objects.all()
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
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
        count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({'count': count})

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
    user_products = Product.objects.filter(seller=request.user)   # edit22 - add (4)
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
def search_view(request):   # edit22 - added
    q = request.GET.get('q', '').strip()
    results = Product.objects.none()
    if q:
        results = Product.objects.filter(name__icontains=q) | Product.objects.filter(description__icontains=q)
    return render(request, 'hc_app/search_results.html', {
        'query': q,
        'results': results
    })

