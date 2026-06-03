import datetime
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.contrib.auth import get_user_model

class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'auth-input reg-shadow'})
    )

    class Meta:
        model = get_user_model()
        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'auth-input reg-shadow'})
            field.label = ''

        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'

        self.fields['username'].help_text = 'Только буквы, цифры и @/./+/-/_. Не более 150 символов'
        self.fields['password1'].help_text ='Пароль должен содержать минимум 8 символов и не быть слишком простым'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError('Email уже зарегистрирован')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginUserForm(AuthenticationForm):

    class Meta:
        model = get_user_model()
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'auth-input reg-shadow'})
            field.label = ''

        self.fields['username'].widget.attrs['placeholder'] = 'Username or email@'
        self.fields['password'].widget.attrs['placeholder'] = 'Password'


class ProfileUserForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'auth-input reg-shadow'})
    )
    date_birth = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'text',
                'class': 'auth-input reg-shadow js-date-picker',
                'autocomplete': 'off',
            }
        )
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'id': 'id_avatar',  # Явно указываем id
            'accept': 'image/*',
            'style': 'display: none;'
        })
    )

    delete_avatar = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = get_user_model()
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'date_birth',
            'avatar',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name not in ['avatar', 'delete_avatar']:
                current_classes = field.widget.attrs.get('class', '').split()

                for css_class in ['auth-input', 'reg-shadow']:
                    if css_class not in current_classes:
                        current_classes.append(css_class)

                field.widget.attrs['class'] = ' '.join(current_classes)

            field.label = ''

        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['date_birth'].widget.attrs['placeholder'] = 'Date of Birth'

        self.fields['username'].help_text = 'Только буквы, цифры и @/./+/-/_. Не более 150 символов'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        current_user = self.instance
        if get_user_model().objects.exclude(pk=current_user.pk).filter(email=email).exists():
            raise forms.ValidationError('Email уже зарегистрирован')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        delete_avatar = self.cleaned_data.get('delete_avatar')
        new_avatar = self.cleaned_data.get('avatar')

        if delete_avatar and user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None

        if new_avatar:
            user.avatar = new_avatar

        if commit:
            user.save()
        return user