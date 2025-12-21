from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import F
from products.models import Product
from accounts.decorators import manager_required
from django.utils.decorators import method_decorator

@method_decorator(manager_required, name='dispatch')
class StockListView(ListView):
    """Vue pour la gestion des stocks"""
    model = Product
    template_name = 'inventory/stock_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        # Trier par statut de stock (rupture d'abord, puis faible, puis ok)
        return Product.objects.filter(
            shop=self.request.user.profile.shop,
            is_active=True
        ).order_by('current_stock')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['low_stock_count'] = Product.objects.filter(
            shop=self.request.user.profile.shop,
            is_active=True, 
            current_stock__lte=F('minimum_stock')
        ).count()
        return context

@manager_required
def brain_dashboard_view(request):
    """Tableau de bord 'Le Cerveau' - Prédictions de stock"""
    from .ai import StockBrain
    
    # Pass the shop to StockBrain
    brain = StockBrain(request.user.profile.shop, analysis_period_days=30)
    predictions = brain.get_dashboard_data()
    
    # Séparer les alertes critiques
    critical_items = [p for p in predictions if p['risk_level'] in ('CRITICAL', 'OUT_OF_STOCK')]
    
    context = {
        'predictions': predictions,
        'critical_count': len(critical_items),
        'total_analyzed': len(predictions),
    }
    
    return render(request, 'inventory/brain_dashboard.html', context)

@manager_required
def get_product_history_api(request, product_id):
    """API pour récupérer l'historique des ventes d'un produit (JSON)"""
    from django.http import JsonResponse
    from sales.models import SaleItem, Sale
    from django.db.models import Sum
    from django.shortcuts import get_object_or_404
    from datetime import timedelta
    from django.utils import timezone
    
    # Security: Ensure product belongs to user's shop
    # Note: user.profile is guaranteed by manager_required + middleware/signals usually, 
    # but we should catch if shop is missing to be safe (though get_queryset handles it above)
    product = get_object_or_404(Product, id=product_id, shop=request.user.profile.shop)
    
    days = 30
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Initialiser les données pour chaque jour (même s'il n'y a pas de vente)
    dates = []
    quantities = []
    
    current = start_date
    while current <= end_date:
        # Chercher les ventes pour ce jour via SaleItem
        # Note: SaleItem -> Sale -> Shop check implicit via Product ownership usually,
        # but to be extra safe we could check sale__shop if Sale had it.
        # Since Product is isolated, SaleItems for this product are implicitly isolated 
        # UNLESS the same product ID existed in multiple shops (impossible due to ID primary key).
        # So checking product ownership is sufficient.
        total = SaleItem.objects.filter(
            product=product,
            sale__sale_date__date=current
        ).aggregate(sum=Sum('quantity'))['sum'] or 0
        
        dates.append(current.strftime('%d/%m'))
        quantities.append(total)
        current += timedelta(days=1)
        
    return JsonResponse({
        'product_name': product.name,
        'dates': dates,
        'quantities': quantities
    })
