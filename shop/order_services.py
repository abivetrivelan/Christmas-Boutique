from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Order, OrderStatusHistory


def send_order_email(order_id, subject, heading, introduction):
    order = Order.objects.prefetch_related('items__product').get(pk=order_id)
    tracking_path = reverse('order_track', args=[order.tracking_token])
    site_url = settings.SITE_URL.rstrip('/')
    context = {
        'order': order,
        'items': list(order.items.all()),
        'heading': heading,
        'introduction': introduction,
        'tracking_url': f'{site_url}{tracking_path}',
        'site_url': site_url,
    }
    text_body = render_to_string('shop/emails/order_update.txt', context)
    html_body = render_to_string('shop/emails/order_update.html', context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    message.attach_alternative(html_body, 'text/html')
    message.send()


def queue_order_confirmation(order):
    transaction.on_commit(
        lambda order_id=order.pk: send_order_email(
            order_id,
            f'Order #{order.pk} confirmed',
            'Thank you for your order',
            'We have received your order and are preparing something lovely for the season.',
        ),
        robust=True,
    )


def update_order_status(order, status, changed_by=None, note=''):
    valid_statuses = dict(Order.STATUS_CHOICES)
    if status not in valid_statuses:
        raise ValueError('Choose a valid order status.')

    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order.pk)
        if locked_order.status == status:
            return False

        locked_order.status = status
        locked_order.save(update_fields=['status'])
        OrderStatusHistory.objects.create(
            order=locked_order,
            status=status,
            changed_by=changed_by,
            note=note,
        )
        transaction.on_commit(
            lambda order_id=locked_order.pk, new_status=status: send_order_email(
                order_id,
                f'Order #{order_id} is {valid_statuses[new_status].lower()}',
                f'Your order is {valid_statuses[new_status].lower()}',
                f'The status of your order has changed to {valid_statuses[new_status].lower()}.',
            ),
            robust=True,
        )

    order.status = status
    return True
