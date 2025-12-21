from django.views.generic import TemplateView
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
from sales.models import Sale, SaleItem
from products.models import Product
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.decorators import manager_required
from django.utils.decorators import method_decorator

@method_decorator(manager_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = getattr(getattr(self.request.user, "profile", None), "shop", None)

        # Base queryset filtered by shop when available
        sales_qs = Sale.objects.filter(is_cancelled=False)
        if shop:
            sales_qs = sales_qs.filter(cashier__profile__shop=shop)

        today = timezone.now().date()
        today_sales = sales_qs.filter(sale_date__date=today)
        context["daily_total"] = today_sales.aggregate(total=Sum("total"))["total"] or 0
        context["daily_count"] = today_sales.count()

        product_qs = Product.objects.filter(is_active=True)
        if shop:
            product_qs = product_qs.filter(shop=shop)
        context["low_stock_products"] = product_qs.filter(current_stock__lte=F("minimum_stock")).order_by("current_stock")

        seven_days_ago = timezone.now() - timedelta(days=7)
        top_products_qs = SaleItem.objects.filter(
            sale__is_cancelled=False,
            sale__sale_date__gte=seven_days_ago,
        )
        if shop:
            top_products_qs = top_products_qs.filter(product__shop=shop)

        context["top_products"] = (
            top_products_qs.values("product__name", "product__barcode")
            .annotate(total_qty=Sum("quantity"), total_revenue=Sum("subtotal"))
            .order_by("-total_revenue")[:10]
        )

        return context

@method_decorator(manager_required, name='dispatch')
class SalesReportView(TemplateView):
    template_name = 'reports/sales_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        sales_qs = Sale.objects.filter(is_cancelled=False)
        
        if date_from:
            sales_qs = sales_qs.filter(sale_date__date__gte=date_from)
        if date_to:
            sales_qs = sales_qs.filter(sale_date__date__lte=date_to)
            
        # Aggregates
        total_revenue = sales_qs.aggregate(Sum('total'))['total__sum'] or 0
        total_transactions = sales_qs.count()
        avg_basket = total_revenue / total_transactions if total_transactions > 0 else 0
        
        context['total_revenue'] = total_revenue
        context['total_transactions'] = total_transactions
        context['avg_basket'] = avg_basket
        
        # Chart Data (Daily Trend)
        daily_trend = sales_qs.annotate(date=TruncDate('sale_date')).values('date').annotate(
            daily_total=Sum('total')
        ).order_by('date')
        
        context['chart_labels'] = [d['date'].strftime('%d/%m') for d in daily_trend]
        context['chart_data'] = [float(d['daily_total']) for d in daily_trend]
        
        # Recent Sales Table
        context['recent_sales'] = sales_qs.select_related('cashier').order_by('-sale_date')[:50]
        
        return context
