from django.db.models import Sum, F
from django.utils import timezone
from datetime import datetime, date, timedelta
from sales.models import Sale
from purchases.models import Purchase
from .models import Expense, ExpenseCategory

class AccountingService:
    def __init__(self, shop):
        self.shop = shop

    def get_financial_summary(self, start_date=None, end_date=None):
        """
        Récupère le résumé financier (Revenus, Achats, Frais, Bénéfice) 
        pour une période donnée.
        """
        # Filtrage par dates si fournies
        sales_qs = Sale.objects.filter(shop=self.shop, is_cancelled=False)
        purchases_qs = Purchase.objects.filter(shop=self.shop)
        expenses_qs = Expense.objects.filter(shop=self.shop)

        if start_date:
            sales_qs = sales_qs.filter(sale_date__date__gte=start_date)
            purchases_qs = purchases_qs.filter(purchase_date__date__gte=start_date)
            expenses_qs = expenses_qs.filter(date__gte=start_date)
        
        if end_date:
            sales_qs = sales_qs.filter(sale_date__date__lte=end_date)
            purchases_qs = purchases_qs.filter(purchase_date__date__lte=end_date)
            expenses_qs = expenses_qs.filter(date__lte=end_date)

        # Calcul des agrégations
        revenue = sales_qs.aggregate(total=Sum('total'))['total'] or 0
        stock_costs = purchases_qs.aggregate(total=Sum('total'))['total'] or 0
        operating_expenses = expenses_qs.aggregate(total=Sum('amount'))['total'] or 0

        total_costs = stock_costs + operating_expenses
        net_profit = revenue - total_costs

        return {
            'revenue': revenue,
            'stock_costs': stock_costs,
            'operating_expenses': operating_expenses,
            'total_costs': total_costs,
            'net_profit': net_profit,
            'sales_count': sales_qs.count(),
            'purchases_count': purchases_qs.count(),
            'expenses_count': expenses_qs.count(),
            # Données pour les détails
            'sales': sales_qs.order_by('-sale_date')[:50],  # Limite pour le dash
            'purchases': purchases_qs.order_by('-purchase_date')[:50],
            'expenses': expenses_qs.order_by('-date')[:50],
        }

    def get_expense_breakdown(self, start_date=None, end_date=None):
        """Répartition des dépenses par catégorie."""
        expenses_qs = Expense.objects.filter(shop=self.shop)
        if start_date:
            expenses_qs = expenses_qs.filter(date__gte=start_date)
        if end_date:
            expenses_qs = expenses_qs.filter(date__lte=end_date)
            
        return expenses_qs.values('category__name', 'category__icon').annotate(
            total=Sum('amount')
        ).order_by('-total')

    @staticmethod
    def get_date_range(period):
        """Helper pour obtenir les plages de dates prédéfinies."""
        today = timezone.now().date()
        if period == 'day':
            return today, today
        elif period == 'month':
            start = today.replace(day=1)
            return start, today
        elif period == 'year':
            start = today.replace(month=1, day=1)
            return start, today
        return None, None
