from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=15, blank=False)
    street = models.CharField(max_length=200, blank=False)
    city = models.CharField(max_length=100, blank=False)
    state = models.CharField(max_length=100, blank=False)
    zip_code = models.CharField(max_length=20, blank=False)
    country = models.CharField(max_length=50, default='PH')

    def __str__(self):
        return self.user.username
    
class Category(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    image = models.ImageField(upload_to='products/images/', blank=True, null=True)
    # video = models.FileField(upload_to='products/videos/', blank=True, null=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    weight = models.DecimalField(max_digits=6, decimal_places=2, help_text="Weight in ounces", default=0)
    length = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    width = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    height = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def __str__(self):
        return self.name
    
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/images/')

class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Pending')
    shipping_label_url = models.URLField(blank=True, null=True) 
    tracking_code = models.CharField(max_length=100, blank=True, null=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

class Quote(models.Model):
    seller = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='received_quotes')
    buyer = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='sent_quotes')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
                               