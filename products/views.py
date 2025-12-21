# products/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from accounts.decorators import manager_required
from django.utils.decorators import method_decorator
from .models import Product, Category
import zipfile
import io


@method_decorator(manager_required, name='dispatch')
class ProductListView(ListView):
    """Liste de tous les produits avec recherche et filtres"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
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
        
        # Filtre par catégorie
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
    """Créer un nouveau produit"""
    model = Product
    template_name = 'products/product_form.html'
    fields = [
        'name', 'barcode', 'category', 'purchase_price', 'selling_price',
        'current_stock', 'minimum_stock', 'is_active', 'image', 'description'
    ]
    success_url = reverse_lazy('products:product_list')
    
    def form_valid(self, form):
        form.instance.shop = self.request.user.profile.shop  # Assign Shop
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Produit "{self.object.name}" créé avec succès !',
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
                }
            })
        messages.success(self.request, f'Produit "{form.instance.name}" créé avec succès !')
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
        context['title'] = 'Nouveau produit'
        context['button_text'] = 'Créer le produit'
        return context


# ... (skipping Update/Delete as they use get_object which uses default manager, but we should probably restrict queryset too for security)
# Default queryset for Update/DeleteView uses model.objects, which is global. 
# SECURITY-CRITICAL: Must override get_queryset for Update/Delete to prevent cross-shop editing.

@method_decorator(manager_required, name='dispatch')
class ProductUpdateView(UpdateView):
    """Modifier un produit existant"""
    model = Product
    template_name = 'products/product_form.html'
    fields = [
        'name', 'barcode', 'category', 'purchase_price', 'selling_price',
        'current_stock', 'minimum_stock', 'is_active', 'image', 'description'
    ]
    success_url = reverse_lazy('products:product_list')
    
    def get_queryset(self):
        return Product.objects.filter(shop=self.request.user.profile.shop)

    def form_valid(self, form):
        messages.success(self.request, f'Produit "{form.instance.name}" modifié avec succès !')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Modifier : {self.object.name}'
        context['button_text'] = 'Enregistrer les modifications'
        return context


@method_decorator(manager_required, name='dispatch')
class ProductDeleteView(DeleteView):
    """Supprimer un produit (soft delete - désactivation)"""
    model = Product
    success_url = reverse_lazy('products:product_list')

    def get_queryset(self):
        return Product.objects.filter(shop=self.request.user.profile.shop)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Soft delete : désactiver au lieu de supprimer
        self.object.is_active = False
        self.object.save()
        messages.warning(request, f'Produit "{self.object.name}" désactivé.')
        return redirect(self.success_url)


@manager_required
def product_toggle_active(request, pk):
    """Activer/désactiver un produit"""
    # Security: filter by shop
    product = get_object_or_404(Product, pk=pk, shop=request.user.profile.shop)
    product.is_active = not product.is_active
    product.save()
    
    status = "activé" if product.is_active else "désactivé"
    messages.success(request, f'Produit "{product.name}" {status}.')
    
    return redirect('products:product_list')


# ============================================
# CATEGORY VIEWS
# ============================================

@method_decorator(manager_required, name='dispatch')
class CategoryListView(ListView):
    """Liste de toutes les catégories"""
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
    """Créer une nouvelle catégorie"""
    model = Category
    template_name = 'products/category_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('products:category_list')
    
    def form_valid(self, form):
        form.instance.shop = self.request.user.profile.shop
        messages.success(self.request, f'Catégorie "{form.instance.name}" créée avec succès !')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle catégorie'
        context['button_text'] = 'Créer la catégorie'
        return context


@method_decorator(manager_required, name='dispatch')
class CategoryUpdateView(UpdateView):
    """Modifier une catégorie existante"""
    model = Category
    template_name = 'products/category_form.html'
    fields = ['name', 'description', 'image', 'is_active', 'order']
    success_url = reverse_lazy('products:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Catégorie "{form.instance.name}" modifiée avec succès !')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Modifier : {self.object.name}'
        context['button_text'] = 'Enregistrer les modifications'
        return context


@method_decorator(manager_required, name='dispatch')
class CategoryDeleteView(DeleteView):
    """Supprimer une catégorie"""
    model = Category
    success_url = reverse_lazy('products:category_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Vérifier si des produits utilisent cette catégorie
        product_count = self.object.products.count()
        if product_count > 0:
            messages.error(
                request, 
                f'Impossible de supprimer la catégorie "{self.object.name}". '
                f'Elle est utilisée par {product_count} produit(s).'
            )
            return redirect(self.success_url)
        
        messages.warning(request, f'Catégorie "{self.object.name}" supprimée.')
        return super().delete(request, *args, **kwargs)
        messages.warning(request, f'Catégorie "{self.object.name}" supprimée.')
        return super().delete(request, *args, **kwargs)


# ============================================
# BARCODE VIEWS
# ============================================

from django.http import HttpResponse, JsonResponse
from .utils.barcode_utils import generate_barcode_image

def barcode_image_view(request, barcode_number):
    """
    Sert l'image du code-barres générée à la volée
    """
    try:
        buffer = generate_barcode_image(barcode_number)
        return HttpResponse(buffer, content_type='image/png')
    except Exception as e:
        return HttpResponse(str(e), status=500)



@manager_required
def generate_barcode_ajax(request):
    """
    Endpoint AJAX pour générer un nouveau code-barres unique
    """
    try:
        # Créer une instance temporaire pour utiliser la méthode generate_barcode
        temp_product = Product()
        code = temp_product.generate_barcode()
        return JsonResponse({'barcode': code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@manager_required
def product_bulk_action(request):
    """
    Gère les actions groupées sur les produits
    """
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_products')
        action = request.POST.get('action')
        
        if not selected_ids:
            messages.warning(request, "Aucun produit sélectionné.")
            return redirect('products:product_list')
        
        products = Product.objects.filter(id__in=selected_ids)
        
        if action == 'delete':
            # Soft delete
            count = products.count()
            products.update(is_active=False)
            messages.success(request, f"{count} produits ont été désactivés.")
            
        elif action == 'download_barcodes':
            # Créer un fichier ZIP en mémoire
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                for product in products:
                    if product.barcode:
                        # Générer l'image du code-barres
                        try:
                            image_buffer = generate_barcode_image(product.barcode)
                            # Nom du fichier : NomProduit_CodeBarre.png
                            # Nettoyer le nom du produit pour éviter les fcaractères invalides
                            safe_name = "".join([c for c in product.name if c.isalnum() or c in (' ', '-', '_')]).strip()
                            filename = f"{safe_name}_{product.barcode}.png"
                            
                            zip_file.writestr(filename, image_buffer.getvalue())
                        except Exception as e:
                            print(f"Erreur pour {product.name}: {e}")
                            continue
            
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="codes_barres_produits.zip"'
            return response
            
    return redirect('products:product_list')
