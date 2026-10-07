from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ContactMessage, Newsletter


class HoneypotFormMixin:
    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Invalid submission.')
        return ''


class ContactForm(HoneypotFormMixin, forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'honeypot-input',
            'autocomplete': 'off',
            'tabindex': '-1',
        }),
    )

    class Meta:
        model = ContactMessage
        fields = ['first_name', 'last_name', 'email', 'address', 'phone', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }


class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField()
    address = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=20, required=False)


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99)


class CouponApplyForm(forms.Form):
    code = forms.CharField(max_length=32)

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()


class NewsletterForm(HoneypotFormMixin, forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'honeypot-input',
            'autocomplete': 'off',
            'tabindex': '-1',
        }),
    )

    class Meta:
        model = Newsletter
        fields = ['email']


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
