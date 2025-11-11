from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Category, ProductImage, UserProfile


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    contact_number = forms.CharField(max_length=15, required=True)

#initialize fields for registration
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
#initialize data validation for password
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        #confirm password and password should match
        if password != confirm:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'category', 'description', 'weight', 'length', 'width', 'height']
    
    
    '''
    to add:
    password validation: 1. at least 8 characters long 2. One capital letter
    Email: 1. Cannot reuse previously registered email (no duplicates)
    Contact no: 1. cannot reuse previously registered contact no (no duplicates)
    '''

# class MultiFileInput(forms.ClearableFileInput):
#     allow_multiple_selected = True

# class ProductImageForm(forms.Form):
#     images = forms.FileField(
#         widget=MultiFileInput(attrs={'multiple': True}),
#         required=True
#     )

class CheckoutForm(forms.Form):
    address_line1 = forms.CharField(label="Address Line 1", max_length=255)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20)
    country = forms.CharField(max_length=50)

class BuyerAddressForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['contact_number', 'street', 'city', 'state', 'zip_code', 'country']
        widgets = {
            'contact_number': forms.TextInput(attrs={'placeholder': 'Enter your contact number', 'required': True}),
            'street': forms.TextInput(attrs={'placeholder': 'Street address', 'required': True}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'required': True}),
            'state': forms.TextInput(attrs={'placeholder': 'State/Province', 'required': True}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'ZIP/Postal code', 'required': True}),
            'country': forms.TextInput(attrs={'placeholder': 'Country', 'required': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required
        for field in self.fields.values():
            field.required = True
            field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label, 'required': True})