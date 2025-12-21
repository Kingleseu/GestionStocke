from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from accounts.decorators import manager_required
from .models import HeroSection, HeroCard, AboutSection, AboutStat, FooterConfig, SocialLink, FooterLink, StoreSettings, Universe, Collection
from .forms import HeroSectionForm, HeroCardForm, AboutSectionForm, AboutStatForm, FooterConfigForm, SocialLinkForm, FooterLinkForm, CategoryForm, UniverseForm, CollectionForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.db.utils import OperationalError, ProgrammingError
from products.models import Product
from products.models import Category

class SPAContextMixin:
    def get_spa_context(self, request):
        from products.models import Category
        import json
        from .models import StoreSettings, FooterConfig, SocialLink, FooterLink
        
        ctx = {}
        
        # Products
        products_qs = Product.objects.filter(is_active=True)
        products_data = []
        for product in products_qs:
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'price': float(product.selling_price),
                'image': product.image.url if product.image else '',
                'category': product.category.name if product.category else 'Divers',
                'material': 'Standard', 
                'customizable': True, 
                'stock': product.current_stock,
                'badge': 'Nouveau' if product.current_stock > 0 else 'Épuisé'
            })
        ctx['products_json'] = json.dumps(products_data)

        # Settings
        store_settings = StoreSettings.objects.first()
        settings_data = {
            'deliveryPrice': float(store_settings.delivery_fee) if store_settings else 5.99,
            'freeShippingThreshold': 100, 
            'taxRate': 0.16,
            'bannerText': '🎁 Livraison gratuite dès 100€ d\'achat',
            'bannerActive': True,
        }
        ctx['store_settings_json'] = json.dumps(settings_data)

        # Cart
        session_cart = request.session.get('cart', {})
        cart_data_js = []
        for pid, qty in session_cart.items():
            try:
                p = Product.objects.get(id=pid)
                cart_data_js.append({
                    'id': str(p.id) + '_',
                    'productId': str(p.id),
                    'name': p.name,
                    'price': float(p.selling_price),
                    'image': p.image.url if p.image else '',
                    'quantity': qty,
                    'customization': None 
                })
            except Product.DoesNotExist:
                continue
        ctx['cart_json'] = json.dumps(cart_data_js)

        # Categories (shared across nav, filtres, catalogue tabs)
        categories_qs = Category.objects.all()
        if hasattr(Category, 'is_active'):
            categories_qs = categories_qs.filter(is_active=True)
        ctx['categories'] = categories_qs
        ctx['nav_categories'] = categories_qs
        ctx['mobile_categories'] = categories_qs
        ctx['filter_categories'] = categories_qs
        

        # Footer Data
        try:
            ctx['footer_config'], _ = FooterConfig.objects.get_or_create(id=1)
            ctx['social_links'] = SocialLink.objects.all()

            # Group Footer Links
            footer_links = FooterLink.objects.all()
            ctx['footer_links_boutique'] = footer_links.filter(section='boutique')
            ctx['footer_links_help'] = footer_links.filter(section='help')
            ctx['footer_links_legal'] = footer_links.filter(section='legal')
        except (OperationalError, ProgrammingError):
            ctx['footer_config'] = None
            ctx['social_links'] = []
            ctx['footer_links_boutique'] = []
            ctx['footer_links_help'] = []
            ctx['footer_links_legal'] = []

        
        return ctx

class StoreStyleGuideView(SPAContextMixin, TemplateView):
    template_name = 'store/style_guide.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_spa_context(self.request))
        return context

class StoreCatalogView(SPAContextMixin, ListView):
    model = Product
    template_name = 'store/home.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return Product.objects.filter(Q(name__icontains=query) | Q(barcode=query), is_active=True)
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Inject SPA data
        context.update(self.get_spa_context(self.request))
        # Keep keys for template rendering if needed (categories)
        categories_qs = Category.objects.all()
        if hasattr(Category, 'is_active'):
            categories_qs = categories_qs.filter(is_active=True)
        context['categories'] = categories_qs
        context['nav_categories'] = categories_qs
        context['mobile_categories'] = categories_qs
        context['filter_categories'] = categories_qs
        

        # Dynamic Website Content
        try:
            context['hero'] = HeroSection.objects.filter(is_active=True).first()
            context['hero_cards'] = list(HeroCard.objects.all())
            context['about'] = AboutSection.objects.first()
            context['about_stats'] = list(AboutStat.objects.all())
            context['universes'] = list(Universe.objects.all())
            context['collections'] = list(Collection.objects.filter(is_active=True))
        except (OperationalError, ProgrammingError):
            context['hero'] = None
            context['hero_cards'] = []
            context['about'] = None
            context['about_stats'] = []
            context['universes'] = []

        
        return context

class StoreCartView(SPAContextMixin, TemplateView):
    template_name = 'store/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_spa_context(self.request))
        return context

class StoreCheckoutView(LoginRequiredMixin, SPAContextMixin, TemplateView):
    template_name = 'store/home.html' 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Inject SPA data so store_base.html renders correctly
        context.update(self.get_spa_context(self.request))
        return context

    def post(self, request, *args, **kwargs):
        from .models import WebOrder, WebOrderItem
        
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "Votre panier est vide.")
            return redirect('store:catalog')

        try:
            # Simple Order Creation
            order = WebOrder.objects.create(
                user=request.user,
                full_name=f"{request.POST.get('first_name')} {request.POST.get('last_name')}",
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                total_amount=0 
            )
            
            total = Decimal('0')
            for pid, qty in cart.items():
                product = Product.objects.get(id=pid)
                price = product.selling_price
                WebOrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=price
                )
                total += price * qty
            
            # Update total with tax/delivery logic if needed
            # For now just subtotal
            order.total_amount = total 
            order.save()
            
            # Clear cart
            request.session['cart'] = {}
            messages.success(request, f"Commande #{order.id} validée avec succès !")
            return redirect('store:catalog')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la commande: {str(e)}")
            return redirect('store:catalog') # Redirect to catalog (SPA) which has the data

def add_to_cart(request, product_id):
    """
    Simple session-based add to cart.
    Stock: cart = {'product_id': quantity}
    """
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    # Add or increment
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    
    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f"{product.name} ajouté au panier !")
    return redirect('store:catalog')

def sync_cart(request):
    """
    API, update session cart from JS cart data before checkout.
    Expected JSON: [{productId: 1, quantity: 2}, ...]
    """
    import json
    from django.http import JsonResponse
    from django.views.decorators.csrf import csrf_exempt

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_data = data.get('cart', [])
            
            # Rebuild session cart
            new_cart = {}
            for item in cart_data:
                pid = str(item.get('productId'))
                qty = int(item.get('quantity', 0))
                if pid and qty > 0:
                    new_cart[pid] = qty
            
            request.session['cart'] = new_cart
            request.session.modified = True
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)


# ============================================
# WEBSITE ADMINISTRATION VIEWS
# ============================================

@method_decorator(manager_required, name='dispatch')
class WebsiteDashboardView(TemplateView):
    template_name = 'store/admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hero_cards_count'] = HeroCard.objects.count()
        context['stats_count'] = AboutStat.objects.count()
        context['categories'] = Category.objects.all()
        context['universes_count'] = Universe.objects.count()
        context['collections_count'] = Collection.objects.count()
        return context


@method_decorator(manager_required, name='dispatch')
class HeroSectionUpdateView(UpdateView):
    model = HeroSection
    form_class = HeroSectionForm
    template_name = 'store/admin/hero_form.html'
    success_url = reverse_lazy('store:admin_dashboard')

    def get_object(self, queryset=None):
        # Always get the first one or create provided we enforce singleton logic
        obj, created = HeroSection.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Section Hero mise à jour avec succès.")
        return super().form_valid(form)


# --- Hero Cards ---

@method_decorator(manager_required, name='dispatch')
class HeroCardListView(ListView):
    model = HeroCard
    template_name = 'store/admin/hero_card_list.html'
    context_object_name = 'cards'


@method_decorator(manager_required, name='dispatch')
class HeroCardCreateView(CreateView):
    model = HeroCard
    form_class = HeroCardForm
    template_name = 'store/admin/hero_card_form.html'
    success_url = reverse_lazy('store:admin_hero_cards')

    def form_valid(self, form):
        messages.success(self.request, "Carte créée avec succès.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class HeroCardUpdateView(UpdateView):
    model = HeroCard
    form_class = HeroCardForm
    template_name = 'store/admin/hero_card_form.html'
    success_url = reverse_lazy('store:admin_hero_cards')

    def form_valid(self, form):
        messages.success(self.request, "Carte mise à jour avec succès.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class HeroCardDeleteView(DeleteView):
    model = HeroCard
    success_url = reverse_lazy('store:admin_hero_cards')
    template_name = 'store/admin/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "Carte supprimée.")
        return super().delete(request, *args, **kwargs)


# --- About Section ---

@method_decorator(manager_required, name='dispatch')
class AboutSectionUpdateView(UpdateView):
    model = AboutSection
    form_class = AboutSectionForm
    template_name = 'store/admin/about_form.html'
    success_url = reverse_lazy('store:admin_dashboard')

    def get_object(self, queryset=None):
        obj, created = AboutSection.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Section À Propos mise à jour.")
        return super().form_valid(form)


# --- About Stats ---

@method_decorator(manager_required, name='dispatch')
class AboutStatListView(ListView):
    model = AboutStat
    template_name = 'store/admin/about_stat_list.html'
    context_object_name = 'stats'


@method_decorator(manager_required, name='dispatch')
class AboutStatCreateView(CreateView):
    model = AboutStat
    form_class = AboutStatForm
    template_name = 'store/admin/about_stat_form.html'
    success_url = reverse_lazy('store:admin_about_stats')

    def form_valid(self, form):
        messages.success(self.request, "Statistique ajoutée.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class AboutStatUpdateView(UpdateView):
    model = AboutStat
    form_class = AboutStatForm
    template_name = 'store/admin/about_stat_form.html'
    success_url = reverse_lazy('store:admin_about_stats')

    def form_valid(self, form):
        messages.success(self.request, "Statistique mise à jour.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class AboutStatDeleteView(DeleteView):
    model = AboutStat
    success_url = reverse_lazy('store:admin_about_stats')
    template_name = 'store/admin/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "Statistique supprimée.")
        return super().delete(request, *args, **kwargs)


# ============================================
# FOOTER ADMINISTRATION
# ============================================

@method_decorator(manager_required, name='dispatch')
class FooterConfigUpdateView(UpdateView):
    model = FooterConfig
    form_class = FooterConfigForm
    template_name = 'store/admin/footer_config_form.html'
    success_url = reverse_lazy('store:admin_dashboard')

    def get_object(self, queryset=None):
        obj, created = FooterConfig.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Configuration du pied de page mise à jour.")
        return super().form_valid(form)


# --- Social Links ---

@method_decorator(manager_required, name='dispatch')
class SocialLinkListView(ListView):
    model = SocialLink
    template_name = 'store/admin/social_link_list.html'
    context_object_name = 'social_links'


@method_decorator(manager_required, name='dispatch')
class SocialLinkCreateView(CreateView):
    model = SocialLink
    form_class = SocialLinkForm
    template_name = 'store/admin/social_link_form.html'
    success_url = reverse_lazy('store:admin_social_links')

    def form_valid(self, form):
        messages.success(self.request, "Lien social ajouté.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class SocialLinkUpdateView(UpdateView):
    model = SocialLink
    form_class = SocialLinkForm
    template_name = 'store/admin/social_link_form.html'
    success_url = reverse_lazy('store:admin_social_links')

    def form_valid(self, form):
        messages.success(self.request, "Lien social mis à jour.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class SocialLinkDeleteView(DeleteView):
    model = SocialLink
    success_url = reverse_lazy('store:admin_social_links')
    template_name = 'store/admin/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "Lien social supprimé.")
        return super().delete(request, *args, **kwargs)


# --- Footer Links ---

@method_decorator(manager_required, name='dispatch')
class FooterLinkListView(ListView):
    model = FooterLink
    template_name = 'store/admin/footer_link_list.html'
    context_object_name = 'footer_links'


@method_decorator(manager_required, name='dispatch')
class FooterLinkCreateView(CreateView):
    model = FooterLink
    form_class = FooterLinkForm
    template_name = 'store/admin/footer_link_form.html'
    success_url = reverse_lazy('store:admin_footer_links')

    def form_valid(self, form):
        messages.success(self.request, "Lien pied de page ajouté.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class FooterLinkUpdateView(UpdateView):
    model = FooterLink
    form_class = FooterLinkForm
    template_name = 'store/admin/footer_link_form.html'
    success_url = reverse_lazy('store:admin_footer_links')

    def form_valid(self, form):
        messages.success(self.request, "Lien pied de page mis à jour.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class FooterLinkDeleteView(DeleteView):
    model = FooterLink
    success_url = reverse_lazy('store:admin_footer_links')
    template_name = 'store/admin/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "Lien pied de page supprimé.")
        return super().delete(request, *args, **kwargs)


# ============================================
# SETTINGS ADMINISTRATION
# ============================================

@method_decorator(manager_required, name='dispatch')
class StoreSettingsUpdateView(UpdateView):
    model = StoreSettings
    fields = ['delivery_fee'] 
    template_name = 'store/admin/settings_form.html'
    success_url = reverse_lazy('store:admin_dashboard')

    def get_object(self, queryset=None):
        obj, created = StoreSettings.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Paramètres de la boutique mis à jour.")
        return super().form_valid(form)


# ============================================
# CATEGORY ADMINISTRATION
# ============================================

@method_decorator(manager_required, name='dispatch')
class CategoryListView(ListView):
    model = Category
    template_name = 'store/admin/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # Show all categories, ordered by order field
        return Category.objects.all().order_by('order', 'name')


@method_decorator(manager_required, name='dispatch')
class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'store/admin/category_form.html'
    success_url = reverse_lazy('store:admin_categories')
    
    def form_valid(self, form):
        # Handle default image selection
        default_choice = self.request.POST.get('default_image_choice')
        if default_choice and default_choice != '':
            # Copy the default SVG to the category's image field
            import shutil
            from django.core.files import File
            from django.conf import settings
            import os
            
            source_path = os.path.join(settings.BASE_DIR, 'store', 'static', 'images', 'categories', default_choice)
            if os.path.exists(source_path):
                # Save the default image
                with open(source_path, 'rb') as f:
                    form.instance.image.save(default_choice, File(f), save=False)
        
        messages.success(self.request, f"Catégorie '{form.instance.name}' créée avec succès.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class CategoryUpdateView(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'store/admin/category_form.html'
    success_url = reverse_lazy('store:admin_categories')
    
    def form_valid(self, form):
        # Handle default image selection
        default_choice = self.request.POST.get('default_image_choice')
        if default_choice and default_choice != '':
            # Copy the default SVG to the category's image field
            import shutil
            from django.core.files import File
            from django.conf import settings
            import os
            
            source_path = os.path.join(settings.BASE_DIR, 'store', 'static', 'images', 'categories', default_choice)
            if os.path.exists(source_path):
                # Save the default image
                with open(source_path, 'rb') as f:
                    form.instance.image.save(default_choice, File(f), save=False)
        
        messages.success(self.request, f"Catégorie '{form.instance.name}' mise à jour avec succès.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class CategoryDeleteView(DeleteView):
    model = Category
    success_url = reverse_lazy('store:admin_categories')
    template_name = 'store/admin/confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        category_name = self.get_object().name
        messages.warning(request, f"Catégorie '{category_name}' supprimée.")
        return super().delete(request, *args, **kwargs)


# --- Universe (Category Navigator) ---

@method_decorator(manager_required, name='dispatch')
class UniverseListView(ListView):
    model = Universe
    template_name = 'store/admin/universe_list.html'
    context_object_name = 'universes'


@method_decorator(manager_required, name='dispatch')
class UniverseUpdateView(UpdateView):
    model = Universe
    form_class = UniverseForm
    template_name = 'store/admin/universe_form.html'
    success_url = reverse_lazy('store:admin_universes')

    def form_valid(self, form):
        messages.success(self.request, "Univers mis à jour avec succès.")
        return super().form_valid(form)


# --- Collections (Zag Style) ---

@method_decorator(manager_required, name='dispatch')
class CollectionListView(ListView):
    model = Collection
    template_name = 'store/admin/collection_list.html'
    context_object_name = 'collections'


@method_decorator(manager_required, name='dispatch')
class CollectionCreateView(CreateView):
    model = Collection
    form_class = CollectionForm
    template_name = 'store/admin/collection_form.html'
    success_url = reverse_lazy('store:admin_collections')

    def form_valid(self, form):
        messages.success(self.request, "Collection créée avec succès.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class CollectionUpdateView(UpdateView):
    model = Collection
    form_class = CollectionForm
    template_name = 'store/admin/collection_form.html'
    success_url = reverse_lazy('store:admin_collections')

    def form_valid(self, form):
        messages.success(self.request, "Collection mise à jour avec succès.")
        return super().form_valid(form)


@method_decorator(manager_required, name='dispatch')
class CollectionDeleteView(DeleteView):
    model = Collection
    success_url = reverse_lazy('store:admin_collections')
    template_name = 'store/admin/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "Collection supprimée.")
        return super().delete(request, *args, **kwargs)


@manager_required
def sync_collections(request):
    """
    Auto-creates Collections from existing Categories.
    It checks if a Collection linked to a Category exists. If not, it creates it.
    """
    categories = Category.objects.all()
    created_count = 0
    
    for category in categories:
        # Check if collection exists for this category
        if not Collection.objects.filter(category=category).exists():
            Collection.objects.create(
                category=category,
                title=category.name,
                subtitle="Découvrir", # Default subtitle
                image=category.image, # Copy image from category if possible
                is_active=True,
                order=category.order or 0
            )
            created_count += 1
            
    if created_count > 0:
        messages.success(request, f"{created_count} collections ont été générées automatiquement depuis vos catégories.")
    else:
        messages.info(request, "Vos collections sont déjà synchronisées avec vos catégories.")
        
    return redirect('store:admin_collections')
