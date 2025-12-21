# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('register/<uuid:token>/', views.register_cashier_view, name='register_cashier'),
    path('logout/', views.logout_view, name='logout'),
    
    # Gestion des utilisateurs (Manager uniquement)
    path('users/', views.user_list, name='user_list'),
    path('users/invite/', views.create_invitation_view, name='create_invitation'),
    path('users/<int:user_id>/toggle/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:cashier_id>/dashboard/', views.cashier_dashboard_view, name='cashier_dashboard'),
    
    # Profil
    path('profile/', views.profile_view, name='profile'),
]
