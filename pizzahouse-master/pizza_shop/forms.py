from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm, EmailInput, PasswordInput, TextInput

from pizza_shop.models import Contact


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password')
        widgets = {
            'username': TextInput(
                attrs={
                    'placeholder': "Имя",
                    'required': ''
                }
            ),
            'password': PasswordInput(
                attrs={
                    'placeholder': 'Пароль',
                    'required': ''
                }
            ),
        }
        labels = {
            'password': 'Пароль',
        }
        help_texts = {
            'email': '',
        }


class UserRegForm(forms.ModelForm):
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(
        attrs={
            'placeholder': 'Пароль',
            'required': ''
        }))
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput(
        attrs={
            'placeholder': 'Повторите пароль',
            'required': ''
        }))

    class Meta:
        model = User
        fields = ('email', 'username')
        widgets = {
            'email': EmailInput(
                attrs={
                    'placeholder': 'E-mail',
                    'required': ''
                }),
            'username': TextInput(
                attrs={
                    'placeholder': 'Имя',
                    'required': ''
                }
            )
        }

    def clean_password2(self):
        # Check that the two password entries match
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Пароли не совпали")
        return password2


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ('phone',)
        widgets = {
            'phone': TextInput(attrs={'placeholder': '+7-(999)-999-9999'}),
        }