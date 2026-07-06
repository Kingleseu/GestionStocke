import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from django.template.loader import render_to_string

from accounts.decorators import manager_required

from .forms import (
    HubForm,
    HubInventoryForm,
    MerchantAccountForm,
    MerchantSignupForm,
    ProcurementOrderStatusForm,
    SupplierForm,
    SupplyCategoryForm,
    SupplyHomeFeatureForm,
    SupplyHomepageStatForm,
    SupplyProcessStepForm,
    SupplyProductForm,
    SupplySiteSettingsForm,
)
from .models import (
    Hub,
    HubInventory,
    MerchantAccount,
    OrderTrackingEvent,
    ProcurementOrder,
    Supplier,
    SupplyCategory,
    SupplyHomeFeature,
    SupplyHomepageStat,
    SupplyProcessStep,
    SupplyProduct,
    SupplySiteSettings,
)
from .services import (
    catalog_payload,
    create_procurement_order,
    find_hub_for_commune,
    merchant_dashboard_context,
    transition_procurement_order,
)


def _user_shop(user):
    profile = getattr(user, 'profile', None)
    return getattr(profile, 'shop', None) if profile else None


def _is_supply_staff(user):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name__in=['Manager', 'Cashier']).exists()
        )
    )


def _merchant_defaults(request):
    user = request.user
    shop = _user_shop(user) if user.is_authenticated else None
    account = getattr(shop, 'merchant_account', None) if shop else None
    name = shop.name if shop else ''

    return {
        'merchant_name': name,
        'commune': account.commune if account else '',
        'delivery_address': shop.address if shop and shop.address else '',
        'contact_phone': account.contact_phone if account and account.contact_phone else (shop.phone if shop and shop.phone else ''),
    }


class SupplyHomeView(TemplateView):
    template_name = 'supply/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suppliers = Supplier.objects.filter(is_active=True)
        hubs = Hub.objects.filter(is_active=True).order_by('name')
        products = SupplyProduct.objects.filter(is_active=True)
        supply_categories = SupplyCategory.objects.filter(is_active=True).order_by('order', 'name')
        site_settings = SupplySiteSettings.get_solo()
        homepage_stats = list(SupplyHomepageStat.objects.filter(is_active=True))
        if not homepage_stats:
            homepage_stats = [
                {'value': suppliers.count(), 'label': 'fournisseurs'},
                {'value': hubs.count(), 'label': 'hubs actifs'},
                {'value': products.count(), 'label': 'produits'},
                {'value': 'J+1', 'label': 'livraison cible'},
            ]
        context.update({
            'site_settings': site_settings,
            'suppliers': suppliers.annotate(product_count=Count('products'))[:8],
            'hubs': hubs,
            'products_json': json.dumps(catalog_payload()),
            'merchant_defaults': _merchant_defaults(self.request),
            'homepage_stats': homepage_stats,
            'features': SupplyHomeFeature.objects.filter(is_active=True),
            'process_steps': SupplyProcessStep.objects.filter(is_active=True),
            'stats': {
                'suppliers': suppliers.count(),
                'hubs': hubs.count(),
                'products': products.count(),
                'orders': ProcurementOrder.objects.count(),
            },
            'category_tabs': supply_categories,
            'nearest_hub': find_hub_for_commune(_merchant_defaults(self.request).get('commune')),
        })
        return context


class MerchantSignupView(TemplateView):
    template_name = 'supply/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not _is_supply_staff(request.user):
            shop = _user_shop(request.user)
            has_merchant_account = bool(shop and hasattr(shop, 'merchant_account'))
            if has_merchant_account:
                return redirect('supply:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form') or MerchantSignupForm()
        context['site_settings'] = SupplySiteSettings.get_solo()
        context['staff_creating_shop'] = _is_supply_staff(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        form = MerchantSignupForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        user, shop = form.save()
        if _is_supply_staff(request.user):
            messages.success(request, f"Boutique {shop.name} creee. Elle apparait maintenant dans le backoffice.")
            return redirect('supply:ops_merchants')

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f"Boutique {shop.name} creee. Vous pouvez maintenant commander.")
        return redirect('supply:dashboard')


class MerchantDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'supply/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(merchant_dashboard_context(self.request.user))
        return context


class ProcurementOrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'supply/order_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_number = kwargs.get('order_number')
        queryset = ProcurementOrder.objects.prefetch_related('items', 'tracking_events').select_related('hub', 'shop')

        if not self.request.user.is_superuser and not self.request.user.groups.filter(name='Manager').exists():
            shop = _user_shop(self.request.user)
            if shop:
                queryset = queryset.filter(shop=shop)
            else:
                queryset = queryset.filter(user=self.request.user)

        order = get_object_or_404(queryset, order_number=order_number)
        context['order'] = order
        context['timeline'] = order.tracking_events.all()
        return context


@require_POST
def create_order(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Connectez-vous pour valider votre approvisionnement.')
        login_url = f"{reverse('accounts:login')}?next={reverse('supply:home')}"
        return redirect(login_url)

    try:
        order = create_procurement_order(request.user, request.POST)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('supply:home')

    messages.success(request, f'Commande {order.tracking_reference} enregistree.')
    return redirect(order.get_absolute_url())


def catalog_api(request):
    return JsonResponse({'products': catalog_payload()})


class SupplyOpsMixin:
    section = ''

    @method_decorator(manager_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ops_section'] = self.section
        return context


@method_decorator(manager_required, name='dispatch')
class SupplyOpsDashboardView(TemplateView):
    template_name = 'supply/ops_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_stats = ProcurementOrder.objects.aggregate(
            total_orders=Count('id'),
            total_amount=Sum('total_amount'),
        )
        low_stock_queryset = HubInventory.objects.filter(
            product__is_active=True,
        ).select_related('hub', 'product', 'product__supplier').order_by('available_quantity')
        context.update({
            'ops_section': 'dashboard',
            'order_stats': order_stats,
            'merchant_count': MerchantAccount.objects.count(),
            'pending_orders_count': ProcurementOrder.objects.exclude(status__in=['delivered', 'cancelled']).count(),
            'supplier_count': Supplier.objects.count(),
            'low_stock_count': low_stock_queryset.filter(
                available_quantity__lte=F('reserved_quantity') + F('reorder_threshold'),
            ).count(),
            'orders': ProcurementOrder.objects.select_related('hub', 'shop').prefetch_related('items')[:12],
            'hub_stats': Hub.objects.annotate(stock_lines=Count('inventories')).order_by('name'),
            'low_stock_items': low_stock_queryset[:10],
            'recent_merchants': MerchantAccount.objects.select_related('shop', 'preferred_hub')
            .annotate(orders_count=Count('shop__procurement_orders'))
            .order_by('-shop__created_at')[:6],
        })
        return context


@method_decorator(manager_required, name='dispatch')
class SupplySiteContentView(TemplateView):
    template_name = 'supply/ops/site_content.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'ops_section': 'content',
            'settings_obj': SupplySiteSettings.get_solo(),
            'stats': SupplyHomepageStat.objects.all(),
            'features': SupplyHomeFeature.objects.all(),
            'process_steps': SupplyProcessStep.objects.all(),
        })
        return context


class SupplySiteSettingsUpdateView(SupplyOpsMixin, UpdateView):
    model = SupplySiteSettings
    form_class = SupplySiteSettingsForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_site_content')
    section = 'content'

    def get_object(self, queryset=None):
        return SupplySiteSettings.get_solo()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Modifier la page publique PEMBENY'
        context['back_url'] = reverse('supply:ops_site_content')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Contenu principal mis a jour.')
        return super().form_valid(form)


class HomepageStatCreateView(SupplyOpsMixin, CreateView):
    model = SupplyHomepageStat
    form_class = SupplyHomepageStatForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_site_content')
    section = 'content'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nouvelle statistique accueil'
        context['back_url'] = reverse('supply:ops_site_content')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Statistique ajoutee.')
        return super().form_valid(form)


class HomepageStatUpdateView(SupplyOpsMixin, UpdateView):
    model = SupplyHomepageStat
    form_class = SupplyHomepageStatForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_site_content')
    section = 'content'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Modifier statistique accueil'
        context['back_url'] = reverse('supply:ops_site_content')
        return context


class HomeFeatureCreateView(SupplyOpsMixin, CreateView):
    model = SupplyHomeFeature
    form_class = SupplyHomeFeatureForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_site_content')
    section = 'content'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nouvelle carte avantage'
        context['back_url'] = reverse('supply:ops_site_content')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Carte avantage ajoutee.')
        return super().form_valid(form)


class HomeFeatureUpdateView(SupplyOpsMixin, UpdateView):
    model = SupplyHomeFeature
    form_class = SupplyHomeFeatureForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_site_content')
    section = 'content'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Modifier carte avantage'
        context['back_url'] = reverse('supply:ops_site_content')
        return context


class ProcessStepCreateView(SupplyOpsMixin, CreateView):
    model = SupplyProcessStep
    form_class = SupplyProcessStepForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_site_content')
    section = 'content'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nouvelle etape processus'
        context['back_url'] = reverse('supply:ops_site_content')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Etape ajoutee.')
        return super().form_valid(form)


class ProcessStepUpdateView(SupplyOpsMixin, UpdateView):
    model = SupplyProcessStep
    form_class = SupplyProcessStepForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_site_content')
    section = 'content'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Modifier etape processus'
        context['back_url'] = reverse('supply:ops_site_content')
        return context


class CategoryListView(SupplyOpsMixin, ListView):
    model = SupplyCategory
    template_name = 'supply/ops/category_list.html'
    context_object_name = 'categories'
    section = 'categories'
    paginate_by = 30

    def get_queryset(self):
        qs = SupplyCategory.objects.order_by('order', 'name')
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(name__icontains=query)
        return qs


class AjaxModalMixin:
    """
    Mixin pour les vues Create/Update qui supportent les modales AJAX.
    Si la requête est AJAX, retourne le formulaire seul sans le layout OPS.
    """
    modal_template_name = 'supply/ops/_modal_form.html'

    def is_modal_request(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def dispatch(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.template_name = self.modal_template_name
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.is_modal_request():
            self.object = form.save()
            return JsonResponse({
                'success': True,
                'redirect_url': self.get_success_url(),
                'object_id': self.object.pk,
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.is_modal_request():
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html}, status=400)
        return super().form_invalid(form)


class CategoryCreateView(AjaxModalMixin, SupplyOpsMixin, CreateView):
    model = SupplyCategory
    form_class = SupplyCategoryForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_categories')
    section = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nouvelle catégorie fournisseur'
        return context


class CategoryUpdateView(AjaxModalMixin, SupplyOpsMixin, UpdateView):
    model = SupplyCategory
    form_class = SupplyCategoryForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_categories')
    section = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Modifier {self.object.name}'
        return context


class SupplierListView(SupplyOpsMixin, ListView):
    model = Supplier
    template_name = 'supply/ops/supplier_list.html'
    context_object_name = 'suppliers'
    section = 'suppliers'
    paginate_by = 30

    def get_queryset(self):
        qs = Supplier.objects.select_related('supply_category').annotate(product_count=Count('products')).order_by('name')
        query = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '')
        if query:
            qs = qs.filter(name__icontains=query)
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs


class SupplierCreateView(AjaxModalMixin, SupplyOpsMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_suppliers')
    section = 'suppliers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nouveau fournisseur'
        return context


class SupplierUpdateView(AjaxModalMixin, SupplyOpsMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_suppliers')
    section = 'suppliers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Modifier {self.object.name}'
        return context


class HubListView(SupplyOpsMixin, ListView):
    model = Hub
    template_name = 'supply/ops/hub_list.html'
    context_object_name = 'hubs'
    section = 'hubs'
    paginate_by = 30

    def get_queryset(self):
        qs = Hub.objects.annotate(stock_lines=Count('inventories')).order_by('name')
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(name__icontains=query)
        return qs


class HubCreateView(AjaxModalMixin, SupplyOpsMixin, CreateView):
    model = Hub
    form_class = HubForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_hubs')
    section = 'hubs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nouveau hub'
        return context


class HubUpdateView(AjaxModalMixin, SupplyOpsMixin, UpdateView):
    model = Hub
    form_class = HubForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_hubs')
    section = 'hubs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Modifier {self.object.name}'
        return context


class ProductListView(SupplyOpsMixin, ListView):
    model = SupplyProduct
    template_name = 'supply/ops/product_list.html'
    context_object_name = 'products'
    section = 'products'
    paginate_by = 40

    def get_queryset(self):
        qs = SupplyProduct.objects.select_related('supplier', 'supply_category').order_by(
            'supply_category__order',
            'supply_category__name',
            'name',
        )
        query = self.request.GET.get('q', '').strip()
        supply_category_id = self.request.GET.get('supply_category', '')
        supplier_id = self.request.GET.get('supplier', '')
        if query:
            qs = qs.filter(name__icontains=query)
        if supply_category_id:
            qs = qs.filter(supply_category_id=supply_category_id)
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supply_categories'] = SupplyCategory.objects.filter(is_active=True).order_by('order', 'name')
        context['suppliers'] = Supplier.objects.order_by('name')
        return context


class ProductCreateView(AjaxModalMixin, SupplyOpsMixin, CreateView):
    model = SupplyProduct
    form_class = SupplyProductForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_products')
    section = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nouveau produit catalogue'
        return context


class ProductUpdateView(AjaxModalMixin, SupplyOpsMixin, UpdateView):
    model = SupplyProduct
    form_class = SupplyProductForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_products')
    section = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Modifier {self.object.name}'
        return context


class InventoryListView(SupplyOpsMixin, ListView):
    model = HubInventory
    template_name = 'supply/ops/inventory_list.html'
    context_object_name = 'inventories'
    section = 'inventory'
    paginate_by = 60

    def get_queryset(self):
        qs = HubInventory.objects.select_related('hub', 'product', 'product__supplier').order_by('hub__name', 'product__name')
        hub_id = self.request.GET.get('hub', '')
        status = self.request.GET.get('status', '')
        query = self.request.GET.get('q', '').strip()
        if hub_id:
            qs = qs.filter(hub_id=hub_id)
        if query:
            qs = qs.filter(product__name__icontains=query)
        if status == 'low':
            qs = [item for item in qs if item.stock_status == 'low']
        elif status == 'out':
            qs = [item for item in qs if item.stock_status == 'out']
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hubs'] = Hub.objects.order_by('name')
        return context


class InventoryCreateView(AjaxModalMixin, SupplyOpsMixin, CreateView):
    model = HubInventory
    form_class = HubInventoryForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_inventory')
    section = 'inventory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Ajouter stock hub'
        return context


class InventoryUpdateView(AjaxModalMixin, SupplyOpsMixin, UpdateView):
    model = HubInventory
    form_class = HubInventoryForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_inventory')
    section = 'inventory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Modifier stock - {self.object.product.name}'
        return context


class MerchantAccountListView(SupplyOpsMixin, ListView):
    model = MerchantAccount
    template_name = 'supply/ops/merchant_list.html'
    context_object_name = 'merchants'
    section = 'merchants'
    paginate_by = 40

    def get_queryset(self):
        qs = (
            MerchantAccount.objects.select_related('shop', 'shop__created_by', 'preferred_hub')
            .annotate(
                orders_count=Count('shop__procurement_orders'),
                orders_total=Sum('shop__procurement_orders__total_amount'),
            )
            .order_by('-shop__created_at')
        )
        query = self.request.GET.get('q', '').strip()
        commune = self.request.GET.get('commune', '').strip()
        hub_id = self.request.GET.get('hub', '')
        credit = self.request.GET.get('credit', '')
        prequalification = self.request.GET.get('prequalification', '')

        if query:
            qs = qs.filter(
                Q(shop__name__icontains=query)
                | Q(shop__email__icontains=query)
                | Q(owner_full_name__icontains=query)
                | Q(contact_phone__icontains=query)
                | Q(whatsapp__icontains=query)
            )
        if commune:
            qs = qs.filter(commune__icontains=commune)
        if hub_id:
            qs = qs.filter(preferred_hub_id=hub_id)
        if credit == 'enabled':
            qs = qs.filter(is_credit_enabled=True)
        elif credit == 'disabled':
            qs = qs.filter(is_credit_enabled=False)
        if prequalification == 'ready':
            qs = qs.filter(business_age__in=MerchantAccount.PREQUALIFIED_AGES)
        elif prequalification == 'review':
            qs = qs.exclude(business_age__in=MerchantAccount.PREQUALIFIED_AGES)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hubs'] = Hub.objects.order_by('name')
        return context


class MerchantAccountDetailView(SupplyOpsMixin, TemplateView):
    template_name = 'supply/ops/merchant_detail.html'
    section = 'merchants'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        merchant = get_object_or_404(
            MerchantAccount.objects.select_related('shop', 'shop__created_by', 'preferred_hub'),
            pk=kwargs['pk'],
        )
        orders_queryset = (
            ProcurementOrder.objects.filter(shop=merchant.shop)
            .select_related('hub')
            .prefetch_related('items')
            .order_by('-created_at')
        )
        orders_total = orders_queryset.aggregate(total=Sum('total_amount')).get('total') or 0
        context.update({
            'merchant': merchant,
            'orders': orders_queryset[:12],
            'orders_count': orders_queryset.count(),
            'active_orders_count': orders_queryset.exclude(status__in=['delivered', 'cancelled']).count(),
            'delivered_orders_count': orders_queryset.filter(status='delivered').count(),
            'orders_total': orders_total,
            'last_order': orders_queryset.first(),
        })
        return context


class MerchantAccountUpdateView(SupplyOpsMixin, UpdateView):
    model = MerchantAccount
    form_class = MerchantAccountForm
    template_name = 'supply/ops/form.html'
    success_url = reverse_lazy('supply:ops_merchants')
    section = 'merchants'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Parametres boutique - {self.object.shop.name}'
        context['back_url'] = reverse('supply:ops_merchants')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Compte boutique mis a jour.')
        return super().form_valid(form)


class OpsOrderListView(SupplyOpsMixin, ListView):
    model = ProcurementOrder
    template_name = 'supply/ops/order_list.html'
    context_object_name = 'orders'
    section = 'orders'
    paginate_by = 40

    def get_queryset(self):
        qs = ProcurementOrder.objects.select_related('hub', 'shop').prefetch_related('items').order_by('-created_at')
        status = self.request.GET.get('status', '')
        hub_id = self.request.GET.get('hub', '')
        query = self.request.GET.get('q', '').strip()
        if status:
            qs = qs.filter(status=status)
        if hub_id:
            qs = qs.filter(hub_id=hub_id)
        if query:
            qs = qs.filter(merchant_name__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ProcurementOrder.STATUS_CHOICES
        context['hubs'] = Hub.objects.order_by('name')
        return context


class OpsOrderDetailView(SupplyOpsMixin, TemplateView):
    template_name = 'supply/ops/order_detail.html'
    section = 'orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = get_object_or_404(
            ProcurementOrder.objects.select_related('hub', 'shop').prefetch_related('items', 'tracking_events'),
            pk=kwargs['pk'],
        )
        context['order'] = order
        context['timeline'] = order.tracking_events.all()
        context['status_form'] = ProcurementOrderStatusForm(instance=order)
        return context


@manager_required
@require_POST
def update_order_status(request, pk):
    order = get_object_or_404(ProcurementOrder, pk=pk)
    form = ProcurementOrderStatusForm(request.POST, instance=order)
    if not form.is_valid():
        messages.error(request, 'Statut invalide.')
        return redirect('supply:ops_order_detail', pk=order.pk)

    note = form.cleaned_data.get('note') or ''
    new_status = form.cleaned_data['status']
    order.payment_reference = form.cleaned_data.get('payment_reference') or ''
    order.save(update_fields=['payment_reference', 'updated_at'])
    try:
        transition_procurement_order(order, new_status, user=request.user, note=note)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('supply:ops_order_detail', pk=order.pk)

    messages.success(request, 'Statut de commande mis a jour.')
    return redirect('supply:ops_order_detail', pk=order.pk)


@manager_required
@require_POST
def toggle_active(request, model_name, pk):
    models = {
        'supplier': Supplier,
        'hub': Hub,
        'product': SupplyProduct,
        'stat': SupplyHomepageStat,
        'feature': SupplyHomeFeature,
        'process': SupplyProcessStep,
    }
    model = models.get(model_name)
    if not model:
        messages.error(request, 'Objet invalide.')
        return redirect('supply:ops_dashboard')

    obj = get_object_or_404(model, pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active'])
    messages.success(request, 'Statut mis a jour.')
    return redirect(request.POST.get('next') or 'supply:ops_dashboard')
