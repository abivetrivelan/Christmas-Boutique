from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from .models import ContactMessage, Newsletter, Order, OrderItem, Product, Category


User = get_user_model()


class StorefrontTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Ornaments')
		self.product = Product.objects.create(
			category=self.category,
			name='Winter Star Ornament',
			price=Decimal('19.95'),
			image_url='https://example.com/winter-star.jpg',
		)

	def checkout_data(self, first_name='Avery'):
		return {
			'first_name': first_name,
			'last_name': 'Customer',
			'email': 'avery@example.com',
			'address': '12 Pine Street',
			'phone': '555-0100',
		}

	def test_cart_add_update_and_remove(self):
		add_response = self.client.post(
			reverse('cart_add', args=[self.product.pk]),
			{'quantity': '2'},
		)
		self.assertRedirects(add_response, reverse('cart_detail'))
		self.assertEqual(self.client.session['cart'], {str(self.product.pk): 2})

		update_response = self.client.post(
			reverse('cart_update', args=[self.product.pk]),
			{'quantity': '3'},
		)
		self.assertRedirects(update_response, reverse('cart_detail'))
		self.assertEqual(self.client.session['cart'], {str(self.product.pk): 3})

		remove_response = self.client.post(
			reverse('cart_remove', args=[self.product.pk]),
		)
		self.assertRedirects(remove_response, reverse('cart_detail'))
		self.assertEqual(self.client.session['cart'], {})

	def test_cart_rejects_malformed_and_out_of_range_quantities(self):
		for quantity in ('abc', '0', '-1', '100'):
			with self.subTest(quantity=quantity):
				response = self.client.post(
					reverse('cart_add', args=[self.product.pk]),
					{'quantity': quantity},
					HTTP_X_REQUESTED_WITH='XMLHttpRequest',
				)
				self.assertEqual(response.status_code, 400)
				self.assertEqual(self.client.session.get('cart', {}), {})

	def test_product_page_provides_csrf_for_ajax_cart_add(self):
		csrf_client = Client(enforce_csrf_checks=True)
		rejected = csrf_client.post(
			reverse('cart_add', args=[self.product.pk]),
			{'quantity': '1'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(rejected.status_code, 403)

		page = csrf_client.get(self.product.get_absolute_url())
		csrf_cookie = page.cookies.get('csrftoken')
		self.assertIsNotNone(csrf_cookie)

		response = csrf_client.post(
			reverse('cart_add', args=[self.product.pk]),
			{'quantity': '2'},
			HTTP_X_CSRFTOKEN=csrf_cookie.value,
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['cart_count'], 2)

	def test_cart_rejects_cumulative_quantity_over_limit(self):
		url = reverse('cart_add', args=[self.product.pk])
		self.client.post(url, {'quantity': '99'})

		response = self.client.post(
			url,
			{'quantity': '1'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(self.client.session['cart'], {str(self.product.pk): 99})

	def test_checkout_creates_order_items_using_database_price(self):
		self.client.post(
			reverse('cart_add', args=[self.product.pk]),
			{'quantity': '2', 'price': '0.01'},
		)

		response = self.client.post(reverse('checkout'), self.checkout_data())

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'shop/order_success.html')
		order = Order.objects.get()
		item = OrderItem.objects.get(order=order)
		self.assertEqual(item.product, self.product)
		self.assertEqual(item.quantity, 2)
		self.assertEqual(item.price, Decimal('19.95'))
		self.assertEqual(order.total_cost, Decimal('39.90'))
		self.assertEqual(self.client.session.get('cart'), {})

	def test_checkout_confirmation_escapes_customer_input(self):
		self.client.post(
			reverse('cart_add', args=[self.product.pk]),
			{'quantity': '1'},
		)
		script = '<script>alert(1)</script>'

		response = self.client.post(reverse('checkout'), self.checkout_data(script))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;', html=False)
		self.assertNotContains(response, '<script>alert(1)</script>', html=False)

	def test_registration_logs_in_and_login_accepts_registered_user(self):
		credentials = {
			'username': 'winter-customer',
			'email': 'winter@example.com',
			'password1': 'NightSky!winter-1948',
			'password2': 'NightSky!winter-1948',
		}
		register_response = self.client.post(reverse('register'), credentials)

		self.assertRedirects(register_response, reverse('home'))
		user = User.objects.get(username='winter-customer')
		self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

		self.client.logout()
		login_response = self.client.post(reverse('login'), {
			'username': credentials['username'],
			'password': credentials['password1'],
		})
		self.assertRedirects(login_response, reverse('home'))
		self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

	def test_order_history_only_shows_current_users_orders(self):
		owner = User.objects.create_user(username='owner', password='secure-password')
		other_user = User.objects.create_user(username='other', password='secure-password')
		owner_order = Order.objects.create(
			user=owner,
			first_name='Owner',
			email='owner@example.com',
			address='1 Pine Street',
		)
		other_order = Order.objects.create(
			user=other_user,
			first_name='Other',
			email='other@example.com',
			address='2 Pine Street',
		)
		self.client.force_login(owner)

		response = self.client.get(reverse('order_history'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'#{owner_order.pk}')
		self.assertNotContains(response, f'#{other_order.pk}')

	def test_contact_form_saves_valid_message_and_rejects_honeypot(self):
		response = self.client.post(reverse('contact'), {
			'first_name': 'Rowan',
			'last_name': 'Pine',
			'email': 'rowan@example.com',
			'message': 'Please tell me about shipping.',
		})
		self.assertRedirects(response, reverse('contact'))
		self.assertEqual(ContactMessage.objects.count(), 1)

		invalid_response = self.client.post(reverse('contact'), {
			'first_name': 'Invalid',
			'email': 'not-an-email',
		})
		self.assertEqual(invalid_response.status_code, 200)
		self.assertEqual(ContactMessage.objects.count(), 1)

		spam_response = self.client.post(reverse('contact'), {
			'first_name': 'Bot',
			'email': 'bot@example.com',
			'message': 'Spam',
			'website': 'https://spam.example',
		})
		self.assertEqual(spam_response.status_code, 200)
		self.assertEqual(ContactMessage.objects.count(), 1)

	def test_newsletter_form_saves_valid_email_and_rejects_honeypot(self):
		response = self.client.post(reverse('newsletter_signup'), {
			'email': 'hello@example.com',
		})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(Newsletter.objects.count(), 1)

		invalid_response = self.client.post(reverse('newsletter_signup'), {
			'email': 'not-an-email',
		})
		self.assertEqual(invalid_response.status_code, 302)
		self.assertEqual(Newsletter.objects.count(), 1)

		spam_response = self.client.post(reverse('newsletter_signup'), {
			'email': 'bot@example.com',
			'website': 'https://spam.example',
		})
		self.assertEqual(spam_response.status_code, 302)
		self.assertEqual(Newsletter.objects.count(), 1)

	def test_newsletter_rejects_external_referer_redirect(self):
		response = self.client.post(
			reverse('newsletter_signup'),
			{'email': 'hello@example.com'},
			HTTP_REFERER='https://attacker.example/redirect',
		)
		self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)

	def test_product_price_must_be_positive(self):
		with self.assertRaises(IntegrityError), transaction.atomic():
			Product.objects.create(
				category=self.category,
				name='Invalid Price Ornament',
				price=Decimal('-1.00'),
				image_url='https://example.com/invalid.jpg',
			)
