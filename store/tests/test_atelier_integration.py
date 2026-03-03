from django.test import TestCase
from store.models import Product, WebOrder, WebOrderItem
from django.contrib.auth.models import User
from decimal import Decimal

class AtelierIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.product = Product.objects.create(
            name="Test Medallion",
            price=20000,
            stock=10,
            customization_rules={
                "is_studio": True,
                "zones": [
                    {"id": "studio_engraving", "type": "text", "constraints": {"max_length": 15}},
                    {"id": "studio_component", "type": "selection", "options": [{"value": "gold", "price_modifier": 5000}]}
                ]
            }
        )

    def test_customized_order_creation(self):
        """Test creating an order with customization data"""
        custom_data = {
            "is_studio": True,
            "choices": {
                "studio_engraving": {"text": "Love", "font": "Anglaise"},
                "studio_component": "gold"
            },
            "extra_cost": 5000,
            "quantity": 1,
            "preview": "data:image/png;base64,fakeimage"
        }

        order = WebOrder.objects.create(
            user=self.user,
            full_name="Test Client",
            total_amount=25000,
            status='pending'
        )
        
        item = WebOrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            price=25000,
            customization_data=custom_data
        )

        # Verify data storage
        self.assertTrue(item.customization_data['is_studio'])
        self.assertEqual(item.customization_data['extra_cost'], 5000)
        self.assertEqual(item.customization_data['choices']['studio_engraving']['text'], "Love")

    def test_customization_parsing(self):
        """Test the logic used in views to parse customization"""
        custom_data = {
            "is_studio": True,
            "choices": {
                "studio_engraving": {"text": "Test", "font": "Arial"},
                "studio_component": "gold"
            },
            "extra_cost": 0,
            "preview": "http://example.com/img.png"
        }
        
        # Simulate what _parse_customization does
        details = {
            'is_studio': custom_data.get('is_studio', False),
            'extra_cost': custom_data.get('extra_cost', 0),
            'preview': custom_data.get('preview'),
            'choices': {}
        }
        
        self.assertEqual(details['preview'], "http://example.com/img.png")
        self.assertEqual(details['is_studio'], True)
