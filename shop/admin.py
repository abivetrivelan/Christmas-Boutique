from django.contrib import admin

from .models import Category, ContactMessage, Coupon, Newsletter, Order, OrderItem, OrderStatusHistory, Product
from .order_services import update_order_status


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_featured', 'is_bestseller')
    list_filter = ('category', 'is_featured', 'is_bestseller')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ('status', 'note', 'changed_by', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email', 'status', 'coupon',
        'discount_amount', 'created_at', 'total_cost',
    )
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = Order.objects.only('status').get(pk=obj.pk).status
        requested_status = obj.status
        if previous_status and previous_status != requested_status:
            obj.status = previous_status
        super().save_model(request, obj, form, change)
        if previous_status and previous_status != requested_status:
            update_order_status(obj, requested_status, changed_by=request.user)
        elif not change:
            OrderStatusHistory.objects.create(
                order=obj,
                status=obj.status,
                changed_by=request.user,
            )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_type', 'value', 'minimum_order', 'expires_at',
        'used_count', 'usage_limit', 'is_active',
    )
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
