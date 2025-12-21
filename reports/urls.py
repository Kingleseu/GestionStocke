from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('sales-report/', views.SalesReportView.as_view(), name='sales_report'),
]