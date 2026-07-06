from django import forms
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from accounts.models import Shop
from accounts.services import build_unique_username, get_user_by_email_and_space
from accounts.models import ACCOUNT_SPACE_CUSTOMER

from .models import (
    Hub,
    HubInventory,
    MerchantAccount,
    ProcurementOrder,
    Supplier,
    SupplyCategory,
    SupplyHomeFeature,
    SupplyHomepageStat,
    SupplyProcessStep,
    SupplyProduct,
    SupplySiteSettings,
)

MAX_STOREFRONT_PHOTO_SIZE = 10 * 1024 * 1024


class PembenyModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.pop('class', None)
                continue
            field.widget.attrs.setdefault('class', 'pb-input')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'pb-checkbox'


class SupplyCategoryForm(PembenyModelForm):
    """Formulaire de création de catégorie fournisseur"""
    class Meta:
        model = SupplyCategory
        fields = ['name', 'description', 'image', 'is_active', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class SupplierForm(PembenyModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name',
            'category',
            'supply_category',
            'contact_name',
            'phone',
            'email',
            'address',
            'logo',
            'description',
            'is_active',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class HubForm(PembenyModelForm):
    coverage_text = forms.CharField(
        label='Communes couvertes',
        required=False,
        help_text='Une commune par ligne ou separee par une virgule.',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'pb-input'}),
    )

    class Meta:
        model = Hub
        fields = [
            'name',
            'code',
            'commune',
            'address',
            'coverage_text',
            'manager_phone',
            'delivery_fee',
            'is_active',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['coverage_text'].initial = '\n'.join(self.instance.coverage_communes or [])

    def clean_coverage_text(self):
        value = self.cleaned_data.get('coverage_text') or ''
        raw_items = []
        for line in value.replace(',', '\n').splitlines():
            item = line.strip()
            if item:
                raw_items.append(item)
        return list(dict.fromkeys(raw_items))

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.coverage_communes = self.cleaned_data.get('coverage_text', [])
        if commit:
            instance.save()
        return instance


class SupplyProductForm(PembenyModelForm):
    class Meta:
        model = SupplyProduct
        fields = [
            'supplier',
            'name',
            'brand',
            'sku',
            'category',
            'supply_category',
            'unit_label',
            'package_size',
            'wholesale_price',
            'currency',
            'minimum_order_quantity',
            'image',
            'description',
            'icon_class',
            'is_active',
            'is_featured',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class HubInventoryForm(PembenyModelForm):
    class Meta:
        model = HubInventory
        fields = [
            'hub',
            'product',
            'available_quantity',
            'reserved_quantity',
            'reorder_threshold',
        ]

    def clean(self):
        cleaned = super().clean()
        available = cleaned.get('available_quantity') or 0
        reserved = cleaned.get('reserved_quantity') or 0
        if reserved > available:
            raise forms.ValidationError('La quantite reservee ne peut pas depasser la quantite disponible.')
        return cleaned


class MerchantAccountForm(PembenyModelForm):
    shop_name = forms.CharField(label='Nom de la boutique', max_length=100)
    shop_email = forms.EmailField(label='Email boutique', required=False)
    shop_address = forms.CharField(
        label='Adresse / repere',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    class Meta:
        model = MerchantAccount
        fields = [
            'shop_name',
            'shop_email',
            'shop_address',
            'owner_full_name',
            'commune',
            'contact_phone',
            'secondary_phone',
            'whatsapp',
            'whatsapp_active',
            'shop_type',
            'business_age',
            'storefront_photo',
            'preferred_hub',
            'credit_limit',
            'credit_used',
            'is_credit_enabled',
        ]
        labels = {
            'owner_full_name': 'Nom complet du proprietaire / gerant',
            'commune': 'Commune',
            'contact_phone': 'Numero de telephone principal',
            'secondary_phone': 'Numero secondaire',
            'whatsapp': 'Numero WhatsApp',
            'whatsapp_active': 'WhatsApp actif sur ce numero ?',
            'shop_type': 'Type de boutique',
            'business_age': "Anciennete de l'activite",
            'storefront_photo': 'Photo de la devanture du PDV',
            'preferred_hub': 'Hub prefere',
            'credit_limit': 'Limite de credit',
            'credit_used': 'Credit utilise',
            'is_credit_enabled': 'Credit actif',
        }
        help_texts = {
            'business_age': 'PEMBENY prequalifie les boutiques avec au moins 6 mois d activite.',
            'storefront_photo': 'Facade de face, bien cadree, lisible. Fichier inferieur a 10MB.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['shop_name'].initial = self.instance.shop.name
            self.fields['shop_email'].initial = self.instance.shop.email
            self.fields['shop_address'].initial = self.instance.shop.address

    def clean_storefront_photo(self):
        photo = self.cleaned_data.get('storefront_photo')
        if photo and getattr(photo, 'size', 0) > MAX_STOREFRONT_PHOTO_SIZE:
            raise forms.ValidationError('La photo doit faire moins de 10MB.')
        return photo

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            shop = instance.shop
            shop.name = self.cleaned_data['shop_name'].strip()
            shop.email = (self.cleaned_data.get('shop_email') or '').strip()
            shop.address = (self.cleaned_data.get('shop_address') or '').strip()
            shop.phone = instance.contact_phone
            shop.save(update_fields=['name', 'email', 'address', 'phone'])
        return instance


class ProcurementOrderStatusForm(forms.ModelForm):
    note = forms.CharField(
        label='Note de suivi',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'pb-input', 'placeholder': 'Ex: Commande chargee sur triporteur.'}),
    )

    class Meta:
        model = ProcurementOrder
        fields = ['status', 'payment_reference']
        widgets = {
            'status': forms.Select(attrs={'class': 'pb-input'}),
            'payment_reference': forms.TextInput(attrs={'class': 'pb-input'}),
        }


class SupplySiteSettingsForm(PembenyModelForm):
    class Meta:
        model = SupplySiteSettings
        fields = [
            'brand_name',
            'brand_signature',
            'logo',
            'hero_badge',
            'hero_title',
            'hero_subtitle',
            'primary_cta_text',
            'primary_cta_url',
            'secondary_cta_text',
            'secondary_cta_url',
            'network_title',
            'network_subtitle',
            'contact_phone',
            'footer_text',
        ]
        widgets = {
            'hero_subtitle': forms.Textarea(attrs={'rows': 4}),
            'network_subtitle': forms.Textarea(attrs={'rows': 3}),
        }


class SupplyHomepageStatForm(PembenyModelForm):
    class Meta:
        model = SupplyHomepageStat
        fields = ['value', 'label', 'order', 'is_active']


class SupplyHomeFeatureForm(PembenyModelForm):
    class Meta:
        model = SupplyHomeFeature
        fields = ['icon_class', 'title', 'body', 'badge', 'order', 'is_active']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
        }


class SupplyProcessStepForm(PembenyModelForm):
    class Meta:
        model = SupplyProcessStep
        fields = ['number', 'title', 'body', 'icon_class', 'order', 'is_active']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
        }


class MerchantSignupForm(forms.Form):
    WHATSAPP_CHOICES = [
        ('yes', 'Oui'),
        ('no', 'Non'),
    ]

    shop_name = forms.CharField(
        label='Nom de la boutique',
        max_length=100,
        help_text="Nom exact tel qu'il apparait sur l'enseigne ou communique par le proprietaire.",
    )
    owner_full_name = forms.CharField(
        label='Nom complet du proprietaire / gerant',
        max_length=180,
        help_text='Ex : Felicien TSHIAMA KAPINGA',
    )
    email = forms.EmailField(
        label='Email de connexion',
        help_text='Cet email servira a se connecter a l espace boutique.',
    )
    phone = forms.CharField(
        label='Numero de telephone principal',
        max_length=50,
        help_text='Ex : 0815 342 781',
    )
    secondary_phone = forms.CharField(
        label='Numero secondaire',
        max_length=50,
        required=False,
        help_text='Laisser vide si pas de deuxieme numero.',
    )
    whatsapp_active = forms.ChoiceField(
        label='WhatsApp actif sur ce numero ?',
        choices=WHATSAPP_CHOICES,
        initial='yes',
        widget=forms.RadioSelect,
    )
    shop_type = forms.ChoiceField(
        label='Type de boutique',
        choices=MerchantAccount.SHOP_TYPE_CHOICES,
        initial=MerchantAccount.SHOP_TYPE_NEIGHBORHOOD,
        help_text='Regarde et choisis le type le plus proche de ce que tu observes.',
        widget=forms.RadioSelect,
    )
    business_age = forms.ChoiceField(
        label="Anciennete de l'activite",
        choices=MerchantAccount.BUSINESS_AGE_CHOICES,
        initial=MerchantAccount.AGE_6_TO_12_MONTHS,
        help_text='Critere de pre-qualification : PEMBENY exige au minimum 6 mois d activite.',
        widget=forms.RadioSelect,
    )
    storefront_photo = forms.FileField(
        label='Photo de la devanture du PDV',
        help_text='Photo obligatoire, facade de face, bien cadree, lisible. Fichier inferieur a 10MB.',
    )
    commune = forms.CharField(label='Commune', max_length=80)
    address = forms.CharField(label='Adresse / repere', widget=forms.Textarea(attrs={'rows': 3}))
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput())
    password_confirm = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.pop('class', None)
                continue
            field.widget.attrs.setdefault('class', 'pb-input')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_by_email_and_space(email, ACCOUNT_SPACE_CUSTOMER):
            raise ValidationError('Une boutique utilise deja cet email.')
        return email

    def clean_whatsapp_active(self):
        return self.cleaned_data.get('whatsapp_active') == 'yes'

    def clean_storefront_photo(self):
        photo = self.cleaned_data.get('storefront_photo')
        if not photo:
            raise ValidationError('La photo de la devanture est obligatoire.')
        if photo.size > MAX_STOREFRONT_PHOTO_SIZE:
            raise ValidationError('La photo doit faire moins de 10MB.')
        content_type = getattr(photo, 'content_type', '')
        if content_type and not content_type.startswith('image/'):
            raise ValidationError('Le fichier doit etre une image.')
        return photo

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Les mots de passe ne correspondent pas.')
        return cleaned

    def save(self):
        email = self.cleaned_data['email']
        owner_full_name = self.cleaned_data['owner_full_name'].strip()
        name_parts = owner_full_name.split()
        first_name = name_parts[0] if name_parts else owner_full_name
        last_name = ' '.join(name_parts[1:])
        phone = self.cleaned_data['phone'].strip()
        secondary_phone = self.cleaned_data.get('secondary_phone', '').strip()
        whatsapp_active = self.cleaned_data['whatsapp_active']
        whatsapp = phone if whatsapp_active else ''
        user = User(
            username=build_unique_username(email.split('@')[0]),
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=True,
            is_staff=False,
        )
        user.set_password(self.cleaned_data['password'])
        user.save()

        merchant_group, _ = Group.objects.get_or_create(name='Merchant')
        user.groups.add(merchant_group)

        shop = Shop.objects.create(
            name=self.cleaned_data['shop_name'].strip(),
            created_by=user,
            address=self.cleaned_data['address'].strip(),
            phone=phone,
            email=email,
        )
        profile = user.profile
        profile.shop = shop
        profile.phone = phone
        profile.address = self.cleaned_data['address'].strip()
        profile.save(update_fields=['shop', 'phone', 'address', 'updated_at'])

        MerchantAccount.objects.update_or_create(
            shop=shop,
            defaults={
                'owner_full_name': owner_full_name,
                'commune': self.cleaned_data['commune'].strip(),
                'contact_phone': phone,
                'secondary_phone': secondary_phone,
                'whatsapp': whatsapp,
                'whatsapp_active': whatsapp_active,
                'shop_type': self.cleaned_data['shop_type'],
                'business_age': self.cleaned_data['business_age'],
                'storefront_photo': self.cleaned_data['storefront_photo'],
            },
        )
        return user, shop