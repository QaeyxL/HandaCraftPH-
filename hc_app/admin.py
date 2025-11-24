from django.contrib import admin
from .models import UserProfile, Category, Product, ProductImage, Order, OrderItem, Quote, AuditLog
from .models import SellerWorkflowTask
from .models import Attribute, AttributeOption, ProductAttribute
from .models import CartItem


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'contact_number', 'is_seller', 'is_archived')
	list_filter = ('is_seller', 'is_archived')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'seller', 'price', 'category', 'created_at')
	list_filter = ('category',)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
	list_display = ('product',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'buyer', 'seller', 'total', 'status', 'created_at')
	list_filter = ('status',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('order', 'product', 'quantity', 'subtotal')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'product', 'quantity', 'item_price', 'customization_summary', 'added_at')
	list_filter = ('product', 'added_at')
	readonly_fields = ('customization_summary',)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
	list_display = ('id', 'buyer', 'seller', 'product', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ('action', 'target_user', 'performed_by', 'timestamp')
	list_filter = ('action',)


@admin.register(SellerWorkflowTask)
class SellerWorkflowTaskAdmin(admin.ModelAdmin):
	list_display = ('title', 'seller', 'product', 'order_item', 'due_date', 'status')
	list_filter = ('status', 'due_date')
	search_fields = ('title', 'notes')


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug', 'type')
	prepopulated_fields = {'slug': ('name',)}


@admin.register(AttributeOption)
class AttributeOptionAdmin(admin.ModelAdmin):
	list_display = ('attribute', 'value', 'modifier_type', 'price_modifier')
	list_filter = ('attribute', 'modifier_type')


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
	list_display = ('product', 'attribute', 'required', 'order')
	list_filter = ('required',)
