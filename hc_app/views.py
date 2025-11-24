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
from easypost import EasyPostClient
from random import choice
from .models import Product, Category, CartItem, ProductImage, Order, OrderItem, UserProfile, Quote
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

    if product.stock <= 0:
        return JsonResponse({"error": 'Product is out of stock.'}, status=400) # inventory

    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        if cart_item.quantity + 1 > product.stock:
            return JsonResponse({"error": 'Cannot add more items than available in stock.'}, status=400) # inventory
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
                cart_total = sum(item.product.price * item.quantity for item in CartItem.objects.filter(user=request.user)) # recalcalculate cart total if item deleted
                return JsonResponse({"success": True, "quantity": 0, "cart_total": float(cart_total), "item_subtotal": 0})

        item_subtotal = cart_item.product.price * cart_item.quantity
        cart_total = sum(item.product.price * item.quantity for item in CartItem.objects.filter(user=request.user))

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
    user_products = Product.objects.filter(seller=request.user)   # edit22 - add (5)
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
        "recent_quotes": Quote.objects.filter(seller=request.user).order_by("-created_at")[:20],  # edit22 - added
        "statuses": statuses,  # edit22 - added
        }
    return render(request, "hc_app/dashboard.html", context)   # edit22 - add context


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
    results = Product.objects.none()
    if q:
        results = Product.objects.filter(name__icontains=q) | Product.objects.filter(description__icontains=q)
    return render(request, 'hc_app/search_results.html', {
        'query': q,
        'results': results
    })

