from django.test import TestCase, Client
from django.urls import reverse
from products.models import Product, Category, CustomizationTemplate
from products.services import CustomizationService
from django.contrib.auth.models import User
from decimal import Decimal
import json

class CustomizationLogicTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")
        self.template = CustomizationTemplate.objects.create(
            name="Zag Style Template",
            rules={
                "version": "2.0",
                "zones": [
                    {
                        "id": "engraving",
                        "type": "text",
                        "label": "Gravure",
                        "required": True,
                        "constraints": {
                            "max_length": 10,
                            "allowed_fonts": ["Arial", "Cursive"]
                        },
                        "price_formula": {
                            "base": 5.00,
                            "per_char": 0.50
                        }
                    },
                    {
                        "id": "symbol",
                        "type": "selection",
                        "label": "Symbole",
                        "required": False,
                        "options": [
                            {"value": "heart", "label": "Cœur", "price_modifier": 2.00},
                            {"value": "star", "label": "Étoile", "price_modifier": 3.00}
                        ]
                    }
                ]
            }
        )
        self.product = Product.objects.create(
            name="Test Collier",
            purchase_price=Decimal("10.00"),
            selling_price=Decimal("20.00"),
            category=self.category,
            is_customizable=True,
            customization_template=self.template
        )
        self.client = Client()
        self.user = User.objects.create_user(
            username='customization-client',
            email='customization@example.com',
            password='Secret123!',
        )

    def test_price_calculation(self):
        # Case 1: Text only (5 carbons = base 5 + 5*0.5 = 7.5 extra)
        data = {"choices": {"engraving": {"text": "Hello", "font": "Arial"}}}
        extra = CustomizationService.calculate_customization_price(self.product, data)
        self.assertEqual(extra, Decimal("7.50"))

        # Case 2: Text + Symbol (7.5 + 2.0 = 9.5 extra)
        data["choices"]["symbol"] = "heart"
        extra = CustomizationService.calculate_customization_price(self.product, data)
        self.assertEqual(extra, Decimal("9.50"))

    def test_validation_logic(self):
        # Missing required field
        data = {"choices": {}}
        with self.assertRaises(Exception):
            CustomizationService.validate_customization_data(self.product, data)

        # Text too long
        data = {"choices": {"engraving": {"text": "This is too long", "font": "Arial"}}}
        with self.assertRaises(Exception):
            CustomizationService.validate_customization_data(self.product, data)

    def test_cart_synchronization(self):
        self.client.force_login(self.user)

        # Mock a cart sync
        cart_data = [
            {
                "productId": str(self.product.id),
                "quantity": 2,
                "customization": {"choices": {"engraving": {"text": "Marie", "font": "Arial"}}}
            }
        ]
        response = self.client.post(
            reverse('store:sync_cart'),
            data=json.dumps({"cart": cart_data}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check session
        session_cart = self.client.session['cart']
        self.assertEqual(len(session_cart), 1)
        # Key should contain hash
        key = list(session_cart.keys())[0]
        self.assertTrue(key.startswith(str(self.product.id)))
        self.assertEqual(session_cart[key]['quantity'], 2)
        self.assertEqual(session_cart[key]['customization']['choices']['engraving']['text'], "Marie")
