from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

app_name = 'hc_app'  # optional, useful for namespacing

urlpatterns = [
    path('', views.register_view, name='register'),    # root shows Register
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home_view, name='home'),       # note trailing slash
    path('sell/', views.sell, name='sell'),
    path('catalog/', views.catalog, name='catalog'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('category/<int:category_id>/', views.category_view, name='category'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart_view'), 
    path('category/<str:category_name>/', views.category_products, name='category_products'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('my_listings/', views.my_listings, name='my_listings'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('ajax/address-suggestions/', views.address_suggestions, name='address_suggestions'),
    path('address-autocomplete/', views.address_autocomplete, name='address_autocomplete'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('my-orders/', views.my_orders_view, name='orders'),
    path('my-orders/delete/<int:order_id>/', views.delete_order, name='delete_order'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)