from decimal import Decimal

from django.core.management.base import BaseCommand

from supply.models import (
    Hub,
    HubInventory,
    Supplier,
    SupplyHomeFeature,
    SupplyHomepageStat,
    SupplyProcessStep,
    SupplyProduct,
    SupplySiteSettings,
)


class Command(BaseCommand):
    help = 'Charge un catalogue demo PEMBENY avec fournisseurs, hubs, produits et stocks.'

    def handle(self, *args, **options):
        hubs_data = [
            {
                'code': 'EST',
                'name': 'Hub Est',
                'commune': 'Ndjili',
                'coverage_communes': ['Ndjili', 'Kimbaseke', 'Masina', 'Nsele'],
                'delivery_fee': Decimal('3.00'),
            },
            {
                'code': 'CENTRE',
                'name': 'Hub Centre',
                'commune': 'Gombe',
                'coverage_communes': ['Gombe', 'Lingwala', 'Barumbu', 'Kasa-Vubu'],
                'delivery_fee': Decimal('4.00'),
            },
            {
                'code': 'SUD',
                'name': 'Hub Sud',
                'commune': 'Lemba',
                'coverage_communes': ['Lemba', 'Matete', 'Limete', 'Mont-Ngafula'],
                'delivery_fee': Decimal('3.50'),
            },
            {
                'code': 'OUEST',
                'name': 'Hub Ouest',
                'commune': 'Ngaliema',
                'coverage_communes': ['Ngaliema', 'Kintambo', 'Bumbu', 'Ngiri-Ngiri'],
                'delivery_fee': Decimal('4.50'),
            },
        ]

        hubs = {}
        for data in hubs_data:
            hub, _ = Hub.objects.update_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'commune': data['commune'],
                    'coverage_communes': data['coverage_communes'],
                    'delivery_fee': data['delivery_fee'],
                    'is_active': True,
                },
            )
            hubs[data['code']] = hub

        suppliers_data = [
            ('Bralima / Heineken', 'beverages'),
            ('Pepsi / BECO', 'beverages'),
            ('Marsavco', 'hygiene'),
            ('Beltexco', 'food'),
            ('Minocongo', 'flour'),
            ('Swissta', 'snacks'),
        ]

        suppliers = {}
        for name, category in suppliers_data:
            supplier, _ = Supplier.objects.update_or_create(
                name=name,
                defaults={'category': category, 'is_active': True},
            )
            suppliers[name] = supplier

        products_data = [
            ('Primus 65cl', 'Bralima / Heineken', 'beverages', 'caisse 24 bouteilles', Decimal('32.00'), 'bi-cup-straw', {'EST': 95, 'CENTRE': 40}),
            ('Skol 65cl', 'Bralima / Heineken', 'beverages', 'caisse 24 bouteilles', Decimal('30.00'), 'bi-cup-straw', {'EST': 70, 'OUEST': 35}),
            ('Nkoyi 65cl', 'Bralima / Heineken', 'beverages', 'caisse 24 bouteilles', Decimal('28.00'), 'bi-cup-straw', {'EST': 52}),
            ('Coca-Cola 50cl', 'Pepsi / BECO', 'beverages', 'caisse 24 bouteilles', Decimal('28.00'), 'bi-cup-straw', {'CENTRE': 86, 'SUD': 48}),
            ('Fanta Orange 50cl', 'Pepsi / BECO', 'beverages', 'caisse 24 bouteilles', Decimal('26.00'), 'bi-cup-straw', {'CENTRE': 64}),
            ('Sprite 50cl', 'Pepsi / BECO', 'beverages', 'caisse 24 bouteilles', Decimal('26.00'), 'bi-cup-straw', {'CENTRE': 54}),
            ('Indomie Poulet', 'Beltexco', 'food', 'boite 40 paquets', Decimal('22.00'), 'bi-box2-heart', {'SUD': 110, 'EST': 62}),
            ('Indomie Legumes', 'Beltexco', 'food', 'boite 40 paquets', Decimal('22.00'), 'bi-box2-heart', {'SUD': 94}),
            ('Jumbo Cube x100', 'Beltexco', 'food', 'boite 100 cubes', Decimal('18.00'), 'bi-basket', {'SUD': 68, 'CENTRE': 34}),
            ('Savon Omo 1kg', 'Marsavco', 'hygiene', 'carton 20 pieces', Decimal('45.00'), 'bi-droplet', {'OUEST': 72}),
            ('Savon Lux 150g', 'Marsavco', 'hygiene', 'carton 48 pieces', Decimal('38.00'), 'bi-droplet-half', {'OUEST': 66, 'CENTRE': 24}),
            ('Shampoing Palmolive', 'Marsavco', 'hygiene', 'carton 24 bouteilles', Decimal('52.00'), 'bi-droplet', {'OUEST': 42}),
            ('Farine Ngola 25kg', 'Minocongo', 'flour', 'sac 25kg', Decimal('35.00'), 'bi-bag', {'EST': 58, 'SUD': 31}),
            ('Farine Ngola 50kg', 'Minocongo', 'flour', 'sac 50kg', Decimal('65.00'), 'bi-bag-fill', {'EST': 32}),
            ('Biscuits Swissta x24', 'Swissta', 'snacks', 'carton 24 paquets', Decimal('19.00'), 'bi-box', {'CENTRE': 80, 'OUEST': 37}),
            ('Chocolat Swissta x24', 'Swissta', 'snacks', 'carton 24 pieces', Decimal('24.00'), 'bi-box', {'CENTRE': 44}),
        ]

        for index, (name, supplier_name, category, unit, price, icon, stock_map) in enumerate(products_data, start=1):
            product, _ = SupplyProduct.objects.update_or_create(
                supplier=suppliers[supplier_name],
                name=name,
                defaults={
                    'brand': supplier_name,
                    'category': category,
                    'unit_label': unit,
                    'wholesale_price': price,
                    'currency': 'USD',
                    'minimum_order_quantity': 1,
                    'icon_class': icon,
                    'is_active': True,
                    'is_featured': index <= 6,
                },
            )
            for hub_code, quantity in stock_map.items():
                HubInventory.objects.update_or_create(
                    hub=hubs[hub_code],
                    product=product,
                    defaults={
                        'available_quantity': quantity,
                        'reserved_quantity': 0,
                        'reorder_threshold': 12,
                    },
                )

        settings = SupplySiteSettings.get_solo()
        settings.hero_badge = 'Reseau d approvisionnement - Kinshasa'
        settings.hero_title = 'Votre boutique peut commander chez les grands fournisseurs sans quitter son quartier.'
        settings.hero_subtitle = (
            'PEMBENY connecte les vendeurs, fournisseurs et hubs de distribution dans une seule plateforme. '
            'Creez votre boutique, commandez par carton ou caisse, puis suivez la preparation jusqu a la livraison.'
        )
        settings.network_title = 'Une seule plateforme pour fournisseurs, hubs et boutiques'
        settings.network_subtitle = (
            'Le vendeur commande dans PEMBENY. Le systeme choisit le hub le plus proche, reserve le stock, '
            'puis l equipe operations suit la preparation et la livraison.'
        )
        settings.save()

        stats_data = [
            ('1 000+', 'boutiques visees'),
            ('4', 'hubs Kinshasa'),
            ('6+', 'fournisseurs partenaires'),
            ('J+1', 'livraison cible'),
        ]
        for order, (value, label) in enumerate(stats_data, start=1):
            SupplyHomepageStat.objects.update_or_create(
                order=order,
                defaults={'value': value, 'label': label, 'is_active': True},
            )

        features_data = [
            ('bi-boxes', 'Inventaire centralise', 'Produits fournisseurs, disponibilite par hub et prix gros dans une seule interface.', 'Fournisseurs + hubs'),
            ('bi-truck', 'Livraison hub', 'La commande est orientee vers le hub qui couvre la commune de la boutique.', 'J+1 cible'),
            ('bi-credit-card', 'Paiement flexible', 'Mobile Money, paiement livraison, virement ou credit marchandises selon accord.', 'B2B'),
            ('bi-graph-up-arrow', 'Pilotage boutique', 'Historique, suivi et alertes stock pour aider le vendeur a se reapprovisionner.', 'Espace boutique'),
        ]
        for order, (icon, title, body, badge) in enumerate(features_data, start=1):
            SupplyHomeFeature.objects.update_or_create(
                order=order,
                defaults={'icon_class': icon, 'title': title, 'body': body, 'badge': badge, 'is_active': True},
            )

        process_data = [
            (1, 'Creez votre boutique', 'Le vendeur ouvre son compte, indique sa commune et ses coordonnees WhatsApp.', 'bi-shop'),
            (2, 'Commandez au catalogue', 'Il choisit les produits disponibles par fournisseur, caisse, carton ou sac.', 'bi-cart-check'),
            (3, 'Preparation au hub', 'Le stock est reserve et l equipe hub prepare la commande.', 'bi-box-seam'),
            (4, 'Livraison et confirmation', 'Apres reception, le stock hub est deduit et le suivi est cloture.', 'bi-check-circle'),
        ]
        for order, (number, title, body, icon) in enumerate(process_data, start=1):
            SupplyProcessStep.objects.update_or_create(
                order=order,
                defaults={'number': number, 'title': title, 'body': body, 'icon_class': icon, 'is_active': True},
            )

        self.stdout.write(self.style.SUCCESS('Catalogue PEMBENY demo charge avec succes.'))
