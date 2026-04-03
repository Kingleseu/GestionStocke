from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard Financier
    path('accounting/', views.AccountingDashboardView.as_view(), name='dashboard'),
    
    # Gestion des Dépenses (Charges)
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/add/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/categories/add/', views.ExpenseCategoryCreateView.as_view(), name='category_create'),
    
    # Exports
    path('accounting/export/<str:format>/', views.ExportAccountingView.as_view(), name='export'),
]