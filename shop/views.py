from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CartQuantityForm, CheckoutForm, ContactForm, NewsletterForm, RegisterForm
from .models import Category, Order, OrderItem, Product


class StockUnavailableError(Exception):
    pass


def invalid_cart_quantity_response(request, message='Choose a quantity from 1 to 99.'):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'error': message}, status=400)
    messages.error(request, message)
    return redirect('cart_detail')


def home(request):
    categories = Category.objects.all()[:3]
    featured_products = Product.objects.filter(is_featured=True)[:4]
    bestsellers = Product.objects.filter(is_bestseller=True)[:4]
    newsletter_form = NewsletterForm()
    return render(request, 'shop/home.html', {
        'categories': categories,
        'featured_products': featured_products,
        'bestsellers': bestsellers,
        'newsletter_form': newsletter_form,
    })


def shop_view(request, cat_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.all()

    if cat_slug:
        category = get_object_or_404(Category, slug=cat_slug)
        products = products.filter(category=category)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')

    return render(request, 'shop/shop.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query or '',
        'sort': sort or '',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:4]
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related': related,
    })


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartQuantityForm({'quantity': request.POST.get('quantity', '1')})
    if not form.is_valid():
        return invalid_cart_quantity_response(request)
    try:
        cart.add(product=product, quantity=form.cleaned_data['quantity'])
    except ValueError as error:
        return invalid_cart_quantity_response(request, str(error))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'cart_count': len(cart), 'cart_total': str(cart.get_total_price())})
    messages.success(request, f'Added "{product.name}" to your cart.')
    return redirect('cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'cart_count': len(cart), 'cart_total': str(cart.get_total_price())})
    return redirect('cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartQuantityForm({'quantity': request.POST.get('quantity', '1')})
    if not form.is_valid():
        return invalid_cart_quantity_response(request)
    try:
        cart.add(product=product, quantity=form.cleaned_data['quantity'], override_quantity=True)
    except ValueError as error:
        return invalid_cart_quantity_response(request, str(error))
    return redirect('cart_detail')


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, 'Your cart is empty — add something festive first!')
        return redirect('shop_all')

    initial = {}
    if request.user.is_authenticated:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cart_items = list(cart)
            try:
                with transaction.atomic():
                    product_ids = sorted({item['product'].pk for item in cart_items})
                    locked_products = {
                        product.pk: product
                        for product in Product.objects.select_for_update()
                        .filter(pk__in=product_ids)
                        .order_by('pk')
                    }

                    for item in cart_items:
                        product = locked_products.get(item['product'].pk)
                        available = product.stock if product else 0
                        if available < item['quantity']:
                            raise StockUnavailableError(
                                f'Only {available} of "{item["product"].name}" are available. '
                                'Please update your cart.'
                            )

                    for item in cart_items:
                        product_id = item['product'].pk
                        quantity = item['quantity']
                        updated = Product.objects.filter(
                            pk=product_id,
                            stock__gte=quantity,
                        ).update(stock=F('stock') - quantity)
                        if not updated:
                            product = locked_products[product_id]
                            raise StockUnavailableError(
                                f'"{product.name}" is no longer available in that quantity. '
                                'Please update your cart.'
                            )

                    order = Order.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data['email'],
                        address=form.cleaned_data['address'],
                        phone=form.cleaned_data['phone'],
                    )
                    for item in cart_items:
                        product = locked_products[item['product'].pk]
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            price=product.price,
                            quantity=item['quantity'],
                        )
            except StockUnavailableError as error:
                messages.error(request, str(error))
                return redirect('cart_detail')
            cart.clear()
            return render(request, 'shop/order_success.html', {'order': order})
    else:
        form = CheckoutForm(initial=initial)

    return render(request, 'shop/checkout.html', {'form': form, 'cart': cart})


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for reaching out! We'll get back to you soon.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'shop/contact.html', {'form': form})


@require_POST
def newsletter_signup(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'You are subscribed! Watch your inbox for HoHoHo deals.')
    else:
        messages.error(request, 'Please enter a valid email address.')
    referer = request.META.get('HTTP_REFERER', '')
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    return redirect('home')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'shop/register.html', {'form': form})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/order_history.html', {'orders': orders})
