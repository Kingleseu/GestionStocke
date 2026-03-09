# products/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from accounts.decorators import manager_required
from django.utils.decorators import method_decorator
from .models import Product, Category, CustomizableComponent, CustomizationFont, ProductCustomizationConfig, CustomizationTemplate
from .utils.barcode_utils import generate_barcode_image
import zipfile
import io
import json
import logging


logger = logging.getLogger(__name__)


@method_decorator(manager_required, name='dispatch')
class ProductListView(ListView):
    """Liste de tous les produits avec recherche et filtres"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # --- AUTO-FIX: Ensure Shapes Exist ---
        try:
            from .models import CustomizableComponent
            import os
            import shutil
            
            # Paths
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
            COMPONENTS_DIR = os.path.join(MEDIA_ROOT, 'customization', 'components')
            BRAIN_DIR = r"C:\Users\ebenn\.gemini\antigravity\brain\1a670f36-802c-4aa7-927a-13ddca681fab"
            
            if not os.path.exists(COMPONENTS_DIR):
                os.makedirs(COMPONENTS_DIR)

            # Define shapes to ensure
            shapes = [
                {"id": "dogtag", "name": "Medallion Dog Tag", "src": "uploaded_image_2_1768598060571.png", "dest": "medallion_dogtag.png"},
                {"id": "bar_curved", "name": "Medallion Curved Bar", "src": "uploaded_image_0_1768598060571.png", "dest": "medallion_bar_curved.png"},
                {"id": "cross", "name": "Medallion Cross", "src": "medallion_cross_silver_1768484430783.png", "dest": "medallion_cross_v2.png"},
                {"id": "bar_curved", "name": "Medallion Curved Bar Gold", "src": "uploaded_image_1_1768599384726.png", "dest": "medallion_bar_curved_gold.png"},
            ]
            
            for s in shapes:
                # 1. Copy File
                dest_path = os.path.join(COMPONENTS_DIR, s['dest'])
                src_path = os.path.join(BRAIN_DIR, s['src'])
                
                # FORCE COPY to ensure correct version (fix for Cherry image persistence)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"[AutoFix] Copied/Overwrote {s['dest']}")
                
                # 2. Update DB
                db_path = f"customization/components/{s['dest']}"
                comp, created = CustomizableComponent.objects.get_or_create(
                    shape_identifier=s['id'],
                    defaults={
                        "name": s['name'],
                        "component_type": "medallion",
                        "image": db_path,
                        "is_active": True
                    }
                )
                if not created:
                    # Force properties
                    if comp.image != db_path or not comp.is_active:
                        comp.image = db_path
                        comp.is_active = True
                        comp.save()
                        print(f"[AutoFix] Updated DB {s['name']}")
                        
        except Exception as e:
            print(f"[AutoFix Error] {e}")

        # --- AUTO-FIX: Ensure Fonts Exist ---
        try:
            fonts_to_sync = [
                {"name": "Dancing Script", "family": "Dancing Script"},
                {"name": "Great Vibes", "family": "Great Vibes"},
                {"name": "Playfair Display", "family": "Playfair Display"},
                {"name": "Cinzel", "family": "Cinzel"},
                {"name": "Cinzel Decorative", "family": "Cinzel Decorative"},
                {"name": "Montserrat", "family": "Montserrat"},
                {"name": "Bodoni Moda", "family": "Bodoni Moda"},
                {"name": "Lora", "family": "Lora"},
                {"name": "Italianno", "family": "Italianno"},
                {"name": "Parisienne", "family": "Parisienne"},
                {"name": "Inter", "family": "Inter"},
                {"name": "Arial", "family": "Arial"},
                {"name": "Courier New", "family": "Courier New"},
                {"name": "Myriad Pro Regular", "family": "Myriad Pro Regular"},
                {"name": "Myriad Pro Bold", "family": "Myriad Pro Bold"},
                {"name": "Myriad Pro Semibold", "family": "Myriad Pro Semibold"},
                {"name": "Myriad Pro Light", "family": "Myriad Pro Light"},
                {"name": "Myriad Pro Italic", "family": "Myriad Pro Italic"},
            ]
            for f_data in fonts_to_sync:
                CustomizationFont.objects.update_or_create(
                    name=f_data['name'],
                    defaults={'font_family': f_data['family'], 'is_active': True}
                )
        except Exception as e:
            print(f"[AutoFix Fonts Error] {e}")
        # -------------------------------------
        
        return super().dispatch(request, *args, **kwargs)

    
    def get_queryset(self):
        # Filter by Shop
        try:
            user_shop = self.request.user.profile.shop
        except (AttributeError, UserProfile.DoesNotExist):
            # Fallback for safety (though specific views should handle this)
            return Product.objects.none()
            
        if not user_shop:
            messages.error(self.request, "Vous devez avoir une boutique pour voir les produits.")
            return Product.objects.none()

        queryset = Product.objects.filter(shop=user_shop).select_related('category')
        
        # Recherche
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(barcode__icontains=search) |
                Q(category__name__icontains=search)
            )
        
        # Filtre par catÃ©gorie
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filtre par statut
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'low_stock':
            queryset = [p for p in queryset if p.is_low_stock]
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_shop = self.request.user.profile.shop
        context['categories'] = Category.objects.filter(shop=user_shop)
        # Add context for Customization Modal
        context['components'] = CustomizableComponent.objects.filter(is_active=True)
        context['fonts'] = CustomizationFont.objects.filter(is_active=True)
        context['customization_templates'] = CustomizationTemplate.objects.filter(is_active=True)
        context['search'] = self.request.GET.get('search', '')
        
        # Convert selected_category to int for proper comparison in template
        try:
            context['selected_category'] = int(self.request.GET.get('category', ''))
        except (ValueError, TypeError):
            context['selected_category'] = None
            
        context['selected_status'] = self.request.GET.get('status', '')
        
        # Statistiques
        all_products = Product.objects.filter(shop=user_shop)
        context['total_products'] = all_products.count()
        context['active_products'] = all_products.filter(is_active=True).count()
        context['low_stock_count'] = sum(1 for p in all_products if p.is_low_stock)
        
        return context


@method_decorator(manager_required, name='dispatch')
class ProductCreateView(CreateView):
    """CrÃ©er un nouveau produit"""
    model = Product
    template_name = 'products/product_form.html'
    fields = [
        'name', 'barcode', 'category', 'color_choice', 'custom_color', 'purchase_price', 'selling_price',
        'current_stock', 'minimum_stock', 'is_active', 'image', 'secondary_image', 'extra_image_1', 'extra_image_2',
        'description', 'is_customizable', 'engraving_mode', 'engraving_price'
    ]
    success_url = reverse_lazy('products:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_shop = self.request.user.profile.shop
        context['title'] = 'Nouveau Produit'
        context['button_text'] = 'CrÃ©er le produit'
        context['categories'] = Category.objects.filter(shop=user_shop)
        context['components'] = CustomizableComponent.objects.filter(is_active=True)
        context['fonts'] = CustomizationFont.objects.filter(is_active=True)
        context['customization_templates'] = CustomizationTemplate.objects.filter(is_active=True)
        context['allowed_component_ids'] = []
        context['allowed_font_ids'] = []
        return context
    
    def form_valid(self, form):
        form.instance.shop = self.request.user.profile.shop  # Assign Shop
        # If user adds a new component, force customization on
        new_comp_name = (self.request.POST.get('new_component_name') or '').strip()
        new_comp_image = self.request.FILES.get('new_component_image')
        if new_comp_name and new_comp_image:
            form.instance.is_customizable = True

        self.object = form.save()
        messages.success(self.request, f'Produit "{form.instance.name}" crÃ©Ã© avec succÃ¨s !')
        
        # Handle Customization Config
        if self.object.is_customizable:
            try:
                # Create default config if allowed components/fonts are present
                allowed_components = self.request.POST.getlist('allowed_components')
                allowed_fonts = self.request.POST.getlist('allowed_fonts')
                template_id = self.request.POST.get('customization_template')

                new_comp = None
                new_comp_name = (self.request.POST.get('new_component_name') or '').strip()
                new_comp_type = self.request.POST.get('new_component_type') or 'medallion'
                new_comp_image = self.request.FILES.get('new_component_image')
                if new_comp_name and new_comp_image:
                    new_comp = CustomizableComponent.objects.create(
                        name=new_comp_name,
                        component_type=new_comp_type,
                        image=new_comp_image,
                        is_active=True
                    )
                    allowed_components = [str(new_comp.id)]

                if allowed_components:
                    allowed_components = [allowed_components[0]]

                if allowed_components or allowed_fonts:
                    config, created = ProductCustomizationConfig.objects.get_or_create(product=self.object)
                    
                    if allowed_components:
                        config.allowed_components.set(allowed_components)
                    if allowed_fonts:
                        config.allowed_fonts.set(allowed_fonts)
                    
                    if template_id:
                         self.object.customization_template_id = template_id
                         self.object.save()

                    # Basic studio config
                    config.studio_config = {
                        "steps": ["component", "engraving"] if allowed_components else ["engraving"],
                        "initial_view": "front"
                    }
                    config.save()
            except Exception as e:
                print(f"Error saving customization config: {e}")

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Produit "{self.object.name}" crÃ©Ã© avec succÃ¨s !',
                'product': {
                    'id': self.object.id,
                    'name': self.object.name,
                    'barcode': self.object.barcode,
                    'category': self.object.category.name if self.object.category else '-',
                    'selling_price': float(self.object.selling_price),
                    'current_stock': self.object.current_stock,
                    'stock_status': self.object.stock_status,
                    'is_active': self.object.is_active,
                    'image_url': self.object.image.url if self.object.image else None,
                    'secondary_image_url': self.object.secondary_image.url if self.object.secondary_image else None,
                }
            })

        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)
    


# ... (skipping Update/Delete as they use get_object which uses default manager, but we should probably restrict queryset too for security)
# Default queryset for Update/DeleteView uses model.objects, which is global. 
# SECURITY-CRITICAL: Must override get_queryset for Update/Delete to prevent cross-shop editing.

@method_decorator(manager_required, name='dispatch')
class ProductUpdateView(UpdateView):
    """Modifier un produit existant"""
    model = Product
    template_name = 'products/product_form.html'
    fields = [
        'name', 'barcode', 'category', 'color_choice', 'custom_color', 'purchase_price', 'selling_price',
        'current_stock', 'minimum_stock', 'is_active', 'image', 'secondary_image', 'extra_image_1', 'extra_image_2',
        'description', 'is_customizable', 'engraving_mode', 'engraving_price'
    ]
    success_url = reverse_lazy('products:product_list')
    
    def get_queryset(self):
        return Product.objects.filter(shop=self.request.user.profile.shop)

    def form_valid(self, form):
        messages.success(self.request, f'Produit "{form.instance.name}" modifiÃ© avec succÃ¨s !')
        new_comp_name = (self.request.POST.get('new_component_name') or '').strip()
        new_comp_image = self.request.FILES.get('new_component_image')
        if new_comp_name and new_comp_image:
            form.instance.is_customizable = True
        self.object = form.save()

        # Handle Customization Config (Keep in sync with CreateView)
        if self.object.is_customizable:
            try:
                allowed_components = self.request.POST.getlist('allowed_components')
                allowed_fonts = self.request.POST.getlist('allowed_fonts')
                template_id = self.request.POST.get('customization_template')

                new_comp = None
                new_comp_name = (self.request.POST.get('new_component_name') or '').strip()
                new_comp_type = self.request.POST.get('new_component_type') or 'medallion'
                new_comp_image = self.request.FILES.get('new_component_image')
                if new_comp_name and new_comp_image:
                    new_comp = CustomizableComponent.objects.create(
                        name=new_comp_name,
                        component_type=new_comp_type,
                        image=new_comp_image,
                        is_active=True
                    )
                    allowed_components = [str(new_comp.id)]

                if allowed_components:
                    allowed_components = [allowed_components[0]]

                if allowed_components or allowed_fonts:
                    config, created = ProductCustomizationConfig.objects.get_or_create(product=self.object)
                    
                    if allowed_components:
                        config.allowed_components.set(allowed_components)
                    if allowed_fonts:
                        config.allowed_fonts.set(allowed_fonts)
                    
                    if template_id:
                         self.object.customization_template_id = template_id
                         self.object.save()

                    # Update/Save basic studio config
                    if not config.studio_config:
                        config.studio_config = {
                            "steps": ["component", "engraving"] if allowed_components else ["engraving"],
                            "initial_view": "front"
                        }
                    config.save()
            except Exception as e:
                print(f"Error saving customization config: {e}")

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Produit "{self.object.name}" modifiÃ© avec succÃ¨s !',
                'product': {
                    'id': self.object.id,
                    'name': self.object.name,
                    'barcode': self.object.barcode,
                    'category': self.object.category.name if self.object.category else '-',
                    'selling_price': float(self.object.selling_price),
                    'current_stock': self.object.current_stock,
                    'stock_status': self.object.stock_status,
                    'is_active': self.object.is_active,
                    'image_url': self.object.image.url if self.object.image else None,
                    'secondary_image_url': self.object.secondary_image.url if self.object.secondary_image else None,
                }
            })

        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_shop = self.request.user.profile.shop
        context['title'] = f'Modifier : {self.object.name}'
        context['button_text'] = 'Enregistrer les modifications'
        context['categories'] = Category.objects.filter(shop=user_shop)
        context['components'] = CustomizableComponent.objects.filter(is_active=True)
        context['fonts'] = CustomizationFont.objects.filter(is_active=True)
        context['customization_templates'] = CustomizationTemplate.objects.filter(is_active=True)
        
        # Add existing selections for the visual selectors
        try:
            config = ProductCustomizationConfig.objects.get(product=self.object)
            allowed_ids = [str(id) for id in config.allowed_components.values_list('id', flat=True)]
            context['allowed_component_ids'] = allowed_ids[:1]
            context['allowed_font_ids'] = [str(id) for id in config.allowed_fonts.values_list('id', flat=True)]
        except ProductCustomizationConfig.DoesNotExist:
            context['allowed_component_ids'] = []
            context['allowed_font_ids'] = []
            
        return context


@manager_required
def product_details_ajax(request, pk):
    """Return product details for edit modal prefill."""
    product = get_object_or_404(Product, pk=pk, shop=request.user.profile.shop)

    allowed_component_ids = []
    allowed_font_ids = []
    customization_template_id = None
    try:
        config = ProductCustomizationConfig.objects.get(product=product)
        allowed_component_ids = list(config.allowed_components.values_list('id', flat=True))
        allowed_font_ids = list(config.allowed_fonts.values_list('id', flat=True))
    except ProductCustomizationConfig.DoesNotExist:
        pass

    if product.customization_template_id:
        customization_template_id = product.customization_template_id

    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name or '',
            'barcode': product.barcode or '',
            'category': product.category_id,
            'purchase_price': str(product.purchase_price or '0'),
            'selling_price': str(product.selling_price or '0'),
            'engraving_price': str(product.engraving_price or '0'),
            'current_stock': product.current_stock,
            'minimum_stock': product.minimum_stock,
            'color_choice': product.color_choice or 'argent',
            'custom_color': product.custom_color or '',
            'is_active': bool(product.is_active),
            'is_customizable': bool(product.is_customizable),
            'engraving_mode': product.engraving_mode or 'text',
            'allowed_component_ids': allowed_component_ids,
            'allowed_font_ids': allowed_font_ids,
            'customization_template_id': customization_template_id,
        }
    })



@method_decorator(manager_required, name='dispatch')
class ProductDeleteView(DeleteView):
    """Supprimer un produit (soft delete - dÃ©sactivation)"""
    model = Product
    success_url = reverse_lazy('products:product_list')

    def get_queryset(self):
        return Product.objects.filter(shop=self.request.user.profile.shop)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.warning(request, f'Produit "{self.object.name}" supprim?.')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect(self.success_url)
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # No confirmation page: redirect back to list
        messages.info(request, "Confirmez la suppression depuis la liste des produits.")
        return redirect(self.success_url)


@manager_required
def product_toggle_active(request, pk):
    """Activer/dÃ©sactiver un produit"""
    # Security: filter by shop
    product = get_object_or_404(Product, pk=pk, shop=request.user.profile.shop)
    product.is_active = not product.is_active
    product.save()
    
    status = "activÃ©" if product.is_active else "dÃ©sactivÃ©"
    messages.success(request, f'Produit "{product.name}" {status}.')
    
    return redirect('products:product_list')


# ============================================
# CATEGORY VIEWS
# ============================================

@method_decorator(manager_required, name='dispatch')
class CategoryListView(ListView):
    """Liste de toutes les catÃ©gories"""
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        return Category.objects.filter(shop=self.request.user.profile.shop)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['total_categories'] = Category.objects.filter(shop=self.request.user.profile.shop).count()
        return context


@method_decorator(manager_required, name='dispatch')
class CategoryCreateView(CreateView):
    """CrÃ©er une nouvelle catÃ©gorie"""
    model = Category
    template_name = 'products/category_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('products:category_list')
    
    def form_valid(self, form):
        form.instance.shop = self.request.user.profile.shop
        messages.success(self.request, f'CatÃ©gorie "{form.instance.name}" crÃ©Ã©e avec succÃ¨s !')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle catÃ©gorie'
        context['button_text'] = 'CrÃ©er la catÃ©gorie'
        return context


@method_decorator(manager_required, name='dispatch')
class CategoryUpdateView(UpdateView):
    """Modifier une catÃ©gorie existante"""
    model = Category
    template_name = 'products/category_form.html'
    fields = ['name', 'description', 'image', 'is_active', 'order']
    success_url = reverse_lazy('products:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'CatÃ©gorie "{form.instance.name}" modifiÃ©e avec succÃ¨s !')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Modifier : {self.object.name}'
        context['button_text'] = 'Enregistrer les modifications'
        return context


@method_decorator(manager_required, name='dispatch')
class CategoryDeleteView(DeleteView):
    """Supprimer une catÃ©gorie"""
    model = Category
    success_url = reverse_lazy('products:category_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.warning(request, f'Produit "{self.object.name}" supprim?.')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect(self.success_url)
def barcode_image_view(request, barcode_number):
    """
    Sert l'image du code-barres gÃ©nÃ©rÃ©e Ã  la volÃ©e
    """
    try:
        buffer = generate_barcode_image(barcode_number)
        return HttpResponse(buffer.getvalue(), content_type='image/png')
    except Exception as e:
        return HttpResponse(str(e), status=500)



@manager_required
def generate_barcode_ajax(request):
    """
    Endpoint AJAX pour gÃ©nÃ©rer un nouveau code-barres unique
    """
    try:
        # CrÃ©er une instance temporaire pour utiliser la mÃ©thode generate_barcode
        temp_product = Product()
        code = temp_product.generate_barcode()
        return JsonResponse({'barcode': code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@manager_required
def create_component_ajax(request):
    """Endpoint AJAX pour crÃ©er un CustomizableComponent depuis le modal produit"""
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©thode non autorisÃ©e'}, status=405)

    name = (request.POST.get('new_component_name') or '').strip()
    comp_type = request.POST.get('new_component_type') or 'medallion'
    image = request.FILES.get('new_component_image')

    if not name or not image:
        return JsonResponse({'error': 'Nom et image requis'}, status=400)

    try:
        comp = CustomizableComponent.objects.create(
            name=name,
            component_type=comp_type,
            image=image,
            is_active=True
        )

        return JsonResponse({
            'success': True,
            'component': {
                'id': comp.id,
                'name': comp.name,
                'image_url': comp.image.url if comp.image else None,
                'shape_identifier': comp.shape_identifier or ''
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@manager_required
def delete_component_ajax(request):
    """AJAX endpoint to delete (soft-delete) a component by id"""
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©thode non autorisÃ©e'}, status=405)

    comp_id = request.POST.get('component_id')
    if not comp_id:
        return JsonResponse({'error': 'component_id requis'}, status=400)

    try:
        comp = CustomizableComponent.objects.filter(id=comp_id).first()
        if not comp:
            return JsonResponse({'error': 'Composant introuvable'}, status=404)

        # Soft delete: mark inactive
        comp.is_active = False
        comp.save()
        return JsonResponse({'success': True, 'id': comp_id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@manager_required
def bulk_delete_components_ajax(request):
    """AJAX endpoint to bulk-delete components (soft-delete)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©thode non autorisÃ©e'}, status=405)

    ids = request.POST.getlist('component_ids[]') or request.POST.getlist('component_ids')
    if not ids:
        return JsonResponse({'error': 'Aucun id fourni'}, status=400)

    try:
        qs = CustomizableComponent.objects.filter(id__in=ids)
        count = qs.update(is_active=False)
        return JsonResponse({'success': True, 'deleted_count': count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@manager_required
def product_bulk_action(request):
    """
    GÃ¨re les actions groupÃ©es sur les produits
    """
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_products')
        action = request.POST.get('action')
        
        if not selected_ids:
            messages.warning(request, "Aucun produit sÃ©lectionnÃ©.")
            return redirect('products:product_list')
        
        products = Product.objects.filter(id__in=selected_ids)
        
        if action == 'delete':
            # Soft delete
            count = products.count()
            products.update(is_active=False)
            messages.success(request, f"{count} produits ont Ã©tÃ© dÃ©sactivÃ©s.")
            
        elif action == 'download_barcodes':
            # CrÃ©er un fichier ZIP en mÃ©moire
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                for product in products:
                    if product.barcode:
                        # GÃ©nÃ©rer l'image du code-barres
                        try:
                            image_buffer = generate_barcode_image(product.barcode)
                            # Nom du fichier : NomProduit_CodeBarre.png
                            # Nettoyer le nom du produit pour Ã©viter les fcaractÃ¨res invalides
                            safe_name = "".join([c for c in product.name if c.isalnum() or c in (' ', '-', '_')]).strip()
                            filename = f"{safe_name}_{product.barcode}.png"
                            
                            zip_file.writestr(filename, image_buffer.getvalue())
                        except Exception as e:
                            print(f"Erreur pour {product.name}: {e}")
                            continue
            
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="codes_barres_produits.zip"'
            return response
            
    return redirect('products:product_list')


@manager_required
def get_product_customization_data(request, product_id):
    """
    AJAX endpoint to get authorized components and fonts for a product.
    Returns JSON with components and fonts data.
    Manager endpoint - for admin panel
    """
    def _safe_media_url(file_field):
        if not file_field:
            return None
        try:
            return file_field.url
        except Exception:
            return None

    try:
        product = Product.objects.get(id=product_id, shop=request.user.profile.shop)
        config = ProductCustomizationConfig.objects.filter(product=product).first()

        components_data = []
        fonts_data = []

        if config:
            for comp in config.allowed_components.filter(is_active=True):
                components_data.append({
                    'id': comp.id,
                    'name': comp.name,
                    'image_url': _safe_media_url(comp.image),
                    'shape_identifier': comp.shape_identifier or ''
                })

            for font in config.allowed_fonts.filter(is_active=True):
                fonts_data.append({
                    'id': font.id,
                    'name': font.name,
                    'font_family': font.font_family
                })

        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'product_name': product.name,
            'product_image': _safe_media_url(product.image),
            'engraving_mode': getattr(product, 'engraving_mode', 'text'),
            'engraving_price': float(product.engraving_price),
            'components': components_data,
            'fonts': fonts_data
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produit non trouve'}, status=404)
    except Exception:
        logger.exception('Admin customization-data failed for product_id=%s', product_id)
        return JsonResponse(
            {'success': False, 'error': 'Erreur serveur lors du chargement de la personnalisation'},
            status=500,
        )


def get_product_customization_data_public(request, product_id):
    """
    AJAX endpoint to get authorized components and fonts for a product.
    Returns JSON with components and fonts data.
    PUBLIC endpoint - accessible without authentication
    """
    def _safe_media_url(file_field):
        if not file_field:
            return None
        try:
            return file_field.url
        except Exception:
            return None

    try:
        product = Product.objects.get(id=product_id, is_active=True)
        config = ProductCustomizationConfig.objects.filter(product=product).first()

        components_data = []
        fonts_data = []

        if config:
            for comp in config.allowed_components.filter(is_active=True):
                components_data.append({
                    'id': comp.id,
                    'name': comp.name,
                    'image_url': _safe_media_url(comp.image),
                    'shape_identifier': comp.shape_identifier or ''
                })

            for font in config.allowed_fonts.filter(is_active=True):
                fonts_data.append({
                    'id': font.id,
                    'name': font.name,
                    'font_family': font.font_family
                })

        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'product_name': product.name,
            'product_image': _safe_media_url(product.image),
            'engraving_mode': getattr(product, 'engraving_mode', 'text'),
            'engraving_price': float(product.engraving_price),
            'components': components_data,
            'fonts': fonts_data
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produit non trouve'}, status=404)
    except Exception:
        logger.exception('Public customization-data failed for product_id=%s', product_id)
        return JsonResponse(
            {'success': False, 'error': 'Erreur serveur lors du chargement de la personnalisation'},
            status=500,
        )
