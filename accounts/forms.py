from django import forms
from captcha.fields import CaptchaField
from .models import CustomUser


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-input'
        }),
        min_length=8,
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'form-input'
        }),
        label='Confirm Password'
    )
    
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'address']
        widgets = {
            'username':   forms.TextInput(attrs={'placeholder': 'Choose username', 'class': 'form-input'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'your@email.com', 'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-input'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-input'}),
            'phone':      forms.TextInput(attrs={'placeholder': '+91 1234567890', 'class': 'form-input'}),
            'address':    forms.Textarea(attrs={
                'placeholder': 'Full address — street, city, state, pincode',
                'class': 'form-input',
                'rows': 3,
                'style': 'resize:vertical; min-height:80px;',
            }),
        }
    
    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match!")
        
        return password2
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered!")
        return email


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter username',
            'class': 'form-input',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-input'
        })
    )
    captcha = CaptchaField(
        label='Security Code',
        help_text='Enter the characters shown in the image'
    )
    
    # accounts/forms.py

