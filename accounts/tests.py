import re

from django.contrib.auth.models import Group, User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from store.models import CustomerProfile

from .models import ACCOUNT_SPACE_CUSTOMER, ACCOUNT_SPACE_STAFF, CashierInvitation, Shop
from .forms import CustomerSignupForm, ManagerSignupForm


class CustomerAuthTests(TestCase):
    def _extract_code(self, email_body):
        match = re.search(r'\b(\d{6})\b', email_body)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_customer_signup_creates_profile_and_sends_otp(self):
        response = self.client.post(
            reverse('accounts:customer_signup'),
            {
                'first_name': 'Franck',
                'last_name': 'Museba',
                'email': 'franck@example.com',
                'phone': '+243976797748',
                'city': 'Kinshasa',
                'address': 'Route des huileries',
                'next': reverse('store:catalog'),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertTrue(payload['otp_sent'])

        user = User.objects.get(email='franck@example.com')
        profile = CustomerProfile.objects.get(user=user)

        self.assertEqual(profile.phone, '+243976797748')
        self.assertEqual(profile.city, 'Kinshasa')
        self.assertTrue(user.groups.filter(name='Customer').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Code de connexion MKARIBU - Boutique', mail.outbox[0].subject)

    def test_customer_can_login_with_otp(self):
        user = User.objects.create_user(
            username='client-test',
            email='client@example.com',
            password='SecretPass123!',
            first_name='Client',
        )
        CustomerProfile.objects.create(user=user, phone='+243000000000', city='Kinshasa')

        request_response = self.client.post(
            reverse('accounts:login'),
            {
                'account_space': ACCOUNT_SPACE_CUSTOMER,
                'email': 'client@example.com',
                'next': reverse('store:catalog'),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(request_response.status_code, 200)
        self.assertTrue(request_response.json()['otp_sent'])
        self.assertEqual(len(mail.outbox), 1)

        code = self._extract_code(mail.outbox[0].body)
        verify_response = self.client.post(
            reverse('accounts:otp_verify'),
            {
                'email': 'client@example.com',
                'account_space': ACCOUNT_SPACE_CUSTOMER,
                'code': code,
                'next': reverse('store:catalog'),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(verify_response.status_code, 200)
        payload = verify_response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['redirect_url'], reverse('store:catalog'))
        self.assertEqual(self.client.session.get('_auth_user_id'), str(user.id))

    def test_login_request_does_not_authenticate_user_before_otp_verification(self):
        user = User.objects.create_user(
            username='client-wait',
            email='client-wait@example.com',
            password='SecretPass123!',
        )
        CustomerProfile.objects.create(user=user, phone='+243000000009', city='Kinshasa')

        response = self.client.post(
            reverse('accounts:login'),
            {
                'account_space': ACCOUNT_SPACE_CUSTOMER,
                'email': 'client-wait@example.com',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client.session.get('_auth_user_id'))

    def test_staff_otp_redirects_to_pos_by_default(self):
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='SecretPass123!',
            is_staff=True,
        )
        user.groups.add(manager_group)

        request_response = self.client.post(
            reverse('accounts:login'),
            {
                'account_space': ACCOUNT_SPACE_STAFF,
                'email': 'manager@example.com',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(request_response.status_code, 200)
        self.assertTrue(request_response.json()['otp_sent'])

        code = self._extract_code(mail.outbox[0].body)
        verify_response = self.client.post(
            reverse('accounts:otp_verify'),
            {
                'email': 'manager@example.com',
                'account_space': ACCOUNT_SPACE_STAFF,
                'code': code,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(verify_response.json()['redirect_url'], reverse('sales:pos'))

    def test_customer_signup_allows_email_already_used_by_staff_account(self):
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        staff_user = User.objects.create_user(
            username='staff-shared',
            email='shared@example.com',
            password='SecretPass123!',
            is_staff=True,
        )
        staff_user.groups.add(manager_group)

        form = CustomerSignupForm(
            data={
                'first_name': 'Client',
                'last_name': 'Shared',
                'email': 'shared@example.com',
                'phone': '+243000000001',
                'city': 'Kinshasa',
                'address': '',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_manager_signup_allows_email_already_used_by_customer_account(self):
        User.objects.create_user(
            username='customer-shared',
            email='shared@example.com',
            password='SecretPass123!',
        )

        form = ManagerSignupForm(
            data={
                'shop_name': 'Boutique Shared',
                'first_name': 'Manager',
                'last_name': 'Shared',
                'email': 'shared@example.com',
                'phone': '+243000000002',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)


class StaffInvitationFlowTests(TestCase):
    def setUp(self):
        self.manager_group, _ = Group.objects.get_or_create(name='Manager')
        self.manager = User.objects.create_user(
            username='manager-owner',
            email='manager-owner@example.com',
            password='SecretPass123!',
            first_name='Manager',
            last_name='Owner',
            is_staff=True,
        )
        self.manager.groups.add(self.manager_group)
        self.shop = Shop.objects.create(
            name='Boutique Centrale',
            created_by=self.manager,
            phone='+243000000100',
            email='manager-owner@example.com',
        )
        self.manager.profile.shop = self.shop
        self.manager.profile.save(update_fields=['shop', 'updated_at'])

    @override_settings(PUBLIC_APP_URL='https://staff.mkaribu.test')
    def test_create_invitation_uses_public_app_url_and_selected_role(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse('accounts:create_invitation'),
            {
                'role': 'Manager',
                'first_name': 'Aline',
                'last_name': 'Mbuyi',
                'email': 'aline.manager@example.com',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        invitation = CashierInvitation.objects.get(email='aline.manager@example.com')
        expected_url = f"https://staff.mkaribu.test{reverse('accounts:register_cashier', args=[str(invitation.token)])}"

        self.assertTrue(payload['success'])
        self.assertEqual(invitation.role, 'Manager')
        self.assertEqual(payload['invite_url'], expected_url)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(expected_url, mail.outbox[0].body)

    def test_authenticated_manager_can_open_invitation_registration_form(self):
        invitation = CashierInvitation.objects.create(
            created_by=self.manager,
            email='cashier-one@example.com',
            first_name='Cashier',
            last_name='One',
            role='Cashier',
        )
        self.client.force_login(self.manager)

        response = self.client.get(reverse('accounts:register_cashier', args=[str(invitation.token)]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, invitation.email)
        self.assertContains(response, 'Role fixe')

    def test_authenticated_manager_can_finish_invitation_registration_and_returns_to_team(self):
        invitation = CashierInvitation.objects.create(
            created_by=self.manager,
            email='second-manager@example.com',
            first_name='Second',
            last_name='Manager',
            role='Manager',
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse('accounts:register_cashier', args=[str(invitation.token)]),
            {
                'first_name': 'Second',
                'last_name': 'Manager',
                'email': 'second-manager@example.com',
                'password': 'SecretPass123!',
                'password_confirm': 'SecretPass123!',
            },
        )

        created_user = User.objects.get(email='second-manager@example.com')
        invitation.refresh_from_db()

        self.assertRedirects(response, reverse('accounts:user_list'))
        self.assertFalse(created_user.is_active)
        self.assertTrue(created_user.groups.filter(name='Manager').exists())
        self.assertEqual(created_user.profile.shop, self.shop)
        self.assertTrue(invitation.is_used)
        self.assertEqual(invitation.used_by, created_user)


class ProfilePageTests(TestCase):
    def setUp(self):
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        self.user = User.objects.create_user(
            username='vendeur01',
            email='vendeur@example.com',
            password='SecretPass123!',
            first_name='Didier',
            last_name='Panzu',
            is_staff=True,
        )
        self.user.groups.add(manager_group)
        self.shop = Shop.objects.create(
            name='Boutique Profile',
            created_by=self.user,
            phone='+243000000200',
            email='vendeur@example.com',
        )
        self.user.profile.shop = self.shop
        self.user.profile.save(update_fields=['shop', 'updated_at'])

    def test_profile_page_hides_top_admin_button_and_links_profile_menu(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('accounts:profile'))
        self.assertContains(response, f"{reverse('accounts:profile')}#profile-settings")
        self.assertNotContains(response, 'bi bi-shield-lock')

    def test_profile_update_saves_vendor_information(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('accounts:profile'),
            {
                'first_name': 'Didier',
                'last_name': 'Panzu',
                'email': 'vendeur@example.com',
                'phone': '+243977000111',
                'employee_code': 'VD-004',
                'position_title': 'Vendeur senior',
                'address': 'Gombe, Kinshasa',
                'hire_date': '2026-03-15',
                'emergency_contact_name': 'Marie Panzu',
                'emergency_contact_phone': '+243998000222',
                'notes': 'Responsable de la caisse du soir.',
            },
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()

        self.assertEqual(self.user.profile.phone, '+243977000111')
        self.assertEqual(self.user.profile.employee_code, 'VD-004')
        self.assertEqual(self.user.profile.position_title, 'Vendeur senior')
        self.assertEqual(self.user.profile.address, 'Gombe, Kinshasa')
        self.assertEqual(str(self.user.profile.hire_date), '2026-03-15')
        self.assertEqual(self.user.profile.emergency_contact_name, 'Marie Panzu')
        self.assertEqual(self.user.profile.emergency_contact_phone, '+243998000222')
        self.assertEqual(self.user.profile.notes, 'Responsable de la caisse du soir.')
