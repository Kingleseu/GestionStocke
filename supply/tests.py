import json
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Shop

from .models import Hub, HubInventory, MerchantAccount, ProcurementOrder, Supplier, SupplyCategory, SupplyProduct
from .services import create_procurement_order, find_hub_for_commune, transition_procurement_order


class ProcurementOrderServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vendor', password='pass')
        self.hub = Hub.objects.create(
            name='Hub Est',
            code='EST',
            commune='Ndjili',
            coverage_communes=['Ndjili', 'Masina'],
            delivery_fee=Decimal('3.00'),
        )
        self.supplier = Supplier.objects.create(name='Bralima', category='beverages')
        self.product = SupplyProduct.objects.create(
            supplier=self.supplier,
            name='Primus 65cl',
            category='beverages',
            unit_label='caisse 24 bouteilles',
            wholesale_price=Decimal('32.00'),
        )
        self.inventory = HubInventory.objects.create(
            hub=self.hub,
            product=self.product,
            available_quantity=10,
            reserved_quantity=0,
            reorder_threshold=2,
        )

    def _payload(self, quantity=2):
        return {
            'merchant_name': 'Depot Fraicheur',
            'commune': 'Ndjili',
            'delivery_address': 'Av Test',
            'contact_phone': '0810000000',
            'payment_method': 'm-pesa',
            'cart_payload': json.dumps([
                {'productId': self.product.id, 'quantity': quantity},
            ]),
        }

    def test_find_hub_for_commune_uses_coverage(self):
        self.assertEqual(find_hub_for_commune('Masina'), self.hub)

    def test_create_order_reserves_hub_stock(self):
        order = create_procurement_order(self.user, self._payload(quantity=2))

        self.assertTrue(order.order_number.startswith('PB-'))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.subtotal, Decimal('64.00'))
        self.assertEqual(order.total_amount, Decimal('67.00'))
        self.assertEqual(order.status, 'pending_payment')
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.reserved_quantity, 2)
        self.assertEqual(order.tracking_events.count(), 2)

    def test_create_order_rejects_insufficient_stock(self):
        with self.assertRaisesMessage(ValueError, 'Stock insuffisant'):
            create_procurement_order(self.user, self._payload(quantity=20))

    def test_cancelled_order_releases_reserved_stock(self):
        order = create_procurement_order(self.user, self._payload(quantity=3))

        transition_procurement_order(order, 'cancelled', user=self.user, note='Client indisponible')

        self.inventory.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
        self.assertEqual(self.inventory.available_quantity, 10)
        self.assertEqual(self.inventory.reserved_quantity, 0)

    def test_delivered_order_commits_reserved_stock(self):
        order = create_procurement_order(self.user, self._payload(quantity=4))

        transition_procurement_order(order, 'delivered', user=self.user, note='Reception confirmee')

        self.inventory.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')
        self.assertEqual(self.inventory.available_quantity, 6)
        self.assertEqual(self.inventory.reserved_quantity, 0)


class SupplyOpsViewTests(TestCase):
    def setUp(self):
        self._media_root = tempfile.mkdtemp()
        self._media_override = override_settings(MEDIA_ROOT=self._media_root)
        self._media_override.enable()
        self.manager = User.objects.create_superuser(username='ops', password='pass', email='ops@example.com')
        self.supplier = Supplier.objects.create(name='Bralima', category='beverages')
        self.hub = Hub.objects.create(name='Hub Est', code='EST', commune='Ndjili')
        product = SupplyProduct.objects.create(
            supplier=self.supplier,
            name='Primus',
            category='beverages',
            unit_label='caisse 24 bouteilles',
            wholesale_price=32,
        )
        HubInventory.objects.create(hub=self.hub, product=product, available_quantity=20, reserved_quantity=0)
        self.shop = Shop.objects.create(
            name='Depot Test',
            created_by=self.manager,
            address='Av Test',
            phone='0810000000',
            email='depot@example.com',
        )
        self.merchant = MerchantAccount.objects.create(
            shop=self.shop,
            owner_full_name='Jean Manager',
            commune='Ndjili',
            contact_phone='0810000000',
            secondary_phone='0820000000',
            whatsapp='0810000000',
            whatsapp_active=True,
            shop_type=MerchantAccount.SHOP_TYPE_DEPOT,
            business_age=MerchantAccount.AGE_OVER_12_MONTHS,
            preferred_hub=self.hub,
        )

    def tearDown(self):
        self._media_override.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)
        super().tearDown()

    def _photo(self, name='devanture.jpg'):
        return SimpleUploadedFile(name, b'fake storefront image', content_type='image/jpeg')

    def _signup_payload(self, **overrides):
        data = {
            'shop_name': 'Depot Nouveau',
            'owner_full_name': 'Jean Mbuyi',
            'email': 'jean@example.com',
            'phone': '0810000000',
            'secondary_phone': '0820000000',
            'whatsapp_active': 'yes',
            'shop_type': MerchantAccount.SHOP_TYPE_NEIGHBORHOOD,
            'business_age': MerchantAccount.AGE_6_TO_12_MONTHS,
            'storefront_photo': self._photo(),
            'commune': 'Ndjili',
            'address': 'Av Test',
            'password': 'StrongPass123',
            'password_confirm': 'StrongPass123',
        }
        data.update(overrides)
        return data

    def test_ops_pages_render_for_manager(self):
        self.client.force_login(self.manager)
        urls = [
            reverse('supply:ops_dashboard'),
            reverse('supply:ops_site_content'),
            reverse('supply:ops_merchants'),
            reverse('supply:ops_suppliers'),
            reverse('supply:ops_hubs'),
            reverse('supply:ops_products'),
            reverse('supply:ops_inventory'),
            reverse('supply:ops_orders'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_ops_backoffice_uses_single_global_navigation(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('supply:ops_products'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'pb-ops-nav')
        self.assertContains(response, 'Catalogue fournisseurs')

    def test_ops_crud_actions_are_modal_triggers(self):
        self.client.force_login(self.manager)
        urls = [
            reverse('supply:ops_categories'),
            reverse('supply:ops_suppliers'),
            reverse('supply:ops_hubs'),
            reverse('supply:ops_products'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'data-modal')

    def test_ajax_modal_get_returns_form_fragment(self):
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse('supply:ops_supplier_add'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pb-modal-form')
        self.assertNotContains(response, 'pb-page-head')

    def test_ajax_modal_post_creates_category(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse('supply:ops_category_add'),
            {
                'name': 'Produits frais',
                'description': 'Rayon froid',
                'is_active': 'on',
                'order': '3',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'success': True,
            'redirect_url': reverse('supply:ops_categories'),
            'object_id': SupplyCategory.objects.get(name='Produits frais').pk,
        })

    def test_manager_sees_merchant_overview(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('supply:ops_merchants'))

        self.assertContains(response, 'Depot Test')
        self.assertContains(response, 'Ndjili')

    def test_manager_can_open_merchant_signup_form(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('supply:register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Information sur le point de vente')
        self.assertContains(response, 'Etape 1')
        self.assertContains(response, 'Etape 2')
        self.assertContains(response, 'Etape 3')
        self.assertContains(response, 'data-step-next')
        self.assertContains(response, 'connecte comme manager')
        self.assertContains(response, 'Photo de la devanture du PDV')

    def test_public_catalog_uses_backoffice_categories(self):
        active_category = SupplyCategory.objects.create(name='Boissons locales', is_active=True, order=1)
        SupplyCategory.objects.create(name='Categorie masquee', is_active=False, order=2)
        self.supplier.supply_category = active_category
        self.supplier.save(update_fields=['supply_category'])
        product = SupplyProduct.objects.get(name='Primus')
        product.supply_category = active_category
        product.save(update_fields=['supply_category'])

        response = self.client.get(reverse('supply:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-category="%s"' % active_category.pk)
        self.assertContains(response, 'Boissons locales')
        self.assertNotContains(response, 'Categorie masquee')
        self.assertNotContains(response, 'data-category="beverages"')

    def test_public_catalog_renders_horizontal_cart_dock(self):
        response = self.client.get(reverse('supply:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cartDock"')
        self.assertContains(response, 'id="cartToggle"')
        self.assertContains(response, 'pb-cart-horizontal')
        self.assertContains(response, 'bi-cart3')

    def test_manager_can_create_merchant_without_losing_session(self):
        self.client.force_login(self.manager)

        response = self.client.post(reverse('supply:register'), self._signup_payload(
            shop_name='Depot Manager',
            owner_full_name='Paul Kazadi',
            email='paul@example.com',
            phone='0810000002',
            commune='Gombe',
            address='Av Manager',
            storefront_photo=self._photo('manager-front.jpg'),
        ))

        self.assertRedirects(response, reverse('supply:ops_merchants'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.manager.id)
        self.assertTrue(User.objects.filter(email='paul@example.com', profile__shop__name='Depot Manager').exists())

    def test_existing_merchant_is_redirected_from_signup_to_dashboard(self):
        merchant = User.objects.create_user(username='merchant-test', email='merchant-test@example.com', password='pass')
        shop = Shop.objects.create(name='Depot Existing', created_by=merchant)
        merchant.profile.shop = shop
        merchant.profile.save(update_fields=['shop', 'updated_at'])
        MerchantAccount.objects.create(shop=shop, commune='Masina')
        self.client.force_login(merchant)

        response = self.client.get(reverse('supply:register'))

        self.assertRedirects(response, reverse('supply:dashboard'))

    def test_merchant_can_create_shop(self):
        response = self.client.post(reverse('supply:register'), self._signup_payload(
            shop_name='Depot Public',
            owner_full_name='Jean Mbuyi',
            email='jean@example.com',
            phone='0810000000',
            whatsapp_active='no',
            shop_type=MerchantAccount.SHOP_TYPE_PHARMACY,
            business_age=MerchantAccount.AGE_3_TO_6_MONTHS,
            commune='Ndjili',
            address='Av Test',
            storefront_photo=self._photo('depot-test.jpg'),
        ))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='jean@example.com', profile__shop__name='Depot Public').exists())
        account = MerchantAccount.objects.get(shop__name='Depot Public')
        self.assertEqual(account.owner_full_name, 'Jean Mbuyi')
        self.assertEqual(account.shop_type, MerchantAccount.SHOP_TYPE_PHARMACY)
        self.assertEqual(account.business_age, MerchantAccount.AGE_3_TO_6_MONTHS)
        self.assertFalse(account.whatsapp_active)
        self.assertEqual(account.whatsapp, '')
        self.assertFalse(account.is_prequalified)
        self.assertTrue(account.storefront_photo.name.startswith('supply/storefronts/'))

    def test_merchant_dashboard_links_profile_and_logout(self):
        self.client.post(reverse('supply:register'), self._signup_payload(
            shop_name='Depot Mobile',
            owner_full_name='Jeanne Mbuyi',
            email='jeanne@example.com',
            phone='0810000001',
            commune='Masina',
            address='Av Marche',
            storefront_photo=self._photo('mobile-front.jpg'),
        ))

        response = self.client.get(reverse('supply:dashboard'))

        self.assertContains(response, reverse('accounts:profile') + '#profile-settings')
        self.assertContains(response, 'Se deconnecter')

    def test_manager_can_view_merchant_activity_detail(self):
        ProcurementOrder.objects.create(
            user=self.manager,
            shop=self.shop,
            hub=self.hub,
            merchant_name='Depot Test',
            commune='Ndjili',
            delivery_address='Av Test',
            contact_phone='0810000000',
            total_amount=Decimal('50.00'),
            status='awaiting_preparation',
        )
        self.client.force_login(self.manager)

        response = self.client.get(reverse('supply:ops_merchant_detail', args=[self.merchant.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fiche point de vente')
        self.assertContains(response, 'Depot Test')
        self.assertContains(response, 'Prequalifie')
        self.assertContains(response, 'Dernieres commandes')
