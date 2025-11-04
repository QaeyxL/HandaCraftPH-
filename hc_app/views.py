from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from twilio.rest import Client
from .forms import RegisterForm, ProductForm
import requests
from random import choice
from .models import Product, Category, CartItem
from django.shortcuts import get_object_or_404, render

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

def sell(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, 'hc_app/sell.html', {'form': ProductForm(), 'success': True})
    else:
        form = ProductForm()
    return render(request, 'hc_app/sell.html', {'form': form})

def catalog(request):
    products = Product.objects.all()
    return render(request, 'hc_app/catalog.html', {'products': products})

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

def delete_product(request, pk):
    product = Product.objects.get(id=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('catalog')
    return render(request, 'hc_app/delete_confirm.html', {'product': product})

def category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'hc_app/category_products.html', {'category': category, 'products': products})

def home_view(request):
    categories = Category.objects.all()
    products = Product.objects.all()  # for featured products
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
    return redirect(request.META.get('HTTP_REFERER', 'hc_app:home'))

def category_products(request, category_name):
    products = Product.objects.filter(category__name=category_name)
    return render(request, 'hc_app/category_products.html', {'products': products, 'category_name': category_name})

@login_required
def sell(request):
    success = False
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user  # set the logged-in user as seller
            product.save()
            success = True
    else:
        form = ProductForm()

    return render(request, 'hc_app/sell.html', {'form': form, 'success': success})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Only allow the seller who created the product to delete it
    if product.seller != request.user:
        return redirect('hc_app:home')  # or show an error page

    product.delete()
    return redirect('hc_app:sell')  # or redirect to seller's product list

@login_required
def my_listings(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, 'hc_app/my_listings.html', {'products': products})