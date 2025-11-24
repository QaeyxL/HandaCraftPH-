from django.contrib import admin
from .models import UserProfile, Category, Product, ProductImage, Order, OrderItem, Quote, AuditLog


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


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
	list_display = ('id', 'buyer', 'seller', 'product', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ('action', 'target_user', 'performed_by', 'timestamp')
	list_filter = ('action',)
