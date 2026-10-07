from decimal import Decimal
from .models import Product

CART_SESSION_ID = 'cart'


class Cart:
    """A simple session-backed shopping cart.

    Stored in the session as {product_id (str): quantity (int)} so it
    survives across requests without needing a logged-in user.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if cart is None:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = 0
        if override_quantity:
            self.cart[product_id] = quantity
        else:
            self.cart[product_id] += quantity
        if self.cart[product_id] <= 0:
            self.remove(product)
        else:
            self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_map = {str(p.id): p for p in products}
        for product_id, quantity in self.cart.items():
            product = products_map.get(product_id)
            if not product:
                continue
            total_price = product.price * quantity
            yield {
                'product': product,
                'quantity': quantity,
                'total_price': total_price,
            }

    def __len__(self):
        return sum(self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item['total_price']) for item in self
        ) if self.cart else Decimal('0.00')
