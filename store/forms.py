from django import forms
from .models import HeroSection, HeroCard, AboutSection, AboutStat, TrustSignal, FooterConfig, SocialLink, FooterLink, Universe, Collection
from products.models import Category

class HeroSectionForm(forms.ModelForm):
    class Meta:
        model = HeroSection
        fields = '__all__'
        widgets = {
            'subtitle': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'button_text': forms.TextInput(attrs={'class': 'form-control'}),
            'button_link': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class HeroCardForm(forms.ModelForm):
    class Meta:
        model = HeroCard
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'link_text': forms.TextInput(attrs={'class': 'form-control'}),
            'link_url': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'})
        }

class AboutSectionForm(forms.ModelForm):
    class Meta:
        model = AboutSection
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'paragraph1': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'paragraph2': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class AboutStatForm(forms.ModelForm):
    class Meta:
        model = AboutStat
        fields = '__all__'
        widgets = {
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'})
        }

class TrustSignalForm(forms.ModelForm):
    class Meta:
        model = TrustSignal
        fields = '__all__'
        widgets = {
            'svg_content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '<svg ...>'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'})
        }

class FooterConfigForm(forms.ModelForm):
    class Meta:
        model = FooterConfig
        fields = '__all__'
        widgets = {
            'newsletter_title': forms.TextInput(attrs={'class': 'form-control'}),
            'newsletter_text': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'company_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SocialLinkForm(forms.ModelForm):
    class Meta:
        model = SocialLink
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'icon_class': forms.HiddenInput(attrs={'id': 'iconField'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'})
        }

class FooterLinkForm(forms.ModelForm):
    class Meta:
        model = FooterLink
        fields = '__all__'
        widgets = {
            'section': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'})
        }


class CategoryForm(forms.ModelForm):
    """Form for creating/editing categories with image gallery selection"""
    
    # Hidden field to store selected default image
    default_image_choice = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Aucune (utiliser upload personnalisé)'),
            ('bijoux_simples.svg', 'Bijoux Simples'),
            ('collections.svg', 'Collections'),
            ('portraits.svg', 'Portraits'),
            ('bijoux_personnalises.svg', 'Bijoux Personnalisés'),
            ('montres.svg', 'Montres'),
            ('emballages.svg', 'Emballages'),
            ('sculptures.svg', 'Sculptures'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'default-image-radio'}),
        label="Choisir une image par défaut"
    )
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'is_active', 'order', 'shop']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bijoux Simples'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description de la catégorie...'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'id': 'customImageUpload'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'shop': forms.Select(attrs={'class': 'form-select'}),
        }


class UniverseForm(forms.ModelForm):
    class Meta:
        model = Universe
        fields = ['title', 'subtitle', 'category', 'image', 'order'] # Exclude identifier to prevent breaking JS
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optionnel (utilise le nom de la catégorie par défaut)'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Élégance intemporelle'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
