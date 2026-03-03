from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from accounts.decorators import manager_required
from .models import HeroSection, HeroCard, AboutSection, AboutStat, FooterConfig, SocialLink, FooterLink, StoreSettings, Universe, Collection, WebOrder, ManualPayment
from accounts.models import Shop
from .forms import HeroSectionForm, HeroCardForm, AboutSectionForm, AboutStatForm, FooterConfigForm, SocialLinkForm, FooterLinkForm, CategoryForm, UniverseForm, CollectionForm, ShopForm, ManualPaymentForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.db.utils import OperationalError, ProgrammingError
from products.models import Product
from products.models import Product, Category
from products.services import CustomizationService
import json

class SPAContextMixin:
    def get_spa_context(self, request):
        from products.models import Category
        import json
        from .models import StoreSettings, FooterConfig, SocialLink, FooterLink
        
        ctx = {}
        
        # Products - Order by newest first
        products_qs = Product.objects.filter(is_active=True).order_by('-id')
        products_data = []
        for product in products_qs:
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'price': float(product.selling_price),
                'image': product.image.url if product.image else '',
                'secondary_image': product.secondary_image.url if product.secondary_image else '',
                'mockup_image': product.mockup_image.url if product.mockup_image else '',
                'category': product.category.name if product.category else 'Divers',
                'color_choice': product.color_choice,
                'custom_color': product.custom_color or '',
                'color': product.custom_color if product.color_choice == 'autre' and product.custom_color else product.get_color_choice_display(),
                'material': 'Standard', 
                'customizable': product.is_customizable, 
                'engraving_mode': product.engraving_mode,
                'engraving_price': float(product.engraving_price),
                'customization_rules': CustomizationService.get_product_rules(product),
                'production_delay': product.production_delay_days,
                'stock': product.current_stock,
                'badge': 'Nouveau' if product.current_stock > 0 else 'Épuisé'
            })
        ctx['products_json'] = json.dumps(products_data)

        # Settings
        store_settings = StoreSettings.objects.first()
        settings_data = {
            'deliveryPrice': float(store_settings.delivery_fee) if store_settings else 5.99,
            'freeShippingThreshold': 100000, 
            'taxRate': 0.16,
            'bannerText': '🎁 Livraison gratuite dès 100 000 FC d\'achat',
            'bannerActive': True,
        }
        ctx['store_settings_json'] = json.dumps(settings_data)

        # Cart
        session_cart = request.session.get('cart', {})
        cart_data_js = []
        for key, item_data in session_cart.items():
            try:
                # Handle both legacy (int) and new (complex key) entries
                # New structure: key -> { 'product_id': 1, 'quantity': 1, 'customization': ... }
                # OR key -> qty (legacy)
                
                if isinstance(item_data, dict):
                    pid = item_data.get('product_id')
                    qty = item_data.get('quantity')
                    customization = item_data.get('customization')
                else:
                    # Legacy: key is pid, value is qty
                    pid = key
                    qty = item_data
                    customization = None
                
                # Retrieve product
                # Clean pid if it comes from composite key (though if dict, we likely stored explicit pid)
                 # Safety check
                if not pid: continue

                p = Product.objects.get(id=pid)
                cart_data_js.append({
                    'id': key, # Use the unique key
                    'productId': str(p.id),
                    'name': p.name,
                    'price': float(p.selling_price) + float(customization.get('extra_cost', 0) if customization else 0),
                    'image': p.image.url if p.image else '',
                    'quantity': qty,
                    'customization': customization 
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
        context['active_view'] = 'checkout'
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
                # ... existing fields ...
                full_name=f"{request.POST.get('first_name')} {request.POST.get('last_name')}",
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                total_amount=0 
            )
            
            total = Decimal('0')
            total = Decimal('0')
            for key, item_data in cart.items():
                # Handle new vs legacy cart structure
                if isinstance(item_data, dict):
                    pid = item_data.get('product_id')
                    qty = item_data.get('quantity')
                    customization = item_data.get('customization')
                else:
                    # Legacy
                    pid = key.split('_')[0] if '_' in key else key
                    qty = item_data
                    customization = None

                if not pid: continue

                product = Product.objects.get(id=pid)
                # Calculate price including customization
                base_price = product.selling_price
                extra_cost = Decimal(str(customization.get('extra_cost', 0))) if customization else Decimal('0')
                final_price = base_price + extra_cost

                # Create item
                order_item = WebOrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=final_price,
                    customization_data=customization
                )
                
                # Persist preview image and production data if available
                if customization:
                    try:
                        from products.services import CustomizationService
                        order_item.production_data = CustomizationService.generate_production_data(product, customization)
                        order_item.save()

                        # --- DEFINITIVE MEDIA PERSISTENCE ---
                        preview_saved = False
                        
                        # 1. Handle generated PREVIEW (Base64 is preferred for the 'actual result')
                        b64_preview = customization.get('preview')
                        if b64_preview and isinstance(b64_preview, str) and ';base64,' in b64_preview:
                            from django.core.files.base import ContentFile
                            import base64
                            try:
                                format, imgstr = b64_preview.split(';base64,')
                                ext = format.split('/')[-1]
                                data = ContentFile(base64.b64decode(imgstr), name=f"preview_order_{order.id}_{order_item.id}.{ext}")
                                order_item.preview_image.save(data.name, data, save=True)
                                preview_saved = True
                            except Exception as e:
                                print(f"B64 Preview save failed: {e}")

                        # Fallback to preview_id if B64 failed/missing
                        if not preview_saved and customization.get('preview_id'):
                            from products.models import CustomizationPreview
                            try:
                                preview_obj = CustomizationPreview.objects.get(id=customization['preview_id'])
                                if preview_obj.preview_image:
                                    order_item.preview_image.save(
                                        preview_obj.preview_image.name,
                                        preview_obj.preview_image.file,
                                        save=True
                                    )
                                    preview_saved = True
                            except: pass

                        # 2. Handle CLIENT'S ORIGINAL PHOTO (Crucial for workshop)
                        choices = customization.get('choices', {})
                        client_img_data = None
                        # Broad search for any uploaded image key
                        for key in ['recto', 'verso', 'studio_engraving', 'image_upload', 'image']:
                            side = choices.get(key)
                            if isinstance(side, dict):
                                client_img_data = side.get('image_data') or side.get('url') or side.get('file') or side.get('image_preview')
                                if client_img_data and isinstance(client_img_data, str) and len(client_img_data) > 100:
                                    break
                            elif isinstance(side, str) and len(side) > 100:
                                client_img_data = side
                                break
                        
                        if client_img_data and isinstance(client_img_data, str):
                            from django.core.files.base import ContentFile
                            import base64
                            if ';base64,' in client_img_data:
                                try:
                                    format, imgstr = client_img_data.split(';base64,')
                                    ext = format.split('/')[-1]
                                    data = ContentFile(base64.b64decode(imgstr), name=f"client_photo_{order.id}_{order_item.id}.{ext}")
                                    order_item.client_image.save(data.name, data, save=True)
                                except Exception as e:
                                    print(f"Client image save failed: {e}")
                                # (URL handling omitted for now as Base64 covers 99% of Studio uploads)

                    except Exception as e:
                        print(f"Error persisting production/preview data: {e}")
                total += final_price * qty
            
            # Update total with tax/delivery logic if needed
            # For now just subtotal
            order.total_amount = total 
            order.save()
            
            # Clear cart
            request.session['cart'] = {}
            messages.success(request, f"Commande #{order.id} enregistrée. Veuillez suivre les instructions pour le paiement.")
            return redirect('store:payment_instructions', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la commande: {str(e)}")
            return redirect('store:catalog') # Redirect to catalog (SPA) which has the data

class StoreProductDetailView(SPAContextMixin, TemplateView):
    template_name = 'store/product_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('pk')
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        
        context['product'] = product
        context.update(self.get_spa_context(self.request))
        
        # Inject customization rules directly for template usage
        if product.is_customizable and product.effective_customization_rules:
             import json
             context['customization_rules_json'] = json.dumps(product.effective_customization_rules)

        # Similar Products
        if product.category:
            context['similar_products'] = Product.objects.filter(
                category=product.category, 
                is_active=True
            ).exclude(id=product.id).order_by('-id')[:4]
        else:
            context['similar_products'] = Product.objects.filter(
                is_active=True
            ).exclude(id=product.id).order_by('-id')[:4]
        
        return context

class StoreStudioView(SPAContextMixin, TemplateView):
    template_name = 'store/studio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('pk')
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        
        context['product'] = product
        context.update(self.get_spa_context(self.request))
        
        # Inject customization rules directly
        if product.is_customizable and product.effective_customization_rules:
             import json
             context['customization_rules_json'] = json.dumps(product.effective_customization_rules)
        
        return context

def add_to_cart(request, product_id):
    """
    Handle adding items to cart.
    Supports simple GET (legacy) and POST (customization).
    """
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    if request.method == 'POST':
        # Customization Flow
        try:
            data = json.loads(request.body)
            user_customization = data.get('customization', {})
            
            # Validate
            if product.is_customizable:
                try:
                    CustomizationService.validate_customization_data(product, user_customization)
                    # Recalculate price for security
                    extra_cost = CustomizationService.calculate_customization_price(product, user_customization)
                    user_customization['extra_cost'] = float(extra_cost)
                    
                    # Generate Backend Preview
                    preview_file = CustomizationService.generate_preview_image(product, user_customization)
                    if preview_file:
                        from products.models import CustomizationPreview
                        preview_obj = CustomizationPreview.objects.create(
                            product=product,
                            customization_data=user_customization,
                            preview_image=preview_file
                        )
                        user_customization['preview_url'] = preview_obj.preview_image.url
                        user_customization['preview_id'] = preview_obj.id
                except Exception as e:
                     return JsonResponse({'success': False, 'error': str(e)}, status=400)
            else:
                user_customization = None

            # Generate Unique Key based on options
            # Using simple hashing of JSON string to distinguish different customizations of same product
            import hashlib
            cust_str = json.dumps(user_customization, sort_keys=True)
            cust_hash = hashlib.md5(cust_str.encode()).hexdigest()[:8]
            cart_key = f"{product_id}_{cust_hash}"
            
            if cart_key in cart:
                if isinstance(cart[cart_key], dict):
                    cart[cart_key]['quantity'] += 1
                else:
                     cart[cart_key] = {'product_id': str(product_id), 'quantity': 1, 'customization': user_customization}
            else:
                cart[cart_key] = {
                    'product_id': str(product_id),
                    'quantity': 1,
                    'customization': user_customization
                }
            
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, f"{product.name} ajouté !")
            return JsonResponse({'success': True})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': "Invalid JSON"}, status=400)

    else:
        # Legacy GET Flow (Simple Product)
        # Use ProductID as key if no customization
        key = str(product_id)
        if key in cart:
            if isinstance(cart[key], dict):
                 cart[key]['quantity'] += 1
            else:
                 cart[key] += 1
        else:
            # Store as simplified legacy or new format? Let's use new format for consistency from now on
            cart[key] = {'product_id': product_id, 'quantity': 1, 'customization': None}
        
        request.session['cart'] = cart
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
                # Handle complex item object: { productId, quantity, customization, id (optional) }
                pid = str(item.get('productId'))
                qty = int(item.get('quantity', 0))
                customization = item.get('customization')
                
                if pid and qty > 0:
                    # Generate a unique key for this combination
                    import hashlib
                    cust_str = json.dumps(customization, sort_keys=True)
                    cust_hash = hashlib.md5(cust_str.encode()).hexdigest()[:8]
                    cart_key = f"{pid}_{cust_hash}"
                    
                    if customization and not customization.get('preview_url'):
                        # Try to generate preview if missing
                        preview_file = CustomizationService.generate_preview_image(Product.objects.get(id=pid), customization)
                        if preview_file:
                            from products.models import CustomizationPreview
                            preview_obj = CustomizationPreview.objects.create(
                                product=Product.objects.get(id=pid),
                                customization_data=customization,
                                preview_image=preview_file
                            )
                            customization['preview_url'] = preview_obj.preview_image.url
                            customization['preview_id'] = preview_obj.id

                    new_cart[cart_key] = {
                        'product_id': pid,
                        'quantity': qty,
                        'customization': customization
                    }
            
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
        context['pending_payments_count'] = ManualPayment.objects.filter(status='submitted').count()
        context['shop'] = self.request.user.profile.shop
        return context

@method_decorator(manager_required, name='dispatch')
class ShopUpdateView(UpdateView):
    model = Shop
    form_class = ShopForm
    template_name = 'store/admin/shop_form.html'
    success_url = reverse_lazy('store:admin_dashboard')

    def get_object(self, queryset=None):
        return self.request.user.profile.shop

    def form_valid(self, form):
        messages.success(self.request, "Informations de la boutique mises à jour.")
        return super().form_valid(form)


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


# ============================================
# MANUAL PAYMENT PROCESS
# ============================================

class ManualPaymentInstructionsView(LoginRequiredMixin, SPAContextMixin, TemplateView):
    template_name = 'store/payment_instructions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(WebOrder, id=order_id, user=self.request.user)
        
        context['order'] = order
        context.update(self.get_spa_context(self.request))
        return context

class ManualPaymentSubmissionView(LoginRequiredMixin, SPAContextMixin, CreateView):
    model = ManualPayment
    form_class = ManualPaymentForm
    template_name = 'store/payment_submission.html'

    def dispatch(self, request, *args, **kwargs):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(WebOrder, id=order_id, user=self.request.user)
        
        # Prevent multiple submissions if already submitted or approved
        if hasattr(order, 'manual_payment') and order.manual_payment.status in ['submitted', 'approved']:
            messages.info(request, "Vous avez déjà soumis une preuve de paiement pour cette commande.")
            return redirect('store:catalog')
            
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('order_id')
        context['order'] = get_object_or_404(WebOrder, id=order_id, user=self.request.user)
        context.update(self.get_spa_context(self.request))
        return context

    def form_valid(self, form):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(WebOrder, id=order_id, user=self.request.user)
        
        form.instance.order = order
        form.instance.user = self.request.user
        form.instance.status = 'submitted'
        
        # Update Order Status
        order.status = 'awaiting_verification'
        order.save()
        
        messages.success(self.request, "Votre preuve de paiement a été envoyée. Nous allons la vérifier sous peu.")
        form.save()
        return redirect('store:catalog')

# ============================================
# ADMIN PAYMENT VERIFICATION
# ============================================

@method_decorator(manager_required, name='dispatch')
class AdminPaymentListView(ListView):
    model = ManualPayment
    template_name = 'store/admin/payment_list.html'
    context_object_name = 'payments'
    
    def get_queryset(self):
        return ManualPayment.objects.filter(status='submitted').order_by('-created_at')

@manager_required
def approve_payment(request, pk):
    payment = get_object_or_404(ManualPayment, pk=pk)
    payment.status = 'approved'
    payment.verified_at = timezone.now() if 'timezone' in globals() else None
    payment.save()
    
    # Update Order
    order = payment.order
    order.status = 'paid'
    order.save()
    
    messages.success(request, f"Paiement pour commande #{order.id} approuvé.")
    return redirect('store:admin_payments')

@manager_required
def reject_payment(request, pk):
    payment = get_object_or_404(ManualPayment, pk=pk)
    reason = request.POST.get('reason', 'Référence ou preuve invalide.')
    
    payment.status = 'rejected'
    payment.rejection_reason = reason
    payment.save()
    
    # Update Order
    order = payment.order
    order.status = 'pending_payment'
    order.save()
    
    messages.warning(request, f"Paiement pour commande #{order.id} rejeté.")
    return redirect('store:admin_payments')

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


@method_decorator(manager_required, name='dispatch')
class UniverseDeleteView(DeleteView):
    model = Universe
    success_url = reverse_lazy('store:admin_universes')
    template_name = 'store/admin/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"L'univers '{obj.title}' a été supprimé.")
        return super().delete(request, *args, **kwargs)


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
    If duplicates exist (multiple collections for one category), they are automatically removed.
    """
    categories = Category.objects.all()
    created_count = 0
    deleted_count = 0
    
    for category in categories:
        existing = Collection.objects.filter(category=category).order_by('id')
        
        # Deduplication: keep only the first one, delete others
        if existing.count() > 1:
            to_delete = existing[1:]
            deleted_count += to_delete.count()
            for obj in to_delete:
                obj.delete()
        
        # Creation: only if none exists
        if not existing.exists():
            Collection.objects.create(
                category=category,
                title=category.name,
                subtitle="Découvrir",
                image=category.image,
                is_active=True,
                order=category.order or 0
            )
            created_count += 1
            
    msg = []
    if created_count > 0:
        msg.append(f"{created_count} collections générées")
    if deleted_count > 0:
        msg.append(f"{deleted_count} doublons supprimés")
        
    if msg:
        messages.success(request, " - ".join(msg) + ".")
    else:
        messages.info(request, "Vos collections sont déjà parfaitement synchronisées.")
        
    return redirect('store:admin_collections')


@manager_required
def sync_universes(request):
    """
    Auto-creates Universes (Category Navigator items) from existing Categories.
    If duplicates exist (multiple universes for one category), they are automatically removed.
    """
    categories = Category.objects.all()
    created_count = 0
    deleted_count = 0
    
    for category in categories:
        existing = Universe.objects.filter(category=category).order_by('id')
        
        # Deduplication: keep only the first one, delete others
        if existing.count() > 1:
            to_delete = existing[1:]
            deleted_count += to_delete.count()
            for obj in to_delete:
                obj.delete()
        
        # Creation: only if none exists
        if not existing.exists():
            identifier = category.name.upper().replace(' ', '_')
            base_identifier = identifier
            counter = 1
            while Universe.objects.filter(identifier=identifier).exists():
                identifier = f"{base_identifier}_{counter}"
                counter += 1

            Universe.objects.create(
                category=category,
                title=category.name,
                subtitle="", 
                image=category.image, 
                identifier=identifier,
                order=category.order or 0
            )
            created_count += 1
            
    msg = []
    if created_count > 0:
        msg.append(f"{created_count} univers générés")
    if deleted_count > 0:
        msg.append(f"{deleted_count} doublons supprimés")
        
    if msg:
        messages.success(request, " - ".join(msg) + ".")
    else:
        messages.info(request, "Tous vos univers sont déjà parfaitement synchronisés.")
        
    return redirect('store:admin_universes')


# ============================================
# WEB ORDERS MANAGEMENT VIEWS
# ============================================

@method_decorator(manager_required, name='dispatch')
class WebOrderListView(ListView):
    """Liste des commandes web avec filtres"""
    model = WebOrder
    template_name = 'store/admin/weborder_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = WebOrder.objects.all().prefetch_related(
            'items__product', 'manual_payment'
        ).order_by('-created_at')
        
        # Filtres
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        has_custom = self.request.GET.get('has_custom')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(id__icontains=search)
            )
        
        if has_custom == 'yes':
            queryset = queryset.filter(items__customization_data__isnull=False).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = WebOrder.STATUS_CHOICES
        context['total_orders'] = WebOrder.objects.count()
        context['pending_orders'] = WebOrder.objects.filter(status='pending_payment').count()
        context['awaiting_verification_count'] = WebOrder.objects.filter(status='awaiting_verification').count()
        context['paid_orders_count'] = WebOrder.objects.filter(status='paid').count()
        context['customized_orders'] = WebOrder.objects.filter(
            items__customization_data__isnull=False
        ).distinct().count()
        context['pending_payment_count'] = ManualPayment.objects.filter(status='submitted').count()
        
        # Filtres actifs
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')
        context['current_has_custom'] = self.request.GET.get('has_custom', '')
        
        return context


@method_decorator(manager_required, name='dispatch')
class WebOrderDetailView(TemplateView):
    """Détail d'une commande web avec personnalisations"""
    template_name = 'store/admin/weborder_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get('pk')
        order = get_object_or_404(WebOrder.objects.prefetch_related('items__product'), id=order_id)
        
        # Préparer les items avec détails de personnalisation
        items_with_details = []
        for item in order.items.all():
            item_data = {
                'item': item,
                'has_customization': bool(item.customization_data),
                'customization_details': self._parse_customization(item.customization_data, item.product)
            }
            items_with_details.append(item_data)
        
        # Récupérer la preuve de paiement si elle existe
        manual_payment = getattr(order, 'manual_payment', None)
        
        context['order'] = order
        context['items_with_details'] = items_with_details
        context['status_choices'] = WebOrder.STATUS_CHOICES
        context['manual_payment'] = manual_payment
        
        return context
    
    def _parse_customization(self, customization_data, product):
        """Parse customization data pour affichage lisible"""
        if not customization_data:
            return None
        
        is_studio_format = customization_data.get('is_studio', False)
        # S'il y a un sous-dictionnaire "choices", on le traite comme du format studio
        if not is_studio_format and 'choices' in customization_data and isinstance(customization_data['choices'], dict):
            is_studio_format = True

        details = {
            'is_studio': is_studio_format,
            'extra_cost': customization_data.get('extra_cost', 0),
            'preview': customization_data.get('preview'),
            'choices': {},
            'raw_choices': []
        }
        
        if is_studio_format:
            choices = customization_data.get('choices', {})
            
            # Gravure
            if 'studio_engraving' in choices:
                eng = choices['studio_engraving']
                if eng and eng.get('text'):
                    details['choices']['engraving'] = {
                        'text': eng.get('text', ''),
                        'font': eng.get('font', 'N/A'),
                        'label': 'Gravure'
                    }
            
            # Composant
            if 'studio_component' in choices:
                comp_value = choices['studio_component']
                comp_label = comp_value
                if product and hasattr(product, 'customization_rules') and product.customization_rules:
                    zones = product.customization_rules.get('zones', [])
                    for zone in zones:
                        if zone.get('id') == 'studio_component':
                            for option in zone.get('options', []):
                                if option.get('value') == comp_value:
                                    comp_label = option.get('label', comp_value)
                                    break
                
                details['choices']['component'] = {
                    'value': comp_value,
                    'label': comp_label,
                    'display_label': 'Composant'
                }
            
            # Autres choix studio (recto, verso, images, etc.)
            for k, v in choices.items():
                if k not in ['studio_engraving', 'studio_component']:
                    label = str(k).replace('studio_', '').replace('_', ' ').capitalize()
                    
                    if isinstance(v, dict):
                        # Ignorer s'il est explicitement marqué comme inactif
                        if 'active' in v and not v.get('active'):
                            continue
                            
                        # Reconstruire un texte lisible depuis le dictionnaire
                        txt_parts = []
                        if v.get('text'):
                            txt_parts.append(f"Texte: « {v.get('text')} » (Police: {v.get('font', 'N/A')})")
                        if v.get('image_data'):
                            txt_parts.append("Image fournie")
                        
                        v_str = " / ".join(txt_parts) if txt_parts else "Sélectionné"
                    else:
                        v_str = str(v)
                        
                    details['raw_choices'].append({
                        'label': label,
                        'value': v_str
                    })
        else:
            # Ancien système ou personnalisation hors-studio
            for k, v in customization_data.items():
                if k not in ['is_studio', 'extra_cost', 'preview']:
                    if isinstance(v, dict) and 'text' in v:
                        v_str = f"{v.get('text')} (Police: {v.get('font', 'N/A')})"
                    else:
                        v_str = str(v)
                    details['raw_choices'].append({
                        'label': str(k).replace('_', ' ').capitalize(),
                        'value': v_str
                    })
        
        return details


@manager_required
def update_order_status(request, pk):
    """Mettre à jour le statut d'une commande"""
    if request.method == 'POST':
        order = get_object_or_404(WebOrder, id=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(WebOrder.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Statut de la commande #{order.id} mis à jour.")
        else:
            messages.error(request, "Statut invalide.")
    
    return redirect('store:admin_weborder_detail', pk=pk)


@method_decorator(manager_required, name='dispatch')
class WebOrderWhatsAppView(ListView):
    """Chat-like view for managing web orders"""
    model = WebOrder
    template_name = 'store/admin/weborder_whatsapp.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        # Prefetch items and products for efficient rendering
        return WebOrder.objects.all().prefetch_related('items__product').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = self.get_queryset()
        
        prepared_orders = []
        orders_json_list = []

        for o in orders:
            has_custom = any(item.customization_data for item in o.items.all())
            
            # Summary
            items_summary = ", ".join([item.product_name or (item.product.name if item.product else 'Produit') for item in o.items.all()[:2]])
            if o.items.count() > 2:
                items_summary += "..."

            prepared_orders.append({
                'order': o,
                'has_custom': has_custom,
                'summary': items_summary
            })

            # Data for JS
            order_data = {
                'id': str(o.id),
                'name': o.full_name,
                'phone': o.phone,
                'email': o.email,
                'address': o.address,
                'city': o.city,
                'status': o.get_status_display(),
                'status_val': o.status,
                'date': o.created_at.strftime('%d/%m/%Y %H:%M'),
                'total': f"{int(o.total_amount)} FC",
                'details_url': reverse('store:admin_weborder_detail', args=[o.id]),
                'update_url': reverse('store:admin_weborder_update_status', args=[o.id]),
                'items': []
            }
            
            for oi in o.items.all():
                item_data = {
                    'name': oi.product_name,
                    'qty': oi.quantity,
                    'price': f"{int(oi.price)} FC",
                    'image': oi.product.image.url if oi.product and oi.product.image else None,
                    'custom': oi.customization_data,
                    'production': oi.production_data,
                    'preview': oi.preview_image.url if oi.preview_image else None,
                    'client_photo': oi.client_image.url if oi.client_image else None
                }
                order_data['items'].append(item_data)
            
            orders_json_list.append(order_data)
            
        context['prepared_orders'] = prepared_orders
        context['orders_json'] = orders_json_list
        context['status_choices'] = WebOrder.STATUS_CHOICES
        return context


# =============================================================
# GESTION DES PAIEMENTS MANUELS
# =============================================================

@method_decorator(manager_required, name='dispatch')
class AdminPaymentListView(ListView):
    """Liste de tous les paiements manuels soumis"""
    model = ManualPayment
    template_name = 'store/admin/payment_list.html'
    context_object_name = 'payments'
    ordering = ['-created_at']
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('order', 'user')
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ManualPayment.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['pending_count'] = ManualPayment.objects.filter(status='submitted').count()
        return context


@manager_required
def approve_payment(request, pk):
    """Approuver un paiement manuel"""
    payment = get_object_or_404(ManualPayment, id=pk)
    if request.method == 'POST':
        payment.status = 'approved'
        payment.verified_at = timezone.now()
        payment.save()
        # Mettre à jour le statut de la commande
        payment.order.status = 'paid'
        payment.order.save()
        messages.success(request, f"✅ Paiement pour la commande #{payment.order.id} approuvé. Statut → Payée.")
    return redirect('store:admin_weborder_detail', pk=payment.order.id)


@manager_required
def reject_payment(request, pk):
    """Rejeter un paiement manuel avec motif"""
    payment = get_object_or_404(ManualPayment, id=pk)
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        payment.status = 'rejected'
        payment.rejection_reason = rejection_reason
        payment.verified_at = timezone.now()
        payment.save()
        # Remettre la commande en attente de paiement
        payment.order.status = 'pending_payment'
        payment.order.save()
        messages.warning(request, f"❌ Paiement pour la commande #{payment.order.id} rejeté.")
    return redirect('store:admin_weborder_detail', pk=payment.order.id)
