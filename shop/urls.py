from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop_view, name='shop_all'),
    path('category/<slug:cat_slug>/', views.shop_view, name='category_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/coupon/apply/', views.cart_apply_coupon, name='cart_apply_coupon'),
    path('cart/coupon/remove/', views.cart_remove_coupon, name='cart_remove_coupon'),
    path('checkout/', views.checkout, name='checkout'),

    path('contact/', views.contact_view, name='contact'),
    path('newsletter/', views.newsletter_signup, name='newsletter_signup'),

    path('register/', views.register_view, name='register'),
    path('orders/track/<uuid:tracking_token>/', views.order_track, name='order_track'),
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('orders/', views.order_history, name='order_history'),
]
