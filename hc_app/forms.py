from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Category, ProductImage, UserProfile
from .models import SellerWorkflowTask


class SellerWorkflowForm(forms.ModelForm):
    class Meta:
        model = SellerWorkflowTask
        fields = ['title', 'product', 'order_item', 'due_date', 'notes', 'status']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'order_item': forms.Select(attrs={'class': 'form-select'}),
        }


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    contact_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

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
        fields = ['name', 'price', 'category', 'description', 'weight', 'length', 'width', 'height', 'stock']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use deduplicated categories for the category select to avoid repeated names
        try:
            from .utils import get_unique_categories
            cats = get_unique_categories()
            # Set choices from the Category instances (ModelChoiceField expects choices or queryset)
            self.fields['category'].choices = [(c.id, c.name) for c in cats]
        except Exception:
            # fallback to default queryset if helper fails
            self.fields['category'].queryset = Category.objects.order_by('name')
    
    
    '''
    to add:
    password validation: 1. at least 8 characters long 2. One capital letter
    Email: 1. Cannot reuse previously registered email (no duplicates)
    Contact no: 1. cannot reuse previously registered contact no (no duplicates)
    '''

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
            'state': forms.TextInput(attrs={'placeholder': 'State/Province', 'required': False}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'ZIP/Postal code', 'required': True}),
            'country': forms.TextInput(attrs={'placeholder': 'Country', 'required': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required
        for field in self.fields.values():
            self.fields['state'].required = False
            field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label})