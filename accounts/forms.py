from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator

username_validator = UnicodeUsernameValidator()


class CreateUserForm(UserCreationForm):
    email = forms.EmailField(max_length=50,label='Email Address',
                             widget=(forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter Email address'})))
    password1 = forms.CharField(label=_('Password'),
                                widget=(forms.PasswordInput(attrs={'class': 'form-control','placeholder': 'Enter Password'})),
                                )
    password2 = forms.CharField(label=_('Password Confirmation'), widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder': 'Repeat Password'}),
                                )
    username = forms.CharField(
        label=_('Username'),
        max_length=150,
        validators=[username_validator],
        error_messages={'unique': _("A user with that username already exists.")},
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter Username'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)
