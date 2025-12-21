# purchases/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from accounts.decorators import manager_required
from django.utils.decorators import method_decorator
from products.models import Product
from .models import Purchase, PurchaseItem
import json


@method_decorator(manager_required, name='dispatch')
@method_decorator(manager_required, name='dispatch')
class PurchaseListView(ListView):
    """Liste de tous les achats"""
    model = Purchase
    template_name = 'purchases/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 20
    ordering = ['-purchase_date']
    
    def get_queryset(self):
        user_shop = self.request.user.profile.shop
        return Purchase.objects.filter(shop=user_shop).order_by('-purchase_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_shop = self.request.user.profile.shop
        # Statistiques (Filtrées par shop)
        all_purchases = Purchase.objects.filter(shop=user_shop)
        context['total_purchases'] = all_purchases.count()
        context['total_amount'] = sum(p.total for p in all_purchases)
        context['received_count'] = all_purchases.filter(is_received=True).count()
        context['pending_count'] = all_purchases.filter(is_received=False).count()
        
        return context


@manager_required
def purchase_create_view(request):
    """
    Créer un nouvel achat avec lignes d'articles dynamiques
    """
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            supplier = request.POST.get('supplier', '').strip()
            invoice_number = request.POST.get('invoice_number', '').strip()
            notes = request.POST.get('notes', '').strip()
            is_received = request.POST.get('is_received') == 'on'
            
            # Récupérer les lignes d'articles (JSON)
            items_json = request.POST.get('items_data', '[]')
            items = json.loads(items_json)
            
            if not supplier:
                messages.error(request, 'Le nom du fournisseur est obligatoire.')
                return redirect('purchases:purchase_create')
            
            if not items:
                messages.error(request, 'Vous devez ajouter au moins un article.')
                return redirect('purchases:purchase_create')
            
            # Créer l'achat avec transaction atomique
            with transaction.atomic():
                purchase = Purchase.objects.create(
                    shop=request.user.profile.shop,
                    supplier=supplier,
                    invoice_number=invoice_number,
                    notes=notes,
                    is_received=is_received,
                    created_by=request.user,
                    total=0  # Sera calculé automatiquement
                )
                
                # Créer les lignes d'achat
                for item in items:
                    product = get_object_or_404(Product, id=item['product_id'])
                    # Verify product belongs to user's shop
                    if product.shop != request.user.profile.shop:
                        raise Exception("Produit invalide pour cette boutique")

                    quantity = int(item['quantity'])
                    purchase_price = float(item['price'])
                    
                    PurchaseItem.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=quantity,
                        purchase_price=purchase_price,
                        subtotal=quantity * purchase_price
                    )
                
                # Le total et l'ajout au stock sont gérés automatiquement par le modèle
                purchase.refresh_from_db()
                
                messages.success(request, f'Achat créé avec succès ! Total : {purchase.total}$')
                return redirect('purchases:purchase_detail', pk=purchase.id)
                
        except json.JSONDecodeError:
            messages.error(request, 'Erreur lors du traitement des articles.')
            return redirect('purchases:purchase_create')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
            return redirect('purchases:purchase_create')
    
    # GET : afficher le formulaire
    # Filter products by shop
    products = Product.objects.filter(shop=request.user.profile.shop, is_active=True).order_by('name')
    
    # Préparer les données pour le JS
    products_data = []
    for p in products:
        products_data.append({
            'id': p.id,
            'name': p.name,
            'barcode': p.barcode,
            'price': float(p.purchase_price)
        })
    
    context = {
        'products': products,
        'products_json': json.dumps(products_data),
    }
    
    return render(request, 'purchases/purchase_form.html', context)


@method_decorator(manager_required, name='dispatch')
class PurchaseDetailView(DetailView):
    """Détails d'un achat"""
    model = Purchase
    template_name = 'purchases/purchase_detail.html'
    context_object_name = 'purchase'
    
    def get_queryset(self):
        return Purchase.objects.filter(shop=self.request.user.profile.shop)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('product').all()
        return context


@manager_required
def purchase_toggle_received(request, pk):
    """Marquer un achat comme reçu/non reçu"""
    # Filter by shop
    purchase = get_object_or_404(Purchase, pk=pk, shop=request.user.profile.shop)
    
    # Si on marque comme reçu, ajouter au stock
    if not purchase.is_received:
        with transaction.atomic():
            for item in purchase.items.all():
                item.product.current_stock += item.quantity
                item.product.save()
            purchase.is_received = True
            purchase.save()
            messages.success(request, f'Achat #{purchase.id} marqué comme reçu. Stock mis à jour.')
    else:
        # Si on annule la réception, retirer du stock
        with transaction.atomic():
            for item in purchase.items.all():
                item.product.current_stock -= item.quantity
                item.product.save()
            purchase.is_received = False
            purchase.save()
            messages.warning(request, f'Réception annulée pour l\'achat #{purchase.id}. Stock mis à jour.')
    
    return redirect('purchases:purchase_detail', pk=purchase.id)
