from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from datetime import date

UserModel = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=15, blank=False)
    street = models.CharField(max_length=200, blank=False)
    city = models.CharField(max_length=100, blank=False)
    state = models.CharField(max_length=100, blank=False)
    zip_code = models.CharField(max_length=20, blank=False)
    country = models.CharField(max_length=50, default='PH')
    is_seller = models.BooleanField(default=False)
    # soft-delete/archive flag
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    image = models.ImageField(upload_to='products/images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    weight = models.DecimalField(max_digits=6, decimal_places=2, help_text="Weight in ounces", default=0)
    stock = models.PositiveIntegerField(default=0)  # inventory
    length = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    width = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    height = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    seller_street = models.CharField(max_length=200, blank=True, null=True)
    seller_city = models.CharField(max_length=100, blank=True, null=True)
    seller_state = models.CharField(max_length=100, blank=True, null=True)
    seller_zip_code = models.CharField(max_length=20, blank=True, null=True)
    seller_country = models.CharField(max_length=50, default='PH')

    def __str__(self):
        return self.name


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    # store the computed price for this cart item (may include customization price)
    item_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # customization selected by the buyer, stored as JSON: { attribute_slug: [option_id,...] or value }
    customization = models.JSONField(null=True, blank=True)

    def customization_summary(self):
        if not self.customization:
            return ''
        try:
            parts = []
            for k, v in (self.customization.items() if isinstance(self.customization, dict) else []):
                if isinstance(v, list):
                    parts.append(f"{k}: {','.join([str(x) for x in v])}")
                else:
                    parts.append(f"{k}: {v}")
            return '; '.join(parts)
        except Exception:
            return str(self.customization)

    def __str__(self):
        summary = self.customization_summary()
        if summary:
            return f"{self.product.name} x {self.quantity} ({summary})"
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
    estimated_delivery = models.DateField(default=date.today)

    buyer_street = models.CharField(max_length=200, blank=True, null=True)
    buyer_city = models.CharField(max_length=100, blank=True, null=True)
    buyer_state = models.CharField(max_length=100, blank=True, null=True)
    buyer_zip_code = models.CharField(max_length=20, blank=True, null=True)
    buyer_country = models.CharField(max_length=50, blank=True, null=True)

    seller_street = models.CharField(max_length=200, blank=True, null=True)
    seller_city = models.CharField(max_length=100, blank=True, null=True)
    seller_state = models.CharField(max_length=100, blank=True, null=True)
    seller_zip_code = models.CharField(max_length=20, blank=True, null=True)
    seller_country = models.CharField(max_length=50, blank=True, null=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255, default='Unknown Product')
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)


class Quote(models.Model):
    seller = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='received_quotes')
    buyer = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='sent_quotes')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('deactivate', 'Deactivate'),
        ('archive', 'Archive'),
        ('reactivate', 'Reactivate'),
    ]

    target_user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_audit_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_action_display()} -> {self.target_user.username} @ {self.timestamp.isoformat()}"


class SellerWorkflowTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    seller = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='workflow_tasks')
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='workflow_tasks')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='workflow_tasks')
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Attribute(models.Model):
    """Defines a customization attribute (Material, Color, Size, Finish, Add-ons)."""
    TYPE_CHOICES = [
        ('single', 'Single choice (dropdown/radio)'),
        ('multi', 'Multiple choice (checkboxes)'),
        ('numeric', 'Numeric (custom dimensions)'),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='single')

    def __str__(self):
        return self.name


class AttributeOption(models.Model):
    """An option for an Attribute (e.g., 'Abaca - Grade A', 'Natural', 'Polished').

    price_modifier: positive or negative Decimal applied additively.
    modifier_type: 'add' applies additive, 'mul' applies multiplicative factor.
    """
    MODIFIER_CHOICES = [
        ('add', 'Add (₱)'),
        ('mul', 'Multiply (x)')
    ]

    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=140)
    sku = models.CharField(max_length=80, blank=True, null=True)
    price_modifier = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    modifier_type = models.CharField(max_length=8, choices=MODIFIER_CHOICES, default='add')
    extra = models.JSONField(blank=True, null=True)  # for color swatch hex, images etc.

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductAttribute(models.Model):
    """Attach an Attribute to a Product and indicate if it's required."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'attribute')
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}"
