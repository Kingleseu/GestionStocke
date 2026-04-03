from datetime import timedelta
from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .decorators import manager_required
from .forms import (
    CustomerSignupForm,
    ManagerSignupForm,
    ProfileUpdateForm,
    StaffInvitationForm,
    StaffInvitationRegistrationForm,
    CustomerLoginForm,
    StaffLoginForm,
)
from .models import ACCOUNT_SPACE_CUSTOMER, ACCOUNT_SPACE_STAFF, CashierInvitation
from .services import (
    role_label_for_user,
    roles_for_user,
    get_user_by_email_and_space,
    mask_email,
    send_staff_invitation_email,
)


def _wants_json(request):
    accept = request.headers.get('Accept', '')
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in accept


def _serialize_form_errors(form):
    errors = {}
    for field, field_errors in form.errors.items():
        key = '__all__' if field == '__all__' else field
        errors[key] = [str(error) for error in field_errors]
    return errors


def _is_staff_user(user):
    return user.is_staff or user.is_superuser or user.groups.filter(name__in=['Manager', 'Cashier']).exists()


def _default_redirect_for_user(user):
    if _is_staff_user(user):
        return reverse('sales:pos')
    return reverse('store:catalog')


def _resolve_redirect_target(request, user, explicit_next=None):
    fallback = _default_redirect_for_user(user)
    candidate = explicit_next or request.POST.get('next') or request.GET.get('next')

    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate

    return fallback


def _auth_success_payload(user, redirect_url, message):
    return {
        'success': True,
        'message': message,
        'redirect_url': redirect_url,
        'user': {
            'id': user.id,
            'display_name': user.get_full_name().strip() or user.first_name or user.username,
            'email': user.email,
        },
    }


def _build_public_absolute_uri(request, path):
    public_app_url = getattr(settings, 'PUBLIC_APP_URL', '')
    if public_app_url:
        return urljoin(f'{public_app_url}/', path.lstrip('/'))
    return request.build_absolute_uri(path)




@login_required
def logout_view(request):
    redirect_url = _resolve_redirect_target(request, request.user)
    logout(request)
    request.session.pop('otp_preview', None)
    messages.info(request, 'Vous avez ete deconnecte.')

    if _wants_json(request):
        return JsonResponse({'success': True, 'redirect_url': redirect_url})
    return redirect(redirect_url)


def login_view(request):
    """Connexion standard pour les clients (Email + Mot de passe)."""

    if request.user.is_authenticated:
        return redirect(_resolve_redirect_target(request, request.user))

    form = CustomerLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.user_cache
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        redirect_url = _resolve_redirect_target(request, user)
        success_message = f"Bienvenue {user.get_full_name().strip() or user.username}."
        messages.success(request, success_message)

        if _wants_json(request):
            return JsonResponse(_auth_success_payload(user, redirect_url, success_message))
        return redirect(redirect_url)

    if request.method == 'POST' and _wants_json(request):
        return JsonResponse({'success': False, 'errors': _serialize_form_errors(form)}, status=400)

    return render(
        request,
        'accounts/login.html',
        {
            'form': form,
            'next': request.GET.get('next') or request.POST.get('next', ''),
        },
    )


def manager_login_view(request):
    """Connexion dédiée au personnel (Manager/Caissier)."""

    if request.user.is_authenticated:
        if _is_staff_user(request.user):
            return redirect('store:admin_dashboard')
        return redirect('store:catalog')

    form = StaffLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.user_cache
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        redirect_url = request.POST.get('next') or reverse('store:admin_dashboard')
        success_message = f"Session Manager ouverte pour {user.get_full_name().strip() or user.username}."
        messages.success(request, success_message)

        if _wants_json(request):
            return JsonResponse(_auth_success_payload(user, redirect_url, success_message))
        return redirect(redirect_url)

    return render(
        request,
        'accounts/manager_login.html',
        {
            'form': form,
            'next': request.GET.get('next') or request.POST.get('next', ''),
        },
    )




def customer_signup_view(request):
    """Creation de compte client, puis envoi du code OTP."""

    if request.user.is_authenticated:
        return redirect(_resolve_redirect_target(request, request.user))

    if request.method != 'POST' and not _wants_json(request):
        return redirect('store:catalog')

    form = CustomerSignupForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            customer_group, _ = Group.objects.get_or_create(name='Customer')
            user.groups.add(customer_group)
            
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        success_message = 'Votre compte client a été créé avec succès.'
        messages.success(request, success_message)
        
        redirect_url = _resolve_redirect_target(request, user)
        if _wants_json(request):
            return JsonResponse(_auth_success_payload(user, redirect_url, success_message))
        return redirect(redirect_url)

    if _wants_json(request):
        return JsonResponse({'success': False, 'errors': _serialize_form_errors(form)}, status=400)

    messages.error(request, 'Impossible de creer le compte client.')
    return redirect('store:catalog')


def signup_view(request):
    """Inscription manager simplifiee, avec verification OTP."""

    if request.user.is_authenticated:
        return redirect(_resolve_redirect_target(request, request.user))

    form = ManagerSignupForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user, shop = form.save()
            manager_group, _ = Group.objects.get_or_create(name='Manager')
            user.groups.add(manager_group)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f"Boutique '{shop.name}' créée avec succès. Bienvenue on board !")
        
        return redirect('store:admin_dashboard')

    return render(request, 'accounts/signup.html', {'form': form})


@manager_required
def create_invitation_view(request):
    """Inviter un membre du personnel par email."""

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

    current_shop = request.user.profile.shop
    if not current_shop:
        return JsonResponse({'success': False, 'error': "Aucune boutique n'est liee a ce manager."}, status=400)

    form = StaffInvitationForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': _serialize_form_errors(form)}, status=400)

    # The selected role is fixed by the invitation and cannot be changed by the recipient.
    requested_role = form.cleaned_data['role']
    if requested_role == '__never__':
        return JsonResponse({'success': False, 'error': 'Vous n\'êtes pas autorisé à inviter un Manager.'}, status=403)

    invitation = CashierInvitation.objects.create(
        created_by=request.user,
        email=form.cleaned_data['email'],
        first_name=form.cleaned_data['first_name'].strip(),
        last_name=form.cleaned_data['last_name'].strip(),
        role=requested_role,
    )

    invite_path = reverse('accounts:register_cashier', args=[str(invitation.token)])
    invite_url = _build_public_absolute_uri(request, invite_path)
    send_staff_invitation_email(invitation, invite_url, current_shop.name)

    return JsonResponse(
        {
            'success': True,
            'invite_url': invite_url,
            'token': str(invitation.token),
            'role_label': invitation.get_role_display(),
            'email': invitation.email,
            'message': f"Invitation envoyee a {invitation.email}.",
        }
    )


def register_cashier_view(request, token):
    """Inscription du personnel via invitation email."""

    try:
        invitation = CashierInvitation.objects.get(token=token)
    except CashierInvitation.DoesNotExist:
        return render(request, 'accounts/invitation_invalid.html', {'reason': 'not_found'})

    if invitation.is_used:
        return render(request, 'accounts/invitation_invalid.html', {'reason': 'used', 'invitation': invitation})

    if invitation.is_expired:
        return render(request, 'accounts/invitation_invalid.html', {'reason': 'expired', 'invitation': invitation})

    form = StaffInvitationRegistrationForm(invitation, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            invitation.first_name = form.cleaned_data['first_name'].strip()
            invitation.last_name = form.cleaned_data['last_name'].strip()
            invitation.is_used = True
            invitation.used_by = user
            invitation.save(
                update_fields=['first_name', 'last_name', 'is_used', 'used_by']
            )

        messages.success(
            request,
            "Compte activé. Vous pouvez maintenant vous connecter à l'espace personnel.",
        )
        if request.user.is_authenticated:
            if _is_staff_user(request.user):
                return redirect('accounts:user_list')
            return redirect(_default_redirect_for_user(request.user))
        return redirect('accounts:manager_login')

    return render(
        request,
        'accounts/register_cashier.html',
        {
            'form': form,
            'invitation': invitation,
        },
    )


@manager_required
def user_list(request):
    current_shop = request.user.profile.shop

    if not current_shop:
        messages.error(request, "Vous n'etes lie a aucune boutique.")
        return redirect('sales:pos')

    users = User.objects.filter(profile__shop=current_shop).select_related('profile').prefetch_related('groups')

    context = {
        'users': users,
        'total_users': users.count(),
        'managers': users.filter(groups__name='Manager').distinct().count(),
        'cashiers': users.filter(groups__name='Cashier').distinct().count(),
        'active_count': users.filter(is_active=True).count(),
        'pending_count': users.filter(is_active=False).count(),
        'shop_name': current_shop.name,
        'invitation_form': StaffInvitationForm(),
    }
    return render(request, 'accounts/user_list.html', context)


@manager_required
def user_toggle_active(request, user_id):
    try:
        user_to_toggle = User.objects.get(id=user_id)

        if user_to_toggle.profile.shop != request.user.profile.shop:
            messages.error(request, 'Action non autorisee sur cet utilisateur.')
            return redirect('accounts:user_list')

        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save(update_fields=['is_active'])

        status = 'active' if user_to_toggle.is_active else 'desactive'
        messages.success(request, f'Utilisateur {user_to_toggle.username} {status}.')
    except User.DoesNotExist:
        messages.error(request, 'Utilisateur introuvable.')

    return redirect('accounts:user_list')


@login_required
def profile_view(request):
    form = ProfileUpdateForm(request.user, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, 'Profil mis a jour avec succes.')
        return redirect('accounts:profile')

    staff_metrics = None
    if _is_staff_user(request.user):
        from django.db.models import Sum
        from sales.models import Sale

        sales_queryset = Sale.objects.filter(cashier=request.user, is_cancelled=False)
        sales_total = sales_queryset.aggregate(total=Sum('total'))
        last_sale = sales_queryset.order_by('-sale_date').first()
        staff_metrics = {
            'sales_count': sales_queryset.count(),
            'sales_total': sales_total.get('total') or 0,
            'last_sale': last_sale,
        }

    context = {
        'user': request.user,
        'groups': request.user.groups.all(),
        'roles': roles_for_user(request.user),
        'role_label': role_label_for_user(request.user),
        'profile': request.user.profile,
        'form': form,
        'staff_metrics': staff_metrics,
    }
    return render(request, 'accounts/profile.html', context)


@manager_required
def cashier_dashboard_view(request, cashier_id):
    cashier = get_object_or_404(User, id=cashier_id)

    if not cashier.groups.filter(name='Cashier').exists() and not cashier.is_staff:
        messages.warning(request, "Cet utilisateur n'est pas un caissier.")

    from sales.models import Sale
    from .models import UserActivity

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    sales_today = Sale.objects.filter(cashier=cashier, sale_date__date=today)
    sales_week = Sale.objects.filter(cashier=cashier, sale_date__date__gte=start_of_week)
    sales_month = Sale.objects.filter(cashier=cashier, sale_date__date__gte=start_of_month)

    total_today = sum(s.total for s in sales_today)
    total_week = sum(s.total for s in sales_week)
    total_month = sum(s.total for s in sales_month)

    context = {
        'cashier': cashier,
        'stats': {
            'today': {'count': sales_today.count(), 'total': total_today},
            'week': {'count': sales_week.count(), 'total': total_week},
            'month': {'count': sales_month.count(), 'total': total_month},
        },
        'activities': UserActivity.objects.filter(user=cashier)[:50],
        'recent_sales': Sale.objects.filter(cashier=cashier).order_by('-sale_date')[:10],
    }
    return render(request, 'accounts/cashier_dashboard.html', context)
