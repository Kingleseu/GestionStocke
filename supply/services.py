import json
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from accounts.models import Shop

from .models import (
    Hub,
    HubInventory,
    MerchantAccount,
    OrderTrackingEvent,
    ProcurementOrder,
    ProcurementOrderItem,
    SupplyProduct,
)


TERMINAL_ORDER_STATUSES = {'delivered', 'cancelled'}

STATUS_EVENT_LABELS = {
    'pending_payment': 'Paiement en attente',
    'awaiting_preparation': 'Commande validee pour preparation',
    'preparing': 'Preparation au hub',
    'ready_for_dispatch': 'Commande prete a expedier',
    'out_for_delivery': 'Commande en livraison',
    'delivered': 'Commande livree',
    'cancelled': 'Commande annulee',
}


def get_user_shop(user, merchant_name=''):
    if not user or not user.is_authenticated:
        return None

    profile = getattr(user, 'profile', None)
    if profile and profile.shop_id:
        return profile.shop

    shop_name = merchant_name or getattr(user, 'get_full_name', lambda: '')() or user.username
    shop, _ = Shop.objects.get_or_create(name=shop_name, created_by=user)
    if profile:
        profile.shop = shop
        profile.save(update_fields=['shop'])
    return shop


def find_hub_for_commune(commune):
    commune = (commune or '').strip()
    if commune:
        for hub in Hub.objects.filter(is_active=True):
            if hub.handles_commune(commune) or hub.commune.lower() == commune.lower():
                return hub
    return Hub.objects.filter(is_active=True).order_by('id').first()


def parse_cart_payload(raw_payload):
    try:
        payload = json.loads(raw_payload or '[]')
    except json.JSONDecodeError:
        raise ValueError('Panier invalide.')

    if not isinstance(payload, list) or not payload:
        raise ValueError('Le panier est vide.')

    parsed = []
    for item in payload:
        product_id = item.get('productId') or item.get('product_id') or item.get('id')
        quantity = item.get('quantity') or item.get('qty') or 0
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue
        if product_id > 0 and quantity > 0:
            parsed.append({'product_id': product_id, 'quantity': quantity})

    if not parsed:
        raise ValueError('Aucun produit valide dans le panier.')
    return parsed


def _release_reserved_stock(order):
    for item in order.items.select_related('product').all():
        if not item.product_id or not order.hub_id:
            continue
        inventory = HubInventory.objects.select_for_update().filter(hub=order.hub, product=item.product).first()
        if not inventory:
            continue
        inventory.reserved_quantity = max(inventory.reserved_quantity - item.quantity, 0)
        inventory.save(update_fields=['reserved_quantity', 'updated_at'])


def _commit_delivered_stock(order):
    for item in order.items.select_related('product').all():
        if not item.product_id or not order.hub_id:
            continue
        inventory = HubInventory.objects.select_for_update().filter(hub=order.hub, product=item.product).first()
        if not inventory:
            continue
        inventory.reserved_quantity = max(inventory.reserved_quantity - item.quantity, 0)
        inventory.available_quantity = max(inventory.available_quantity - item.quantity, 0)
        inventory.save(update_fields=['available_quantity', 'reserved_quantity', 'updated_at'])


@transaction.atomic
def transition_procurement_order(order, new_status, user=None, note=''):
    order = ProcurementOrder.objects.select_for_update().get(pk=order.pk)
    old_status = order.status

    if old_status in TERMINAL_ORDER_STATUSES and old_status != new_status:
        raise ValueError('Cette commande est deja cloturee.')

    valid_statuses = dict(ProcurementOrder.STATUS_CHOICES)
    if new_status not in valid_statuses:
        raise ValueError('Statut de commande invalide.')

    if old_status == new_status:
        if note:
            OrderTrackingEvent.objects.create(
                order=order,
                status=new_status,
                label='Note operation',
                note=note,
                created_by=user if getattr(user, 'is_authenticated', False) else None,
            )
        return order

    if new_status == 'cancelled':
        _release_reserved_stock(order)
    elif new_status == 'delivered':
        _commit_delivered_stock(order)
        order.escrow_released = order.payment_method != 'credit'

    order.status = new_status
    update_fields = ['status', 'updated_at']
    if new_status == 'delivered':
        update_fields.append('escrow_released')
    order.save(update_fields=update_fields)

    OrderTrackingEvent.objects.create(
        order=order,
        status=new_status,
        label=STATUS_EVENT_LABELS.get(new_status, valid_statuses[new_status]),
        note=note or f'Statut passe de {valid_statuses.get(old_status, old_status)} a {valid_statuses[new_status]}.',
        created_by=user if getattr(user, 'is_authenticated', False) else None,
    )
    return order


@transaction.atomic
def create_procurement_order(user, form_data):
    merchant_name = (form_data.get('merchant_name') or '').strip()
    commune = (form_data.get('commune') or '').strip()
    delivery_address = (form_data.get('delivery_address') or '').strip()
    contact_phone = (form_data.get('contact_phone') or '').strip()
    payment_method = (form_data.get('payment_method') or 'm-pesa').strip()
    payment_reference = (form_data.get('payment_reference') or '').strip()
    notes = (form_data.get('notes') or '').strip()
    cart_items = parse_cart_payload(form_data.get('cart_payload'))

    if not merchant_name:
        raise ValueError('Le nom de la boutique est obligatoire.')
    if not commune:
        raise ValueError('La commune de livraison est obligatoire.')
    if not delivery_address:
        raise ValueError("L'adresse de livraison est obligatoire.")
    if not contact_phone:
        raise ValueError('Le numero WhatsApp est obligatoire.')

    hub = find_hub_for_commune(commune)
    if not hub:
        raise ValueError('Aucun hub actif ne couvre encore cette zone.')

    shop = get_user_shop(user, merchant_name)
    if shop:
        account, _ = MerchantAccount.objects.get_or_create(shop=shop)
        account.commune = commune
        account.contact_phone = contact_phone
        account.whatsapp = contact_phone
        account.preferred_hub = hub
        account.save(update_fields=['commune', 'contact_phone', 'whatsapp', 'preferred_hub', 'updated_at'])

    status = 'pending_payment'
    if payment_method in {'credit', 'delivery-cash'}:
        status = 'awaiting_preparation'

    order = ProcurementOrder.objects.create(
        user=user if user.is_authenticated else None,
        shop=shop,
        hub=hub,
        merchant_name=merchant_name,
        commune=commune,
        delivery_address=delivery_address,
        contact_phone=contact_phone,
        payment_method=payment_method,
        payment_reference=payment_reference,
        delivery_fee=hub.delivery_fee,
        status=status,
        delivery_eta=timezone.now() + timedelta(days=1),
        notes=notes,
    )

    products = SupplyProduct.objects.filter(
        id__in=[item['product_id'] for item in cart_items],
        is_active=True,
    ).select_related('supplier').in_bulk()

    for item in cart_items:
        product = products.get(item['product_id'])
        if not product:
            raise ValueError('Un produit du panier est introuvable.')

        quantity = max(item['quantity'], product.minimum_order_quantity)
        inventory = HubInventory.objects.select_for_update().filter(hub=hub, product=product).first()
        if not inventory:
            raise ValueError(f'{product.name} n est pas disponible au {hub.name}.')
        if inventory.sellable_quantity < quantity:
            raise ValueError(
                f'Stock insuffisant pour {product.name}: {inventory.sellable_quantity} disponible(s) au {hub.name}.'
            )

        inventory.reserve(quantity)
        ProcurementOrderItem.objects.create(
            order=order,
            product=product,
            supplier=product.supplier,
            product_name=product.name,
            supplier_name=product.supplier.name,
            unit_label=product.unit_label,
            quantity=quantity,
            unit_price=product.wholesale_price,
        )

    order.recalculate_totals()
    if payment_method == 'credit':
        order.credit_amount = order.total_amount
        order.save(update_fields=['credit_amount', 'updated_at'])

    OrderTrackingEvent.objects.create(
        order=order,
        status='pending_payment',
        label='Commande enregistree',
        note=f'{hub.name} a recu la demande d approvisionnement.',
        created_by=user if user.is_authenticated else None,
    )
    OrderTrackingEvent.objects.create(
        order=order,
        status=status,
        label='Hub assigne',
        note=f'Preparation prevue depuis {hub.name}.',
        created_by=user if user.is_authenticated else None,
    )
    return order


def catalog_payload():
    rows = []
    products = (
        SupplyProduct.objects.filter(is_active=True)
        .select_related('supplier', 'supply_category')
        .prefetch_related('hub_inventories__hub')
        .order_by('supply_category__order', 'supply_category__name', 'name')
    )
    for product in products:
        total_sellable = sum(inv.sellable_quantity for inv in product.hub_inventories.all() if inv.hub.is_active)
        hubs = [
            {
                'name': inv.hub.name,
                'code': inv.hub.code,
                'quantity': inv.sellable_quantity,
                'status': inv.stock_status,
            }
            for inv in product.hub_inventories.all()
            if inv.hub.is_active
        ]
        rows.append({
            'id': product.id,
            'name': product.name,
            'brand': product.brand or product.supplier.name,
            'supplier': product.supplier.name,
            'category': str(product.supply_category_id or ''),
            'categoryLabel': product.supply_category.name if product.supply_category_id else '',
            'unit': product.unit_label,
            'price': float(product.wholesale_price),
            'priceLabel': product.price_label,
            'currency': product.currency,
            'minQty': product.minimum_order_quantity,
            'icon': product.icon_class,
            'available': total_sellable,
            'hubs': hubs,
        })
    return rows


def merchant_dashboard_context(user):
    shop = get_user_shop(user) if user.is_authenticated else None
    merchant_account = getattr(shop, 'merchant_account', None) if shop else None
    orders = ProcurementOrder.objects.none()
    if shop:
        orders = ProcurementOrder.objects.filter(shop=shop).prefetch_related('items')
    else:
        orders = ProcurementOrder.objects.filter(user=user).prefetch_related('items')

    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_orders = orders.filter(created_at__gte=month_start)
    monthly_total = sum((order.total_amount for order in monthly_orders), Decimal('0.00'))

    low_stock = HubInventory.objects.filter(
        product__is_active=True,
        available_quantity__lte=models_f('reserved_quantity') + models_f('reorder_threshold'),
    ).select_related('product', 'hub')[:6]

    return {
        'shop': shop,
        'merchant_account': merchant_account,
        'orders': orders[:8],
        'orders_count': orders.count(),
        'monthly_orders_count': monthly_orders.count(),
        'monthly_total': monthly_total,
        'next_order': orders.exclude(status__in=['delivered', 'cancelled']).first(),
        'low_stock_hub_items': low_stock,
    }


def models_f(field_name):
    from django.db.models import F

    return F(field_name)
