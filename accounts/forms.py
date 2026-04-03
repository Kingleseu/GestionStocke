from django import forms
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.utils import timezone

from store.models import CustomerProfile

from .models import (
    ACCOUNT_SPACE_CHOICES,
    ACCOUNT_SPACE_CUSTOMER,
    ACCOUNT_SPACE_STAFF,
    CashierInvitation,
    Shop,
    STAFF_ROLE_CHOICES,
    UserProfile,
)
from .services import account_space_for_user, build_unique_username, get_user_by_email_and_space




from django.contrib.auth import authenticate

class StaffLoginForm(forms.Form):
    """Formulaire de connexion dédié au personnel (Manager/Caissier)."""
    email = forms.EmailField(
        label='Email professionnel',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre.email@boutique.com', 'autofocus': True})
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # On vérifie d'abord si l'utilisateur existe dans l'espace Staff
            user = get_user_by_email_and_space(email, ACCOUNT_SPACE_STAFF)
            if not user:
                raise ValidationError("Aucun compte du personnel n'est lié à cet email.")
            
            # Authentification standard Django
            self.user_cache = authenticate(username=user.username, password=password)
            if self.user_cache is None:
                raise ValidationError("Mot de passe incorrect.")
            elif not self.user_cache.is_active:
                raise ValidationError("Ce compte est désactivé.")
        return cleaned_data

class CustomerLoginForm(forms.Form):
    """Formulaire de connexion pour les clients."""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre@email.com', 'autofocus': True})
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = get_user_by_email_and_space(email, ACCOUNT_SPACE_CUSTOMER)
            if not user:
                raise ValidationError("Aucun compte client n'est lié à cet email.")
            
            self.user_cache = authenticate(username=user.username, password=password)
            if self.user_cache is None:
                raise ValidationError("Mot de passe incorrect.")
            elif not self.user_cache.is_active:
                raise ValidationError("Ce compte est désactivé.")
        return cleaned_data

class CustomerSignupForm(forms.Form):
    first_name = forms.CharField(label='Prénoms', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150)
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Téléphone', max_length=20)
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput())
    password_confirm = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput())

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_by_email_and_space(email, ACCOUNT_SPACE_CUSTOMER):
            raise ValidationError('Un compte client existe déjà avec cet email.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self):
        email = self.cleaned_data['email']
        first_name = self.cleaned_data['first_name'].strip()
        last_name = self.cleaned_data['last_name'].strip()
        password = self.cleaned_data['password']

        username_seed = email.split('@')[0] or f'{first_name}{last_name}'
        user = User(
            username=build_unique_username(username_seed),
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=True,
        )
        user.set_password(password)
        user.save()

        CustomerProfile.objects.update_or_create(
            user=user,
            defaults={
                'phone': self.cleaned_data['phone'].strip(),
                'city': '',
                'address': '',
                'zip_code': '',
            },
        )
        return user


class ManagerSignupForm(forms.Form):
    shop_name = forms.CharField(label='Nom de la boutique', max_length=100)
    first_name = forms.CharField(label='Prénom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150)
    email = forms.EmailField(label='Email professionnel')
    phone = forms.CharField(label='Téléphone', max_length=20)
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput())
    password_confirm = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput())

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_by_email_and_space(email, ACCOUNT_SPACE_STAFF):
            raise ValidationError('Un compte du personnel existe déjà avec cet email.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self):
        email = self.cleaned_data['email']
        first_name = self.cleaned_data['first_name'].strip()
        last_name = self.cleaned_data['last_name'].strip()
        password = self.cleaned_data['password']

        user = User(
            username=build_unique_username(email.split('@')[0]),
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=True,
            is_staff=True,
        )
        user.set_password(password)
        user.save()

        shop = Shop.objects.create(
            name=self.cleaned_data['shop_name'].strip(),
            created_by=user,
            phone=self.cleaned_data['phone'].strip(),
            email=email,
        )

        profile = user.profile
        profile.shop = shop
        profile.save(update_fields=['shop', 'updated_at'])
        return user, shop


class StaffInvitationForm(forms.Form):
    role = forms.ChoiceField(label='Rôle', choices=STAFF_ROLE_CHOICES)
    first_name = forms.CharField(label='Prénom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150, required=False)
    email = forms.EmailField(label='Email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_by_email_and_space(email, ACCOUNT_SPACE_STAFF):
            raise ValidationError('Un membre du personnel existe déjà avec cet email.')
        if CashierInvitation.objects.filter(
            email__iexact=email,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).exists():
            raise ValidationError('Une invitation active existe déjà pour cet email.')
        return email


class StaffInvitationRegistrationForm(forms.Form):
    first_name = forms.CharField(label='Prénom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150, required=False)
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput())
    password_confirm = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput())

    def __init__(self, invitation, *args, **kwargs):
        self.invitation = invitation
        initial = kwargs.setdefault('initial', {})
        initial.setdefault('first_name', invitation.first_name)
        initial.setdefault('last_name', invitation.last_name)
        initial.setdefault('email', invitation.email)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if email != self.invitation.email:
            raise ValidationError("Utilisez l'email qui a reçu l'invitation.")
        if get_user_by_email_and_space(email, ACCOUNT_SPACE_STAFF):
            raise ValidationError('Un membre du personnel existe déjà avec cet email.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self):
        first_name = self.cleaned_data['first_name'].strip()
        last_name = self.cleaned_data['last_name'].strip()
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']

        user = User(
            username=build_unique_username(email.split('@')[0]),
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=False,
            is_staff=True,
        )
        user.set_password(password)
        user.save()

        group_name = self.invitation.role
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

        inviter_profile = self.invitation.created_by.profile
        user.profile.shop = inviter_profile.shop
        user.profile.save(update_fields=['shop', 'updated_at'])
        return user


class ProfileUpdateForm(forms.Form):
    first_name = forms.CharField(label='Prenom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150, required=False)
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Telephone', max_length=50, required=False)
    employee_code = forms.CharField(label='Matricule', max_length=50, required=False)
    position_title = forms.CharField(label='Poste', max_length=100, required=False)
    address = forms.CharField(
        label='Adresse',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    hire_date = forms.DateField(
        label="Date d'embauche",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    emergency_contact_name = forms.CharField(
        label="Contact d'urgence",
        max_length=150,
        required=False,
    )
    emergency_contact_phone = forms.CharField(
        label="Telephone d'urgence",
        max_length=50,
        required=False,
    )
    notes = forms.CharField(
        label='Notes internes',
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        profile = user.profile
        initial = kwargs.setdefault('initial', {})
        initial.setdefault('first_name', user.first_name)
        initial.setdefault('last_name', user.last_name)
        initial.setdefault('email', user.email)
        initial.setdefault('phone', profile.phone)
        initial.setdefault('employee_code', profile.employee_code)
        initial.setdefault('position_title', profile.position_title)
        initial.setdefault('address', profile.address)
        initial.setdefault('hire_date', profile.hire_date)
        initial.setdefault('emergency_contact_name', profile.emergency_contact_name)
        initial.setdefault('emergency_contact_phone', profile.emergency_contact_phone)
        initial.setdefault('notes', profile.notes)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            css_class = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} {css_class}'.strip()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        existing_user = get_user_by_email_and_space(email, account_space_for_user(self.user))
        if existing_user and existing_user.pk != self.user.pk:
            raise ValidationError('Un autre compte du meme espace utilise deja cet email.')
        return email

    def save(self):
        profile = self.user.profile
        self.user.first_name = self.cleaned_data['first_name'].strip()
        self.user.last_name = self.cleaned_data['last_name'].strip()
        self.user.email = self.cleaned_data['email']
        self.user.save(update_fields=['first_name', 'last_name', 'email'])

        profile.phone = self.cleaned_data['phone'].strip()
        profile.employee_code = self.cleaned_data['employee_code'].strip()
        profile.position_title = self.cleaned_data['position_title'].strip()
        profile.address = self.cleaned_data['address'].strip()
        profile.hire_date = self.cleaned_data['hire_date']
        profile.emergency_contact_name = self.cleaned_data['emergency_contact_name'].strip()
        profile.emergency_contact_phone = self.cleaned_data['emergency_contact_phone'].strip()
        profile.notes = self.cleaned_data['notes'].strip()
        profile.save(
            update_fields=[
                'phone',
                'employee_code',
                'position_title',
                'address',
                'hire_date',
                'emergency_contact_name',
                'emergency_contact_phone',
                'notes',
                'updated_at',
            ]
        )
        return self.user
