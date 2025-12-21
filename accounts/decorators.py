# accounts/decorators.py

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from functools import wraps


from django.http import JsonResponse

def manager_required(view_func):
    """
    Décorateur pour restreindre l'accès aux utilisateurs du groupe Manager
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or '/api/' in request.path:
                return JsonResponse({'success': False, 'error': 'Session expirée. Veuillez vous reconnecter.'}, status=401)
            return redirect('accounts:login')
        
        if request.user.is_superuser or request.user.groups.filter(name='Manager').exists():
            return view_func(request, *args, **kwargs)
        
        # Rediriger vers la page d'accueil si pas autorisé
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or '/api/' in request.path:
            return JsonResponse({'success': False, 'error': 'Accès refusé. Droits insuffisants.'}, status=403)
            
        from django.contrib import messages
        messages.error(request, "Accès refusé. Vous devez être Manager pour accéder à cette page.")
        return redirect('sales:pos')  # Rediriger vers l'écran de caisse
    
    return wrapper


def cashier_required(view_func):
    """
    Décorateur pour restreindre l'accès aux utilisateurs du groupe Cashier ou Manager
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or '/api/' in request.path:
                return JsonResponse({'success': False, 'error': 'Session expirée. Veuillez vous reconnecter.'}, status=401)
            return redirect('accounts:login')
        
        if (request.user.is_superuser or 
            request.user.groups.filter(name__in=['Manager', 'Cashier']).exists()):
            return view_func(request, *args, **kwargs)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or '/api/' in request.path:
            return JsonResponse({'success': False, 'error': 'Accès refusé. Droits insuffisants.'}, status=403)

        from django.contrib import messages
        messages.error(request, "Accès refusé. Vous devez être caissier pour accéder à cette page.")
        return redirect('accounts:login')
    
    return wrapper


def is_manager(user):
    """
    Fonction helper pour vérifier si un utilisateur est Manager
    """
    return user.is_superuser or user.groups.filter(name='Manager').exists()


def is_cashier(user):
    """
    Fonction helper pour vérifier si un utilisateur est Cashier ou Manager
    """
    return user.is_superuser or user.groups.filter(name__in=['Manager', 'Cashier']).exists()
