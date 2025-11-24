from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from twilio.rest import Client
from django.contrib.auth.models import User  # edit22 - added
from .forms import RegisterForm, ProductForm, CheckoutForm, BuyerAddressForm
import requests, easypost
from easypost import EasyPostClient
from random import choice
from .models import Product, Category, CartItem, ProductImage, Order, OrderItem, UserProfile, Quote
from django.db.models import Q, Sum
from django.http import JsonResponse
from decimal import Decimal
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from decouple import config  # edit22 - added 
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.contrib.auth import login as auth_login
from django.db import DatabaseError
from django.db.utils import ProgrammingError
from .models import SellerWorkflowTask
from .forms import SellerWorkflowForm
from django.views.decorators.http import require_POST
from .models import Attribute, AttributeOption, ProductAttribute
from decimal import Decimal as D
import json
from django.views.decorators.http import require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count

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

# home_view is defined later with categories/products context — keep the consolidated version below

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
            product.seller_street = request.POST.get('street1')
            product.seller_city = request.POST.get('city')
            product.seller_state = request.POST.get('state')
            product.seller_zip_code = request.POST.get('zip')
            product.seller_country = request.POST.get('country', 'PH')
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

# catalog is implemented below as `catalog(request)` (edited by edit22)

def catalog(request):   # edit22 - edited
    products = Product.objects.all()
    category = request.GET.get("category")
    if category:
        try:
            cat_id = int(category)
            products = products.filter(category_id=cat_id)
        except (ValueError, TypeError):
            products = products.filter(Q(category__slug__iexact=category) | Q(category__name__iexact=category))

    # Provide categories to populate the filter dropdown (deduplicated)
    from .utils import get_unique_categories
    categories = get_unique_categories()

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


def customize_view(request):
    """Landing page for customization. Lists products that can be customized (have ProductAttribute entries)."""
    products = Product.objects.filter(product_attributes__isnull=False).distinct().order_by('-created_at')[:60]
    return render(request, 'hc_app/customize.html', {'products': products})


@require_GET
def product_attributes_api(request, pk):
    """Return attributes and options for a product as JSON."""
    product = get_object_or_404(Product, id=pk)
    attrs = []
    for pa in product.product_attributes.select_related('attribute').all():
        attr = pa.attribute
        options = []
        for opt in attr.options.all():
            options.append({
                'id': opt.id,
                'value': opt.value,
                'price_modifier': str(opt.price_modifier),
                'modifier_type': opt.modifier_type,
                'extra': opt.extra or {},
            })
        attrs.append({
            'id': attr.id,
            'name': attr.name,
            'slug': attr.slug,
            'type': attr.type,
            'required': pa.required,
            'options': options,
        })
    return JsonResponse({'attributes': attrs})


@require_POST
def calculate_custom_price(request):
    """Accepts JSON payload with product_id and selected option ids to compute custom price.

    POST body: {'product_id': 1, 'selected_options': [opt_id,...], 'size_value': optional}
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST.dict() if request.POST else {}

    product_id = payload.get('product_id') or request.POST.get('product_id')
    selected = payload.get('selected_options') or request.POST.getlist('selected_options')
    size_value = payload.get('size_value') or request.POST.get('size_value')

    product = get_object_or_404(Product, id=product_id)
    base = D(str(product.price))
    add_sum = D('0')
    mul_factor = D('1')

    if selected:
        # selected may be list of strings
        for s in selected:
            try:
                opt = AttributeOption.objects.get(id=int(s))
            except Exception:
                continue
            pm = D(str(opt.price_modifier or 0))
            if opt.modifier_type == 'add':
                add_sum += pm
            else:
                # multiplicative factor stored as multiplier (e.g., 1.10 for +10%)
                mul_factor *= pm

    # size_value handling: if numeric and product has size-based pricing rules, add simple proportional logic
    if size_value:
        try:
            sv = D(str(size_value))
            # naive size pricing: price increases linearly (developer can replace with rules)
            # e.g., if size_value represents area multiplier
            add_sum += (sv - D('1')) * base
        except Exception:
            pass

    final = (base + add_sum) * mul_factor
    return JsonResponse({'base': str(base), 'final': str(final)})


def compute_custom_price_for_product(product, selected_option_ids=None, size_value=None):
    """Helper: compute final price Decimal for a product given selected option ids (list) and optional numeric size_value."""
    base = D(str(product.price))
    add_sum = D('0')
    mul_factor = D('1')
    if selected_option_ids:
        for s in selected_option_ids:
            try:
                opt = AttributeOption.objects.get(id=int(s))
            except Exception:
                continue
            pm = D(str(opt.price_modifier or 0))
            if opt.modifier_type == 'add':
                add_sum += pm
            else:
                mul_factor *= pm

    if size_value:
        try:
            sv = D(str(size_value))
            add_sum += (sv - D('1')) * base
        except Exception:
            pass

    final = (base + add_sum) * mul_factor
    return final

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

# delete_product is implemented later with permission checks; earlier duplicate removed

def category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    # Some deployments contain duplicate Category rows with the same name but
    # different ids. To ensure products linked to any duplicate category are
    # included, match by the category name (case-insensitive) as well as the
    # chosen Category instance.
    products = Product.objects.filter(category__name__iexact=category.name)
    return render(request, 'hc_app/category_products.html', {'category': category, 'products': products})

def categories_list(request):   # edit22 - added
    # Prefetch products for each category to show previews. Use unique categories helper
    from .utils import get_unique_categories
    categories = get_unique_categories()
    # prefetch products for the selected category ids to avoid N+1 when templates access products
    # build mapping by id
    prefetch_qs = Category.objects.filter(id__in=[c.id for c in categories]).prefetch_related('product_set')
    cat_map = {c.id: c for c in prefetch_qs}
    ordered = [cat_map[c.id] for c in categories if c.id in cat_map]
    return render(request, "hc_app/categories.html", {"categories": ordered})

def home_view(request):
    from .utils import get_unique_categories
    categories = get_unique_categories()
    # show recent products as featured crafts (most recently created first)
    featured_products = Product.objects.order_by('-created_at')[:8]
    return render(request, 'hc_app/home.html', {
        'categories': categories,
        'featured_products': featured_products
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Accept optional customization JSON (from product page customizer)
    customization = None
    item_price = None
    if request.method == 'POST':
        # customization may be sent as JSON string in POST or via AJAX body
        try:
            if request.POST.get('customization'):
                customization = json.loads(request.POST.get('customization'))
        except Exception:
            customization = None

    # If customization provided, try to match existing cart item for same user/product/customization
    if customization:
        # look for cart items with identical customization
        existing = CartItem.objects.filter(user=request.user, product=product)
        matched = None
        for it in existing:
            try:
                if it.customization == customization:
                    matched = it
                    break
            except Exception:
                continue
        if matched:
            cart_item = matched
            cart_item.quantity += 1
            cart_item.save()
        else:
            # compute item_price using helper
            selected = []
            size_value = None
            # gather selected option ids if present
            for v in (customization.values() if isinstance(customization, dict) else []):
                if isinstance(v, list):
                    selected.extend(v)
                else:
                    try:
                        # maybe numeric
                        size_value = v
                    except Exception:
                        pass
            try:
                item_price = compute_custom_price_for_product(product, selected_option_ids=selected, size_value=size_value)
            except Exception:
                item_price = product.price
            cart_item = CartItem.objects.create(user=request.user, product=product, quantity=1, customization=customization, item_price=item_price)
    else:
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product, customization__isnull=True)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({'count': count, 'item_quantity': cart_item.quantity, 'item_price': float(cart_item.item_price) if cart_item.item_price else float(product.price)})

    return redirect('hc_app:cart_view')

def category_products(request, category_name):
    # Accept either slug or name for category lookup to be tolerant of URL format.
    # Be defensive if duplicate Category rows exist (same name) — prefer slug, otherwise
    # pick the first matching Category to avoid MultipleObjectsReturned.
    category = Category.objects.filter(slug__iexact=category_name).first()
    if not category:
        qs = Category.objects.filter(name__iexact=category_name).order_by('id')
        if not qs.exists():
            # no category found by slug or name
            raise Http404("Category not found")
        # if multiple categories share the same name, pick the one with the lowest id
        category = qs.first()
        # If the chosen category has a slug, redirect to the canonical slug URL to
        # normalize links and avoid repeat lookups in the future.
        if category.slug:
            # Only redirect to canonical slug when configured to do so
            from django.conf import settings
            if getattr(settings, 'CANONICALIZE_CATEGORY_SLUGS', True):
                return redirect('hc_app:category_products', category_name=category.slug)

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
        unit = item.item_price if (item.item_price is not None) else item.product.price
        total += unit * item.quantity 

    return render(request, 'hc_app/cart.html', {
        'cart_items': cart_items,
        'total': total
    })


@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        
        if action == 'increase':
            if hasattr(cart_item.product, 'stock') and cart_item.product.stock <= cart_item.quantity:
                return JsonResponse({"error": "Product is out of stock."})
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                cart_total = sum((item.item_price if item.item_price is not None else item.product.price) * item.quantity for item in CartItem.objects.filter(user=request.user)) # recalculate cart total if item deleted
                return JsonResponse({"success": True, "quantity": 0, "cart_total": float(cart_total), "item_subtotal": 0})

        unit_price = cart_item.item_price if cart_item.item_price is not None else cart_item.product.price
        item_subtotal = unit_price * cart_item.quantity
        cart_total = sum((item.item_price if item.item_price is not None else item.product.price) * item.quantity for item in CartItem.objects.filter(user=request.user))

        return JsonResponse({
            "success": True,
            "quantity": cart_item.quantity,
            "item_subtotal": float(item_subtotal),
            "cart_total": float(cart_total)
        })

    return JsonResponse({"error": "Invalid request"})
    return redirect('hc_app:cart_view')



@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    return redirect('hc_app:cart_view')


easypost_client = EasyPostClient(settings.EASYPOST_API_KEY)

@login_required
def checkout_view(request):
    cart_items = CartItem.objects.filter(user=request.user)

    seller_totals = {}
    shipping_flat_rate = Decimal('100.00')
    for item in cart_items:
        seller = item.product.seller
        if seller.id not in seller_totals:
            seller_totals[seller.id] = {
                "seller": seller,
                "items": [],
                "subtotal": Decimal('0'),
                "shipping": shipping_flat_rate,
                "estimated_delivery": datetime.now().date() + timedelta(days=5),
            }
        seller_totals[seller.id]["items"].append(item)
        seller_totals[seller.id]["subtotal"] += item.product.price * item.quantity

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == "POST":
        form = BuyerAddressForm(request.POST, instance=profile)
        
        if is_ajax and "calculate_shipping" in request.POST:
            print("=== AJAX Shipping Calculation ===")
            
            if form.is_valid():
                temp_profile = form.save(commit=False)
                
                for seller_id, data in seller_totals.items():
                    seller_profile, _ = UserProfile.objects.get_or_create(user=data["seller"])
                    to_country = temp_profile.country.strip().lower().replace(" ", "")

                    if to_country in ["philippines", "ph"]:
                        shipping_cost = shipping_flat_rate

                    elif to_country in ["usa", "unitedstates", "unitedstatesofamerica", "us"]:
                        try:
                            to_address = easypost_client.address.create(
                                name=request.user.username,
                                street1=temp_profile.street,
                                city=temp_profile.city,
                                state=temp_profile.state,
                                zip=temp_profile.zip_code,
                                country="US",
                                phone=temp_profile.contact_number
                            )

                            from_address = easypost_client.address.create(
                                name=data["seller"].username,
                                street1=seller_profile.street or "123 Example St",
                                city=seller_profile.city or "City",
                                state=seller_profile.state or "State",
                                zip=seller_profile.zip_code or "0000",
                                country="US",
                                phone=seller_profile.contact_number or "0000000000"
                            )

                            parcel = easypost_client.parcel.create(
                                length=10, width=5, height=5, weight=16
                            )

                            shipment = easypost_client.shipment.create(
                                to_address=to_address,
                                from_address=from_address,
                                parcel=parcel,
                                options={"currency": "USD"}
                            )

                            rates = shipment.rates
                            if rates:
                                lowest_rate = min(float(r.rate) for r in rates)
                                shipping_cost = Decimal(str(round(lowest_rate * 60, 2)))
                            else:
                                shipping_cost = shipping_flat_rate

                        except Exception as e:
                            print(f"EasyPost error: {e}")
                            shipping_cost = shipping_flat_rate
                    else:
                        return JsonResponse({
                            "success": False,
                            "error": f"Delivery to {temp_profile.country} is not supported."
                        })

                    data["shipping"] = shipping_cost
                
                temp_profile.save()
                total_amount = sum(d["subtotal"] + d["shipping"] for d in seller_totals.values())
                
                response_data = {
                    "success": True,
                    "seller_totals": [
                        {"id": str(sid), "shipping": str(d["shipping"])} 
                        for sid, d in seller_totals.items()
                    ],
                    "total_amount": str(total_amount)
                }
                print(f"Returning JSON: {response_data}")
                return JsonResponse(response_data)
            else:
                return JsonResponse({
                    "success": False, 
                    "error": "Please fill out all required fields correctly."
                })
        
        elif "place_order" in request.POST:
            print("=== Place Order ===")
            payment_method = request.POST.get("payment_method", "")

            if not payment_method:
                messages.error(request, "Please select a payment method.")
            elif form.is_valid():
                temp_profile = form.save()

                # Stock check
                stock_error = False
                for data in seller_totals.values():
                    for item in data["items"]:
                        if item.quantity > item.product.stock:
                            messages.error(request, f"Not enough stock for {item.product.name}. Stock: {item.product.stock}")
                            stock_error = True
                            break
                    if stock_error:
                        break

                if not stock_error:
                    # Create orders
                    created_orders = []
                    for seller_id, data in seller_totals.items():
                        order = Order.objects.create(
                            buyer=request.user,
                            seller=data["seller"],
                            total=data["subtotal"] + data["shipping"],
                            shipping_cost=data["shipping"],
                            payment_method=payment_method,
                            status="Pending",
                            estimated_delivery=data["estimated_delivery"],
                            buyer_street=temp_profile.street,
                            buyer_city=temp_profile.city,
                            buyer_state=temp_profile.state,
                            buyer_zip_code=temp_profile.zip_code,
                            buyer_country=temp_profile.country,
                            seller_street=data["items"][0].product.seller_street,
                            seller_city=data["items"][0].product.seller_city,
                            seller_state=data["items"][0].product.seller_state,
                            seller_zip_code=data["items"][0].product.seller_zip_code,
                            seller_country=data["items"][0].product.seller_country
                        )
                        for item in data["items"]:
                            OrderItem.objects.create(
                                order=order,
                                product=item.product,
                                product_name=item.product.name,
                                product_price=item.product.price,
                                quantity=item.quantity,
                                subtotal=item.product.price * item.quantity
                            )
                        created_orders.append(order)

                    cart_items.delete()
                    messages.success(request, "Order placed successfully!")
                    return redirect("hc_app:order_confirmation", order_id=created_orders[0].id)
            else:
                messages.error(request, "Please fill out all required fields.")

    else:
        form = BuyerAddressForm(instance=profile)

    total_amount = sum(data["subtotal"] + data["shipping"] for data in seller_totals.values())

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
                country='PH'
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
    country = request.GET.get("country", "")  # optional: filter by country

    if len(query) < 3:
        return JsonResponse([], safe=False)

    # Build Nominatim API URL
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 5,  # number of suggestions
    }
    if country:
        params["countrycodes"] = country.lower()  # e.g., "ph" or "us"

    response = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers={"User-Agent": "HandacraftPH/1.0"})
    results = response.json()

    suggestions = []
    for r in results:
        addr = r.get("address", {})
        street = addr.get("road") or addr.get("pedestrian") or ""
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        state = addr.get("state") or ""
        zip_code = addr.get("postcode") or ""
        country_name = addr.get("country") or ""

        if street and city:
            suggestions.append({
                "street": street,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "country": country_name
            })

    return JsonResponse(suggestions, safe=False)

@login_required
def dashboard_view(request):
    from .utils import get_unique_categories
    user_products = Product.objects.filter(seller=request.user)   # edit22 - add (4)
    recent_orders = Order.objects.filter(seller=request.user).order_by('-created_at')[:10]    
    total_orders = Order.objects.filter(seller=request.user).count()
    total_customers = Order.objects.filter(seller=request.user).values('buyer').distinct().count()
    statuses = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"] 
    #  dummy stats
    context = {
        "total_customers": total_customers,
        "total_orders": total_orders,
        "monthly_sales": [],
        "recent_orders": recent_orders,
        "user_products": user_products,   # edit22 - edited "user_products": request.user.products.all()
        "users": User.objects.exclude(id=request.user.id),   # edit22 - added
        "recent_quotes": [],
        "statuses": statuses,  # edit22 - added
    "categories": get_unique_categories(),
    }
    # Try to load recent quotes, but don't crash the whole view if the table is missing or DB errors occur.
    try:
        context["recent_quotes"] = Quote.objects.filter(seller=request.user).order_by("-created_at")[:20]
        context["db_ok"] = True
    except (ProgrammingError, DatabaseError) as e:
        # DB might not have the table applied (migrations not run) or other DB issues.
        context["recent_quotes"] = []
        context["db_ok"] = False
        context["db_error_message"] = str(e)
    # Seller workflow tasks
    try:
        context['workflow_tasks'] = SellerWorkflowTask.objects.filter(seller=request.user).order_by('due_date')
    except Exception:
        context['workflow_tasks'] = []
    return render(request, "hc_app/dashboard.html", context)   # edit22 - add context


@login_required
@require_POST
def workflow_create(request):
    form = SellerWorkflowForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.seller = request.user
        task.save()
        messages.success(request, 'Workflow task created.')
    else:
        messages.error(request, 'Failed to create workflow task. Please check the input.')
    return redirect('hc_app:dashboard')


@login_required
def workflow_update(request, task_id):
    task = get_object_or_404(SellerWorkflowTask, id=task_id, seller=request.user)
    if request.method == 'POST':
        form = SellerWorkflowForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Workflow task updated.')
            return redirect('hc_app:dashboard')
    else:
        form = SellerWorkflowForm(instance=task)
    return render(request, 'hc_app/workflow_edit.html', {'form': form, 'task': task})


@login_required
@require_POST
def workflow_delete(request, task_id):
    task = get_object_or_404(SellerWorkflowTask, id=task_id, seller=request.user)
    task.delete()
    messages.success(request, 'Workflow task deleted.')
    return redirect('hc_app:dashboard')


@login_required
def dashboard_stats(request):
    """Return basic dashboard stats for the logged-in seller as JSON.

    Response shape: { customersTotal: int, ordersCount: int }
    """
    # Optional category filter (accept id or slug/name)
    category_param = request.GET.get('category')
    cat_filter = None
    if category_param:
        try:
            cat_filter = int(category_param)
        except Exception:
            # try slug or name
            cat_qs = Category.objects.filter(Q(slug__iexact=category_param) | Q(name__iexact=category_param)).first()
            if cat_qs:
                cat_filter = cat_qs.id

    try:
        total_orders = Order.objects.filter(seller=request.user).count()
        total_customers = Order.objects.filter(seller=request.user).values('buyer').distinct().count()
        in_cart_total = CartItem.objects.filter(product__seller=request.user).count()

        # monthly sales for the last 6 months (seller-owned orders)
        now = timezone.now()
        monthly = []
        months = []
        for i in range(5, -1, -1):
            m_date = (now - timedelta(days=now.day-1)).replace(day=1) - timedelta(days=30*i)
            # normalize month/year
            yr = m_date.year
            mo = m_date.month
            months.append((yr, mo))

        for yr, mo in months:
            if cat_filter:
                # sum orderitems subtotal for this seller and category
                s = OrderItem.objects.filter(order__seller=request.user, product__category__id=cat_filter, order__created_at__year=yr, order__created_at__month=mo).aggregate(total=Sum('subtotal'))
                total = s.get('total') or 0
            else:
                s = Order.objects.filter(seller=request.user, created_at__year=yr, created_at__month=mo).aggregate(total=Sum('total'))
                total = s.get('total') or 0
            monthly.append({'year': yr, 'month': mo, 'total': float(total)})

        return JsonResponse({
            'customersTotal': total_customers,
            'ordersCount': total_orders,
            'inCartTotal': in_cart_total,
            'monthly_sales': monthly,
            'db_ok': True,
        })
    except (ProgrammingError, DatabaseError) as e:
        # If the Quote/order tables aren't present or DB inaccessible, return safe defaults
        return JsonResponse({'customersTotal': 0, 'ordersCount': 0, 'inCartTotal': 0, 'monthly_sales': [], 'db_ok': False, 'error': str(e)})


@login_required
def dashboard_quotes(request, buyer_id):
    """Return quotes/messages sent by a given buyer to the logged-in seller."""
    try:
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
        return JsonResponse({'quotes': data, 'db_ok': True})
    except (ProgrammingError, DatabaseError) as e:
        return JsonResponse({'quotes': [], 'db_ok': False, 'error': str(e)})


@login_required
def dashboard_cart_activity(request):
    """Return recent cart additions for this seller (buyer username, product, qty, added_at)."""
    try:
        qs = CartItem.objects.filter(product__seller=request.user).order_by('-added_at')[:20]
        data = []
        for item in qs:
            data.append({
                'id': item.id,
                'buyer_username': item.user.username,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'added_at': item.added_at.isoformat(),
            })
        return JsonResponse({'cart_activity': data, 'db_ok': True})
    except (ProgrammingError, DatabaseError) as e:
        return JsonResponse({'cart_activity': [], 'db_ok': False, 'error': str(e)})


@login_required
def dashboard_map_points(request):
    """Return geo points for map display representing recent buyers for this seller.

    Response: { points: [{ title, customers, geometry: { type: 'Point', coordinates: [lng, lat] } }, ...] }
    """
    try:
        qs = Order.objects.filter(seller=request.user).order_by('-created_at')[:200]
        points = []
        # simple city -> coords mapping for common PH cities (approximate)
        city_coords = {
            'manila': [120.9842, 14.5995],
            'cebu': [123.8854, 10.3157],
            'davao': [125.6131, 7.1907],
            'quezon': [121.2326, 14.1035],
            'makati': [121.0236, 14.5547]
        }
        for o in qs:
            # prefer stored profile coordinates if available
            coord = None
            try:
                profile = UserProfile.objects.filter(user=o.buyer).first()
                if profile and profile.latitude is not None and profile.longitude is not None:
                    coord = [profile.longitude, profile.latitude]
            except Exception:
                profile = None

            # fallback to order-level city/country heuristics
            if not coord:
                city = (o.buyer_city or '').lower()
                for key, val in city_coords.items():
                    if key in city:
                        coord = val
                        break
                if not coord:
                    if (o.buyer_country or '').lower() in ['philippines', 'ph']:
                        coord = city_coords.get('manila')

            if coord:
                title = f"{getattr(o.buyer, 'username', 'Buyer')} ({o.buyer_city or ''})"
                points.append({
                    'title': title,
                    'customers': 1,
                    'geometry': { 'type': 'Point', 'coordinates': coord }
                })
        return JsonResponse({'points': points, 'db_ok': True})
    except Exception as e:
        return JsonResponse({'points': [], 'db_ok': False, 'error': str(e)})


@staff_member_required
def admin_dashboard(request):
    """Render a simple admin-facing dashboard that will fetch data via API dynamically."""
    from .utils import get_unique_categories
    cats = get_unique_categories()
    return render(request, 'hc_app/admin_dashboard.html', {'categories': cats})


@staff_member_required
@require_GET
def admin_sales_api(request):
    """Return sales/bookings aggregates. Query params: start_date, end_date (YYYY-MM-DD), category (id).

    Response: { total_sales: float, total_orders: int, by_category: [{category, total}], timeseries: [{year, month, total}] }
    """
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    cat = request.GET.get('category')
    try:
        q = Order.objects.all()

        # date filters
        try:
            if start:
                sd = datetime.strptime(start, '%Y-%m-%d')
                q = q.filter(created_at__date__gte=sd.date())
            if end:
                ed = datetime.strptime(end, '%Y-%m-%d')
                q = q.filter(created_at__date__lte=ed.date())
        except Exception:
            # ignore parse errors and continue with unfiltered q
            pass

        # category filter: if provided, narrow to orders that have items in that category
        if cat:
            try:
                cid = int(cat)
                order_ids = OrderItem.objects.filter(product__category__id=cid).values_list('order_id', flat=True)
                q = q.filter(id__in=order_ids)
            except Exception:
                cq = Category.objects.filter(Q(slug__iexact=cat) | Q(name__iexact=cat)).first()
                if cq:
                    order_ids = OrderItem.objects.filter(product__category=cq).values_list('order_id', flat=True)
                    q = q.filter(id__in=order_ids)

        # total sales and orders
        total_sales = q.aggregate(total=Sum('total')).get('total') or 0
        total_orders = q.distinct().count()

        # by category (use OrderItem for accurate per-product subtotals)
        by_cat_qs = OrderItem.objects.filter(order__in=q).values('product__category__id', 'product__category__name').annotate(total=Sum('subtotal')).order_by('-total')
        by_category = [{'category_id': b['product__category__id'], 'category': b['product__category__name'], 'total': float(b['total'] or 0)} for b in by_cat_qs]

        # timeseries: monthly sums for selected range (or last 6 months by default)
        timeseries = []
        if start and end:
            try:
                sd = datetime.strptime(start, '%Y-%m-%d')
                ed = datetime.strptime(end, '%Y-%m-%d')
                cur = sd.replace(day=1)
                while cur <= ed:
                    s = q.filter(created_at__year=cur.year, created_at__month=cur.month).aggregate(total=Sum('total'))
                    timeseries.append({'year': cur.year, 'month': cur.month, 'total': float(s.get('total') or 0)})
                    nxt = cur + timedelta(days=32)
                    cur = nxt.replace(day=1)
            except Exception:
                pass
        else:
            now = timezone.now()
            for i in range(5, -1, -1):
                m_date = (now - timedelta(days=now.day-1)).replace(day=1) - timedelta(days=30*i)
                yr = m_date.year
                mo = m_date.month
                s = q.filter(created_at__year=yr, created_at__month=mo).aggregate(total=Sum('total'))
                timeseries.append({'year': yr, 'month': mo, 'total': float(s.get('total') or 0)})

        return JsonResponse({'total_sales': float(total_sales), 'total_orders': total_orders, 'by_category': by_category, 'timeseries': timeseries, 'db_ok': True})
    except (ProgrammingError, DatabaseError) as e:
        return JsonResponse({'total_sales': 0.0, 'total_orders': 0, 'by_category': [], 'timeseries': [], 'db_ok': False, 'error': str(e)})


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
        # require the posted confirm_username to match the logged-in username for safety
        confirm_username = request.POST.get('confirm_username', '').strip()
        if confirm_username != request.user.username:
            messages.error(request, 'Deactivation cancelled: username confirmation did not match.')
            return redirect('hc_app:home')

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
def order_confirmation_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
        order_items = OrderItem.objects.filter(order=order)
    except Order.DoesNotExist:
        return render(request, "hc_app/order_confirmation.html", {"message": "Order not found."})

    return render(request, "hc_app/order_confirmation.html", {
        "order": order,
        "order_items": order_items
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
    # build base queryset
    if q:
        results = Product.objects.filter(name__icontains=q) | Product.objects.filter(description__icontains=q)
    else:
        results = Product.objects.all()

    # tolerant category filter: accept id, slug, or name
    if category:
        try:
            cat_id = int(category)
            results = results.filter(category_id=cat_id)
        except (ValueError, TypeError):
            results = results.filter(Q(category__slug__iexact=category) | Q(category__name__iexact=category))

    from .utils import get_unique_categories
    return render(request, 'hc_app/search_results.html', {
        'query': q,
        'results': results,
        'categories': get_unique_categories(),
        'active_category': category,
    })

