from decimal import Decimal, ROUND_HALF_UP
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    """Product category: Trees, Ornaments, Lights, etc."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])


class Product(models.Model):
    """A single product for sale."""
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    image_url = models.URLField(max_length=500, help_text='External image URL (or /static/... path)')
    stock = models.PositiveIntegerField(default=20)
    is_featured = models.BooleanField(default=False, help_text='Show on the homepage highlight sections')
    is_bestseller = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name='product_price_positive',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f'{base_slug}-{i}'
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0


class ContactMessage(models.Model):
    """Messages submitted through the Contact page form."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.first_name} {self.last_name} <{self.email}>'


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Percentage'),
        ('flat', 'Fixed amount'),
    ]

    code = models.CharField(max_length=32, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    minimum_order = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(value__gt=0),
                name='coupon_value_positive',
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(discount_type='percent')
                    | models.Q(value__lte=100)
                ),
                name='coupon_percent_at_most_100',
            ),
            models.CheckConstraint(
                condition=models.Q(minimum_order__gte=0),
                name='coupon_minimum_nonnegative',
            ),
        ]

    def clean(self):
        self.code = self.code.strip().upper()
        if self.discount_type == 'percent' and self.value > Decimal('100.00'):
            raise ValidationError({'value': 'Percentage discounts cannot exceed 100%.'})

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def validation_error(self, subtotal, at=None):
        at = at or timezone.now()
        if not self.is_active:
            return 'This coupon is no longer active.'
        if self.expires_at and self.expires_at <= at:
            return 'This coupon has expired.'
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return 'This coupon has reached its usage limit.'
        if subtotal < self.minimum_order:
            return f'Spend at least ${self.minimum_order} to use this coupon.'
        return ''

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percent':
            discount = subtotal * self.value / Decimal('100')
        else:
            discount = min(self.value, subtotal)
        return min(discount, subtotal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def __str__(self):
        return self.code


class Order(models.Model):
    """A customer order created at checkout."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='orders'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    coupon = models.ForeignKey(
        Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders'
    )
    discount_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} - {self.first_name} {self.last_name}'

    @property
    def total_cost(self):
        subtotal = sum((item.line_total for item in self.items.all()), Decimal('0.00'))
        return max(Decimal('0.00'), subtotal - self.discount_amount)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name='order_item_price_positive',
            ),
        ]

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def line_total(self):
        return self.price * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, related_name='status_history', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='order_status_changes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Order #{self.order_id}: {self.get_status_display()}'


class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
