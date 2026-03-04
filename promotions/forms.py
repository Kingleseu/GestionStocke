from django import forms
from django.utils import timezone
import re
from .models import Promotion
from products.models import Product


class PromotionForm(forms.ModelForm):
    """Formulaire pour créer/modifier une promotion"""
    
    products = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_products'})
    )

    def __init__(self, *args, **kwargs):
        # Normalize products payload from modal to a CSV string ("1,2,3").
        data = kwargs.get('data')
        if data is not None:
            mutable_data = data.copy()
            if hasattr(mutable_data, 'getlist'):
                products_values = mutable_data.getlist('products')
            else:
                raw_value = mutable_data.get('products', [])
                if isinstance(raw_value, (list, tuple)):
                    products_values = list(raw_value)
                elif raw_value is None:
                    products_values = []
                else:
                    products_values = [raw_value]

            raw_products = ','.join(str(v) for v in products_values if v is not None and str(v).strip())
            parsed_ids = re.findall(r'\d+', raw_products)
            mutable_data['products'] = ','.join(parsed_ids)

            kwargs['data'] = mutable_data

        super().__init__(*args, **kwargs)

        # Products are chosen via JS modal; keep field validation but render hidden.
        self.fields['products'].widget = forms.HiddenInput(attrs={'id': 'id_products'})

        # Keep existing selections when editing.
        if self.instance and self.instance.pk and not self.is_bound:
            selected_ids = self.instance.products.values_list('id', flat=True)
            self.initial['products'] = ','.join(str(pid) for pid in selected_ids)

    class Meta:
        model = Promotion
        fields = [
            'name',
            'description',
            'discount_type',
            'discount_value',
            'scope',
            'products',
            'categories',
            'start_date',
            'end_date',
            'is_active',
            'banner_image',
            'banner_message',
            'display_badge',
            'badge_custom_text',
            'note_business',
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ex: Soldes Printemps'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée de la promotion'
            }),
            'discount_type': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '20',
                'step': '0.01',
                'min': '0'
            }),
            'scope': forms.Select(attrs={
                'class': 'form-control'
            }),
            'products': forms.HiddenInput(attrs={
                'id': 'id_products'
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'banner_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'banner_message': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '🎉 Soldes du Printemps! -20% tout!'
            }),
            'display_badge': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'badge_custom_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Laisser vide pour génération auto'
            }),
            'note_business': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notes internes (raison, client, etc.)'
            }),
        }
    
    def clean(self):
        """Validations personnalisées"""
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')
        scope = cleaned_data.get('scope')
        products_raw = cleaned_data.get('products') or ''
        product_ids = [int(pid) for pid in re.findall(r'\d+', str(products_raw))]
        products = Product.objects.filter(id__in=product_ids)
        cleaned_data['products'] = products
        categories = cleaned_data.get('categories')
        
        # Valider les dates
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError(
                    "La date de fin doit être après la date de début"
                )
        
        # Valider la réduction
        if discount_value:
            if discount_type == 'percentage':
                if not (0 < discount_value <= 100):
                    raise forms.ValidationError(
                        "Le pourcentage doit être entre 0 et 100"
                    )
            elif discount_type == 'fixed':
                if discount_value < 0:
                    raise forms.ValidationError(
                        "Le montant fixe ne peut pas être négatif"
                    )
        
        # Valider la portée
        if scope == 'specific_products' and not products:
            raise forms.ValidationError(
                "Veuillez sélectionner au moins un produit"
            )
        
        if scope == 'specific_categories' and not categories:
            raise forms.ValidationError(
                "Veuillez sélectionner au moins une catégorie"
            )
        
        return cleaned_data


class BulkPromotionActionForm(forms.Form):
    """Formulaire pour actions en masse sur les promotions"""
    
    ACTION_CHOICES = [
        ('activate', 'Activer'),
        ('deactivate', 'Désactiver'),
        ('delete', 'Supprimer'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    confirm = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
