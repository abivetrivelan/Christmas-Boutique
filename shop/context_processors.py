from .cart import Cart


def cart_context(request):
    """Makes the cart (and its item count) available in every template."""
    return {'nav_cart': Cart(request)}
