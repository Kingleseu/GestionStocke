from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from .models import Promotion, PromotionLog
from .forms import PromotionForm, BulkPromotionActionForm
from .utils import calculate_product_price, update_promotion_status
from products.models import Product


class PromotionListView(LoginRequiredMixin, ListView):
    """Liste toutes les promotions"""
    model = Promotion
    template_name = 'promotions/promotion_list.html'
    context_object_name = 'promotions'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Promotion.objects.prefetch_related('products', 'categories').order_by('-start_date')
        
        # Filtrage par statut
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now())
        elif status == 'upcoming':
            qs = qs.filter(is_active=True, start_date__gt=timezone.now())
        elif status == 'expired':
            qs = qs.filter(end_date__lt=timezone.now())
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        
        # Recherche
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(banner_message__icontains=search)
            )
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.request.GET.get('status', 'all')
        context['search'] = self.request.GET.get('search', '')
        
        # Stats
        now = timezone.now()
        context['stats'] = {
            'total': Promotion.objects.count(),
            'active': Promotion.objects.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            ).count(),
            'upcoming': Promotion.objects.filter(
                is_active=True,
                start_date__gt=now
            ).count(),
            'expired': Promotion.objects.filter(end_date__lt=now).count(),
        }
        
        return context


class PromotionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crée une nouvelle promotion"""
    model = Promotion
    form_class = PromotionForm
    template_name = 'promotions/promotion_form.html'
    permission_required = 'promotions.add_promotion'
    success_url = reverse_lazy('promotions:promotion_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"✅ Promotion '{form.instance.name}' créée avec succès!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle Promotion'
        return context


class PromotionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Modifie une promotion"""
    model = Promotion
    form_class = PromotionForm
    template_name = 'promotions/promotion_form.html'
    permission_required = 'promotions.change_promotion'
    success_url = reverse_lazy('promotions:promotion_list')
    
    def form_valid(self, form):
        messages.success(self.request, f"✅ Promotion '{form.instance.name}' modifiée avec succès!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier Promotion'
        return context


class PromotionDetailView(LoginRequiredMixin, DetailView):
    """Affiche les détails d'une promotion"""
    model = Promotion
    template_name = 'promotions/promotion_detail.html'
    context_object_name = 'promotion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promotion = self.object
        
        # Produits affectés
        context['applicable_products'] = promotion.get_applicable_products()[:10]
        context['product_count'] = promotion.get_applicable_products().count()
        
        # Logs
        context['logs'] = promotion.logs.all()[:5]
        
        # Exemple de prix réduit
        products = promotion.get_applicable_products()[:3]
        context['price_examples'] = [
            {
                'product': p,
                'pricing': calculate_product_price(p)
            }
            for p in products
        ]
        
        return context


class PromotionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Supprime une promotion"""
    model = Promotion
    template_name = 'promotions/promotion_confirm_delete.html'
    permission_required = 'promotions.delete_promotion'
    success_url = reverse_lazy('promotions:promotion_list')
    
    def delete(self, request, *args, **kwargs):
        promo_name = self.get_object().name
        messages.success(request, f"✅ Promotion '{promo_name}' supprimée!")
        return super().delete(request, *args, **kwargs)


@login_required
@permission_required('promotions.change_promotion')
def update_all_promotions(request):
    """Met à jour le statut de toutes les promotions"""
    stats = update_promotion_status()
    
    messages.success(
        request,
        f"✅ Mise à jour: {stats['activated']} promo(s) activée(s), {stats['deactivated']} expirée(s)"
    )
    
    return redirect('promotions:promotion_list')


@login_required
def promotion_logs_view(request, pk):
    """Affiche tous les logs d'une promotion"""
    promotion = get_object_or_404(Promotion, pk=pk)
    logs = promotion.logs.all()
    
    return render(request, 'promotions/promotion_logs.html', {
        'promotion': promotion,
        'logs': logs
    })
