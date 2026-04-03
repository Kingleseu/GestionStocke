from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from accounts.decorators import manager_required
from .models import Expense, ExpenseCategory
from .services import AccountingService
from .utils import ExportManager
from datetime import datetime

@method_decorator(manager_required, name='dispatch')
class AccountingDashboardView(View):
    template_name = 'reports/accounting_dashboard.html'
    
    def get(self, request):
        service = AccountingService(request.user.profile.shop)
        period = request.GET.get('period', 'month')
        start_date, end_date = service.get_date_range(period)
        
        # Surcharge manuelle possible (via formulaire futur)
        custom_start = request.GET.get('start_date')
        custom_end = request.GET.get('end_date')
        if custom_start:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
        if custom_end:
            end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()

        data = service.get_financial_summary(start_date, end_date)
        breakdown = list(service.get_expense_breakdown(start_date, end_date))
        
        # Calculer les pourcentages pour le template
        total_ops = data['operating_expenses']
        for item in breakdown:
            item['percentage'] = (item['total'] / total_ops * 100) if total_ops > 0 else 0

        # Calculer la marge bénéficiaire
        revenue = data['revenue']
        margin_percent = (data['net_profit'] / revenue * 100) if revenue > 0 else 0
        
        context = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'summary': data,
            'breakdown': breakdown,
            'margin_percent': margin_percent,
            'now': datetime.now(),
        }
        return render(request, self.template_name, context)

@method_decorator(manager_required, name='dispatch')
class ExpenseListView(ListView):
    model = Expense
    template_name = 'reports/expense_list.html'
    context_object_name = 'expenses'
    
    def get_queryset(self):
        return Expense.objects.filter(shop=self.request.user.profile.shop)

@method_decorator(manager_required, name='dispatch')
class ExpenseCreateView(CreateView):
    model = Expense
    fields = ['category', 'title', 'amount', 'date', 'notes']
    template_name = 'reports/expense_form.html'
    success_url = reverse_lazy('reports:expense_list')

    def form_valid(self, form):
        form.instance.shop = self.request.user.profile.shop
        form.instance.created_by = self.request.user
        messages.success(self.request, "Dépense enregistrée avec succès.")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filtrer les catégories par boutique
        form.fields['category'].queryset = ExpenseCategory.objects.filter(shop=self.request.user.profile.shop)
        return form

@method_decorator(manager_required, name='dispatch')
class ExpenseCategoryCreateView(CreateView):
    model = ExpenseCategory
    fields = ['name', 'description', 'icon']
    template_name = 'reports/category_form.html'
    success_url = reverse_lazy('reports:dashboard')

    def form_valid(self, form):
        form.instance.shop = self.request.user.profile.shop
        messages.success(self.request, "Nouvelle catégorie de dépense créée.")
        return super().form_valid(form)

@method_decorator(manager_required, name='dispatch')
class ExportAccountingView(View):
    def get(self, request, format):
        service = AccountingService(request.user.profile.shop)
        period = request.GET.get('period', 'month')
        start_date, end_date = service.get_date_range(period)
        
        data = service.get_financial_summary(start_date, end_date)
        period_name = f"{period} ({start_date or ''} - {end_date or ''})"
        
        if format == 'excel':
            output = ExportManager.to_excel(data, period_name)
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename=Bilan_MKARIBU_{period}.xlsx'
            return response
            
        elif format == 'pdf':
            buffer = ExportManager.to_pdf(data, period_name)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=Bilan_MKARIBU_{period}.pdf'
            return response
            
        return redirect('reports:dashboard')
