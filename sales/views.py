# sales/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import cashier_required
from products.models import Product
from .models import Sale, SaleItem
import json


@cashier_required
def pos_view(request):
    """
    Écran de caisse (Point of Sale)
    Accessible aux caissiers et managers
    """
    from products.models import Category  # Ensure import

    user_shop = request.user.profile.shop
    # Récupérer tous les produits actifs pour la recherche
    products = Product.objects.filter(shop=user_shop, is_active=True).select_related('category')
    categories = Category.objects.filter(shop=user_shop)
    
    context = {
        'page_title': 'Caisse enregistreuse',
        'products': products,
        'categories': categories,
        'payment_methods': Sale.PAYMENT_METHODS,
    }
    return render(request, 'sales/pos.html', context)


@cashier_required
def search_products(request):
    """
    API pour rechercher des produits (AJAX)
    Retourne les produits en JSON
    """
    query = request.GET.get('q', '').strip()
    exact_match = request.GET.get('exact') == 'true'
    user_shop = request.user.profile.shop
    
    if not query:
        return JsonResponse({'products': []})
    
    if exact_match:
        # Recherche exacte par code-barres uniquement (pour le scanner)
        products = Product.objects.filter(shop=user_shop, is_active=True, barcode__iexact=query)
    else:
        # Recherche standard (Nom ou Code-barres partiel)
        products = Product.objects.filter(
            shop=user_shop, is_active=True
        ).filter(
            name__icontains=query
        ) | Product.objects.filter(
            shop=user_shop, is_active=True,
            barcode__icontains=query
        )
    
    # Limiter à 10 résultats
    products = products.select_related('category')[:10]
    
    # Convertir en JSON
    products_data = [{
        'id': p.id,
        'name': p.name,
        'barcode': p.barcode,
        'category': p.category.name if p.category else '',
        'price': float(p.selling_price),
        'stock': p.current_stock,
        'image': p.image.url if p.image else None,
    } for p in products]
    
    return JsonResponse({'products': products_data})


@cashier_required
@transaction.atomic
def validate_sale(request):
    """
    Valider une vente et créer les objets Sale + SaleItem
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Récupérer les données du panier
        data = json.loads(request.body)
        cart_items = data.get('cart', [])
        payment_method = data.get('payment_method', 'CASH')
        
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Le panier est vide'})
        
        # Créer la vente
        sale = Sale.objects.create(
            shop=request.user.profile.shop,
            cashier=request.user,
            payment_method=payment_method,
            total=0  # Sera calculé automatiquement
        )
        
        # Créer les lignes de vente
        total = 0
        for item in cart_items:
            product = get_object_or_404(Product, id=item['product_id'])
            quantity = int(item['quantity'])
            
            # Vérifier le stock
            if product.current_stock < quantity:
                sale.delete()  # Annuler la vente
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuffisant pour {product.name} (disponible: {product.current_stock})'
                })
            
            # Créer la ligne de vente
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=product.selling_price,
                subtotal=quantity * product.selling_price
            )
            
            total += quantity * product.selling_price
        
        # Le total et la déduction du stock sont gérés automatiquement par le modèle
        sale.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'sale_id': sale.id,
            'total': float(sale.total),
            'redirect_url': reverse('sales:receipt', args=[sale.id])
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données invalides'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f"Erreur serveur: {str(e)}"}, status=500)


@cashier_required
def receipt_view(request, sale_id):
    """
    Afficher le ticket de caisse
    """
    # Security: Ensure sale belongs to user's shop
    # We allow cashiers to see receipts from their shop
    try:
        user_shop = request.user.profile.shop
        sale = Sale.objects.get(id=sale_id, shop=user_shop)
    except Sale.DoesNotExist:
        messages.error(request, "Vente introuvable ou accès refusé.")
        return redirect('sales:pos')
        
    items = sale.items.select_related('product').all()
    
    context = {
        'sale': sale,
        'items': items,
        'shop': user_shop
    }
    
    return render(request, 'sales/receipt.html', context)


@login_required
def sales_history_view(request):
    """Historique des ventes avec filtres"""
    from django.contrib.auth.models import User
    from datetime import datetime, timedelta
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    cashier_id = request.GET.get('cashier')
    payment_method = request.GET.get('payment_method')
    
    user_shop = request.user.profile.shop
    
    # Filter by Shop
    sales = Sale.objects.filter(shop=user_shop).select_related('cashier').prefetch_related('items__product')
    
    if start_date:
        sales = sales.filter(sale_date__gte=start_date)
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        sales = sales.filter(sale_date__lt=end_date_obj)
    if cashier_id:
        sales = sales.filter(cashier_id=cashier_id)
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    
    sales = sales.order_by('-sale_date')
    total_sales = sales.count()
    total_amount = sum(sale.total for sale in sales)
    
    # Filter cashiers by shop
    cashiers = User.objects.filter(profile__shop=user_shop)
    
    context = {
        'sales': sales,
        'cashiers': cashiers,
        'payment_methods': Sale.PAYMENT_METHODS,
        'total_sales': total_sales,
        'total_amount': total_amount,
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'cashier': cashier_id,
            'payment_method': payment_method,
        }
    }
    return render(request, 'sales/sales_history.html', context)
