from decimal import Decimal
from html.parser import HTMLParser
import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from products.models import Category, Product
from store.models import AdminNotification, CustomerProfile, ManualPayment, WebOrder


class MainContentNestingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.main_inside_mobile_menu = False

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        is_mobile_menu = attr_map.get('id') == 'mobileMenu'
        self.stack.append((tag, is_mobile_menu))

        if tag == 'main' and any(is_menu for _, is_menu in self.stack[:-1]):
            self.main_inside_mobile_menu = True

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            open_tag, _ = self.stack[index]
            if open_tag == tag:
                del self.stack[index:]
                break


class AdminNotificationTests(TestCase):
    def setUp(self):
        self.manager_group, _ = Group.objects.get_or_create(name='Manager')
        self.manager = User.objects.create_user(
            username='manager',
            password='secret123',
            is_staff=True,
        )
        self.manager.groups.add(self.manager_group)

        self.cashier = User.objects.create_user(
            username='cashier',
            password='secret123',
            is_staff=True,
        )

    def _create_order(self, **overrides):
        data = {
            'full_name': 'Client Test',
            'email': 'client@example.com',
            'phone': '+243000000000',
            'address': 'Adresse test',
            'city': 'Kinshasa',
            'total_amount': Decimal('25000.00'),
        }
        data.update(overrides)
        return WebOrder.objects.create(**data)

    def test_new_order_creates_notification_for_managers_only(self):
        order = self._create_order()

        manager_notifications = AdminNotification.objects.filter(recipient=self.manager, order=order)
        cashier_notifications = AdminNotification.objects.filter(recipient=self.cashier, order=order)

        self.assertEqual(manager_notifications.count(), 1)
        self.assertEqual(cashier_notifications.count(), 0)
        self.assertIn(f"Commande #{order.id}", manager_notifications.first().message)

    def test_notifications_feed_returns_recent_unread_notifications(self):
        order = self._create_order()
        self.client.force_login(self.manager)

        response = self.client.get(reverse('store:admin_notifications_feed'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['unread_count'], 1)
        self.assertEqual(len(payload['notifications']), 1)
        self.assertEqual(payload['notifications'][0]['order_id'], order.id)

    def test_open_notification_marks_it_as_read_and_redirects(self):
        order = self._create_order()
        notification = AdminNotification.objects.get(recipient=self.manager, order=order)
        self.client.force_login(self.manager)

        response = self.client.get(reverse('store:admin_notification_open', args=[notification.id]))

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertRedirects(response, reverse('store:admin_weborder_detail', args=[order.id]))

    def test_mark_all_notifications_read_marks_everything(self):
        first_order = self._create_order(full_name='Premier client')
        second_order = self._create_order(full_name='Second client', email='second@example.com')
        self.client.force_login(self.manager)

        response = self.client.post(reverse('store:admin_notifications_mark_all_read'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            AdminNotification.objects.filter(
                recipient=self.manager,
                order__in=[first_order, second_order],
                is_read=False,
            ).count(),
            0,
        )


class ManualPaymentFlowTests(TestCase):
    def setUp(self):
        self.temp_media_root = tempfile.mkdtemp()
        self.settings_ctx = self.settings(MEDIA_ROOT=self.temp_media_root)
        self.settings_ctx.enable()

        self.user = User.objects.create_user(
            username='customer',
            password='secret123',
            email='customer@example.com',
        )
        self.order = WebOrder.objects.create(
            user=self.user,
            full_name='Client Test',
            email='client@example.com',
            phone='+243000000000',
            address='Adresse test',
            city='Kinshasa',
            total_amount=Decimal('30000.00'),
        )

    def tearDown(self):
        self.settings_ctx.disable()
        shutil.rmtree(self.temp_media_root, ignore_errors=True)
        super().tearDown()

    def test_payment_instructions_keeps_selected_method(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('store:payment_instructions', args=[self.order.id]),
            {'payment_method': 'airtel'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_payment_method'], 'airtel')
        self.assertEqual(response.context['selected_payment_details']['label'], 'Airtel Money')

    def test_rejected_payment_is_updated_instead_of_creating_new_one(self):
        self.client.force_login(self.user)
        old_file = SimpleUploadedFile('old-proof.jpg', b'old-proof', content_type='image/jpeg')
        existing_payment = ManualPayment.objects.create(
            order=self.order,
            user=self.user,
            payment_method='cash',
            transaction_ref='OLD-REF',
            proof_file=old_file,
            status='rejected',
            rejection_reason='Flou',
        )

        new_file = SimpleUploadedFile('new-proof.jpg', b'new-proof', content_type='image/jpeg')
        response = self.client.post(
            reverse('store:payment_submit', args=[self.order.id]),
            {
                'payment_method': 'airtel',
                'transaction_ref': 'AIR-NEW-123',
                'proof_file': new_file,
            },
        )

        self.order.refresh_from_db()
        self.assertRedirects(response, reverse('store:account_order_detail', args=[self.order.order_number]))
        self.assertEqual(ManualPayment.objects.filter(order=self.order).count(), 1)

        existing_payment.refresh_from_db()
        self.assertEqual(existing_payment.payment_method, 'airtel')
        self.assertEqual(existing_payment.transaction_ref, 'AIR-NEW-123')
        self.assertEqual(existing_payment.status, 'submitted')
        self.assertEqual(existing_payment.rejection_reason, '')
        self.assertEqual(self.order.status, 'awaiting_verification')


class StorefrontAccessGuardTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Bijoux test')
        self.product = Product.objects.create(
            name='Bracelet test',
            category=self.category,
            purchase_price=Decimal('1000.00'),
            selling_price=Decimal('2500.00'),
            current_stock=8,
        )

        self.user = User.objects.create_user(
            username='storeclient',
            password='secret123',
            email='storeclient@example.com',
            first_name='Store',
            last_name='Client',
        )
        CustomerProfile.objects.create(
            user=self.user,
            phone='+243999999999',
            address='Avenue test',
            city='Kinshasa',
            zip_code='1000',
        )

    def test_guest_add_to_cart_requires_authentication(self):
        response = self.client.post(
            reverse('store:add_to_cart', args=[self.product.id]),
            data='{"customization": {}}',
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertTrue(payload['auth_required'])

    def test_guest_sync_cart_requires_authentication(self):
        response = self.client.post(
            reverse('store:sync_cart'),
            data='{"cart": []}',
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.json()['auth_required'])

    def test_checkout_view_prefills_customer_profile_fields(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('store:checkout'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['checkout_customer']['first_name'], 'Store')
        self.assertEqual(response.context['checkout_customer']['phone'], '+243999999999')
        self.assertEqual(response.context['checkout_customer']['address'], 'Avenue test')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', PUBLIC_APP_URL='https://store.mkaribu.test')
class CustomerOrderPortalTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Bijoux suivi')
        self.product = Product.objects.create(
            name='Collier suivi',
            category=self.category,
            purchase_price=Decimal('3000.00'),
            selling_price=Decimal('5500.00'),
            current_stock=20,
        )
        self.user = User.objects.create_user(
            username='portal-user',
            password='secret123',
            email='portal@example.com',
            first_name='Portail',
            last_name='Client',
        )
        CustomerProfile.objects.create(
            user=self.user,
            phone='+243970000001',
            address='Avenue du Portail',
            city='Kinshasa',
            zip_code='1200',
        )
        self.other_user = User.objects.create_user(
            username='other-user',
            password='secret123',
            email='other@example.com',
        )

    def _put_cart_in_session(self):
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'product_id': str(self.product.id),
                'quantity': 2,
                'customization': None,
            }
        }
        session.save()

    def test_checkout_sends_invoice_email_and_creates_delivery_code(self):
        self.client.force_login(self.user)
        self._put_cart_in_session()

        response = self.client.post(
            reverse('store:checkout'),
            {
                'payment_method': 'delivery-cash',
                'first_name': 'Portail',
                'last_name': 'Client',
                'email': 'portal@example.com',
                'phone': '+243970000001',
                'address': 'Avenue du Portail',
                'city': 'Kinshasa',
                'zip_code': '1200',
            },
        )

        order = WebOrder.objects.get(user=self.user)
        self.assertEqual(order.payment_method, 'delivery-cash')
        self.assertTrue(order.order_number.startswith('CMD-'))
        self.assertTrue(order.delivery_confirmation_code)
        self.assertRedirects(response, reverse('store:account_order_detail', args=[order.order_number]))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.order_number, mail.outbox[0].body)
        self.assertIn(order.delivery_confirmation_code, mail.outbox[0].body)
        self.assertIn(reverse('store:account_order_detail', args=[order.order_number]), mail.outbox[0].body)

    def test_customer_order_pages_are_scoped_to_logged_in_user(self):
        own_order = WebOrder.objects.create(
            user=self.user,
            full_name='Portail Client',
            email='portal@example.com',
            phone='+243970000001',
            address='Avenue du Portail',
            city='Kinshasa',
            payment_method='cash',
            total_amount=Decimal('10000.00'),
        )
        foreign_order = WebOrder.objects.create(
            user=self.other_user,
            full_name='Autre Client',
            email='other@example.com',
            phone='+243970000009',
            address='Ailleurs',
            city='Kinshasa',
            payment_method='cash',
            total_amount=Decimal('9000.00'),
        )

        self.client.force_login(self.user)

        list_response = self.client.get(reverse('store:account_orders'))
        detail_response = self.client.get(reverse('store:account_order_detail', args=[own_order.order_number]))
        forbidden_response = self.client.get(reverse('store:account_order_detail', args=[foreign_order.order_number]))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, own_order.order_number)
        self.assertNotContains(list_response, foreign_order.order_number)
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, own_order.order_number)
        self.assertEqual(forbidden_response.status_code, 404)

    def test_customer_can_open_printable_invoice_view(self):
        order = WebOrder.objects.create(
            user=self.user,
            full_name='Portail Client',
            email='portal@example.com',
            phone='+243970000001',
            address='Avenue du Portail',
            city='Kinshasa',
            payment_method='cash',
            total_amount=Decimal('10000.00'),
        )
        order.items.create(
            product=self.product,
            product_name=self.product.name,
            quantity=2,
            price=Decimal('5000.00'),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('store:account_order_invoice', args=[order.order_number]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FACTURE')
        self.assertContains(response, order.order_number)
        self.assertContains(response, 'Imprimer la facture')

    def test_customer_profile_page_updates_store_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('store:account_profile'),
            {
                'first_name': 'Nouveau',
                'last_name': 'Nom',
                'email': 'nouveau@example.com',
                'phone': '+243970000123',
                'address': 'Nouvelle avenue',
                'city': 'Lubumbashi',
                'zip_code': '2200',
            },
        )

        self.user.refresh_from_db()
        self.user.customer_profile.refresh_from_db()
        self.assertRedirects(response, reverse('store:account_profile'))
        self.assertEqual(self.user.first_name, 'Nouveau')
        self.assertEqual(self.user.email, 'nouveau@example.com')
        self.assertEqual(self.user.customer_profile.city, 'Lubumbashi')

    def test_store_navigation_pages_keep_main_content_outside_mobile_menu(self):
        own_order = WebOrder.objects.create(
            user=self.user,
            full_name='Portail Client',
            email='portal@example.com',
            phone='+243970000001',
            address='Avenue du Portail',
            city='Kinshasa',
            payment_method='cash',
            total_amount=Decimal('10000.00'),
        )

        self.client.force_login(self.user)

        pages = [
            reverse('store:catalog'),
            reverse('store:account_profile'),
            reverse('store:account_orders'),
            reverse('store:account_order_detail', args=[own_order.order_number]),
        ]

        for url in pages:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, msg=f'Unexpected status for {url}')

            parser = MainContentNestingParser()
            parser.feed(response.content.decode('utf-8'))

            self.assertFalse(
                parser.main_inside_mobile_menu,
                msg=f'Main content is nested inside mobile menu for {url}',
            )
