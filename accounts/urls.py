from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts'

urlpatterns = [
    # Logins séparés
    path('login/', views.login_view, name='login'),
    path('manager/login/', views.manager_login_view, name='manager_login'),
    
    # Inscriptions
    path('signup/', views.signup_view, name='signup'),
    path('customer/signup/', views.customer_signup_view, name='customer_signup'),
    path('register/<uuid:token>/', views.register_cashier_view, name='register_cashier'),
    path('logout/', views.logout_view, name='logout'),
    
    # Récupération de compte (Mot de passe oublié)
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html', email_template_name='accounts/emails/password_reset_email.html', success_url='/accounts/password-reset/done/'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html', success_url='/accounts/password-reset-complete/'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), 
         name='password_reset_complete'),

    # Gestion des utilisateurs
    path('users/', views.user_list, name='user_list'),
    path('users/invite/', views.create_invitation_view, name='create_invitation'),
    path('users/<int:user_id>/toggle/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:cashier_id>/dashboard/', views.cashier_dashboard_view, name='cashier_dashboard'),
    path('profile/', views.profile_view, name='profile'),
]
