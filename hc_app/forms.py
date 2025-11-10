from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Category, ProductImage


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
        fields = ['name', 'price', 'category', 'description']
    
    
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