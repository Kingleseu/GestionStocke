# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from .decorators import manager_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta


@login_required
def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('accounts:login')


def login_view(request):
    """Page de connexion"""
    if request.user.is_authenticated:
        return redirect('sales:pos')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Vérifier si l'utilisateur existe d'abord pour le message de blocage
        try:
            user_check = User.objects.get(username=username)
            if not user_check.is_active:
                messages.error(request, 'Votre compte est bloqué ou désactivé. Veuillez contacter votre manager.')
                return render(request, 'accounts/login.html')
        except User.DoesNotExist:
            pass
        except Exception as e:
            # Handle database errors gracefully (e.g., tables don't exist yet)
            from django.db import DatabaseError
            if isinstance(e, DatabaseError):
                messages.error(request, 'Erreur de base de données. Veuillez contacter l\'administrateur.')
                return render(request, 'accounts/login.html')
            raise

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Votre compte est bloqué ou désactivé.')
            else:
                login(request, user)
                messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
                next_url = request.GET.get('next', 'sales:pos')
                return redirect(next_url)
        else:
            messages.error(request, 'Identifiants incorrects.')
    
    return render(request, 'accounts/login.html')


def signup_view(request):
    """Inscription pour les Managers (Création de Boutique)"""
    if request.user.is_authenticated:
        return redirect('sales:pos')

    if request.method == 'POST':
        from django.contrib.auth.forms import UserCreationForm
        form = UserCreationForm(request.POST)
        shop_name = request.POST.get('shop_name')

        if form.is_valid() and shop_name:
            # 1. Créer l'utilisateur
            user = form.save()
            
            # 2. Créer la boutique
            from .models import Shop, UserProfile
            shop = Shop.objects.create(name=shop_name, created_by=user)
            
            # 3. Récupérer le profil créé par le signal et lier à la boutique
            profile = user.profile  # Le signal l'a déjà créé
            profile.shop = shop
            profile.save()
            
            # 4. Assigner le groupe Manager
            manager_group, _ = Group.objects.get_or_create(name='Manager')
            user.groups.add(manager_group)
            
            messages.success(request, f"Compte et boutique '{shop_name}' créés avec succès ! Connectez-vous.")
            return redirect('accounts:login')
        else:
            if not shop_name:
                messages.error(request, "Le nom de la boutique est obligatoire.")
    else:
        from django.contrib.auth.forms import UserCreationForm
        form = UserCreationForm()

    return render(request, 'accounts/signup.html', {'form': form})


@manager_required
def create_invitation_view(request):
    """Générer une invitation pour un caissier"""
    from .models import CashierInvitation
    
    invitation = CashierInvitation.objects.create(created_by=request.user)
    
    # Construire l'URL d'inscription
    invite_url = request.build_absolute_uri(
        reverse('accounts:register_cashier', args=[str(invitation.token)])
    )
    
    return JsonResponse({
        'success': True,
        'invite_url': invite_url,
        'token': str(invitation.token)
    })


def register_cashier_view(request, token):
    """Inscription via invitation"""
    if request.user.is_authenticated:
        return redirect('sales:pos')
        
    from .models import CashierInvitation, UserProfile
    from django.contrib.auth.forms import UserCreationForm
    
    try:
        invitation = CashierInvitation.objects.get(token=token, is_used=False)
    except CashierInvitation.DoesNotExist:
        messages.error(request, "Ce lien d'invitation est invalide ou a déjà été utilisé.")
        return redirect('accounts:login')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Compte inactif par défaut
            user.save()
            
            # Assigner le groupe "Cashier"
            cashier_group, _ = Group.objects.get_or_create(name='Cashier')
            user.groups.add(cashier_group)
            
            # Lier à la boutique du Manager qui a invité (le signal a déjà créé le profil)
            inviter_profile = invitation.created_by.profile
            user.profile.shop = inviter_profile.shop
            user.profile.save()
            
            # Marquer l'invitation comme utilisée
            invitation.is_used = True
            invitation.used_by = user
            invitation.save()
            
            messages.success(request, f"Compte créé ! Votre manager ({invitation.created_by.username}) doit maintenant l'activer.")
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register_cashier.html', {'form': form})


@manager_required
def user_list(request):
    """Liste des utilisateurs de MA boutique"""
    # Filtrer uniquement les utilisateurs de la même boutique
    current_shop = request.user.profile.shop
    
    if not current_shop:
        messages.error(request, "Vous n'êtes lié à aucune boutique.")
        return redirect('dashboard')

    users = User.objects.filter(profile__shop=current_shop).select_related('profile').prefetch_related('groups')
    
    context = {
        'users': users,
        'total_users': users.count(),
        'managers': users.filter(groups__name='Manager').count(),
        'cashiers': users.filter(groups__name='Cashier').count(),
        'active_count': users.filter(is_active=True).count(),
        'pending_count': users.filter(is_active=False).count(),
        'shop_name': current_shop.name
    }
    
    return render(request, 'accounts/user_list.html', context)


@manager_required
def user_toggle_active(request, user_id):
    """Activer/désactiver un utilisateur (Sécurité: Vérifier la boutique)"""
    try:
        user_to_toggle = User.objects.get(id=user_id)
        
        # Vérification de sécurité : le manager ne peut agir que sur sa boutique
        if user_to_toggle.profile.shop != request.user.profile.shop:
            messages.error(request, "Action non autorisée sur cet utilisateur.")
            return redirect('accounts:user_list')
            
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()
        
        status = "activé" if user_to_toggle.is_active else "désactivé"
        messages.success(request, f'Utilisateur {user_to_toggle.username} {status}.')
    except User.DoesNotExist:
        messages.error(request, 'Utilisateur introuvable.')
    
    return redirect('accounts:user_list')


@login_required
def profile_view(request):
    """Profil de l'utilisateur connecté"""
    user = request.user
    groups = user.groups.all()
    
    context = {
        'user': user,
        'groups': groups,
    }
    
    return render(request, 'accounts/profile.html', context)


@manager_required
def cashier_dashboard_view(request, cashier_id):
    """Tableau de bord pour un caissier spécifique"""
    cashier = get_object_or_404(User, id=cashier_id)
    
    # Vérifier que c'est bien un caissier (ou a des ventes)
    if not cashier.groups.filter(name='Cashier').exists() and not cashier.is_staff:
        messages.warning(request, "Cet utilisateur n'est pas un caissier.")
    
    # Statistiques de ventes
    from sales.models import Sale
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    sales_today = Sale.objects.filter(cashier=cashier, sale_date__date=today)
    sales_week = Sale.objects.filter(cashier=cashier, sale_date__date__gte=start_of_week)
    sales_month = Sale.objects.filter(cashier=cashier, sale_date__date__gte=start_of_month)
    
    total_today = sum(s.total for s in sales_today)
    total_week = sum(s.total for s in sales_week)
    total_month = sum(s.total for s in sales_month)
    
    # Historique d'activité
    from .models import UserActivity
    activities = UserActivity.objects.filter(user=cashier)[:50]
    
    context = {
        'cashier': cashier,
        'stats': {
            'today': {'count': sales_today.count(), 'total': total_today},
            'week': {'count': sales_week.count(), 'total': total_week},
            'month': {'count': sales_month.count(), 'total': total_month},
        },
        'activities': activities,
        'recent_sales': Sale.objects.filter(cashier=cashier).order_by('-sale_date')[:10]
    }
    
    return render(request, 'accounts/cashier_dashboard.html', context)
