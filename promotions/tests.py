"""
Tests du système de promotions
Pour lancer: python manage.py test promotions
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User

from promotions.models import Promotion, PromotionLog
from promotions.utils import calculate_product_price, get_active_promotions, update_promotion_status
from products.models import Product, Category


class PromotionModelTests(TestCase):
    """Tests des modèles de promotion"""
    
    def setUp(self):
        """Préparation des données de test"""
        self.user = User.objects.create_user(username='testuser', password='123456')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            selling_price=Decimal('100.00'),
            purchase_price=Decimal('50.00'),
            category=self.category
        )
    
    def test_create_promotion_percentage(self):
        """Test création d'une promo avec pourcentage"""
        promo = Promotion.objects.create(
            name='Test Promo 20%',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        self.assertEqual(promo.name, 'Test Promo 20%')
        self.assertEqual(promo.discount_type, 'percentage')
        self.assertEqual(promo.discount_value, Decimal('20.00'))
        self.assertTrue(promo.is_running)
        self.assertEqual(str(promo), 'Test Promo 20% (-20%)')
    
    def test_create_promotion_fixed_amount(self):
        """Test création d'une promo avec montant fixe"""
        promo = Promotion.objects.create(
            name='Test Promo 10€',
            discount_type='fixed',
            discount_value=Decimal('10.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        self.assertEqual(promo.discount_type, 'fixed')
        self.assertEqual(promo.discount_value, Decimal('10.00'))
        self.assertEqual(str(promo), 'Test Promo 10€ (-10€)')
    
    def test_promotion_status_active(self):
        """Test que le statut d'une promo active est correct"""
        promo = Promotion.objects.create(
            name='Test Active',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        self.assertEqual(promo.status, 'active')
        self.assertTrue(promo.is_running)
        self.assertFalse(promo.is_expired)
    
    def test_promotion_status_upcoming(self):
        """Test que le statut d'une promo programmée est correct"""
        promo = Promotion.objects.create(
            name='Test Upcoming',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            scope='all_products',
            start_date=timezone.now() + timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=2),
            is_active=True,
            created_by=self.user
        )
        
        self.assertEqual(promo.status, 'upcoming')
        self.assertTrue(promo.is_upcoming)
        self.assertFalse(promo.is_running)
    
    def test_promotion_status_expired(self):
        """Test que le statut d'une promo expirée est correct"""
        promo = Promotion.objects.create(
            name='Test Expired',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=2),
            end_date=timezone.now() - timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        self.assertEqual(promo.status, 'expired')
        self.assertTrue(promo.is_expired)
        self.assertFalse(promo.is_running)
    
    def test_promotion_calculate_price_percentage(self):
        """Test le calcul du prix réduit (pourcentage)"""
        promo = Promotion.objects.create(
            name='Test 20%',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        reduced_price = promo.calculate_discounted_price(Decimal('100.00'))
        expected = Decimal('100.00') - (Decimal('100.00') * Decimal('0.20'))
        
        self.assertEqual(reduced_price, expected)
        self.assertEqual(reduced_price, Decimal('80.00'))
    
    def test_promotion_calculate_price_fixed(self):
        """Test le calcul du prix réduit (montant fixe)"""
        promo = Promotion.objects.create(
            name='Test 10€',
            discount_type='fixed',
            discount_value=Decimal('10.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        reduced_price = promo.calculate_discounted_price(Decimal('100.00'))
        
        self.assertEqual(reduced_price, Decimal('90.00'))
    
    def test_promotion_badge_text_percentage(self):
        """Test la génération du texte de badge (pourcentage)"""
        promo = Promotion.objects.create(
            name='Test Badge %',
            discount_type='percentage',
            discount_value=Decimal('25.50'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        badge_text = promo.get_badge_text()
        self.assertEqual(badge_text, '-25%')
    
    def test_promotion_badge_text_fixed(self):
        """Test la génération du texte de badge (montant)"""
        promo = Promotion.objects.create(
            name='Test Badge €',
            discount_type='fixed',
            discount_value=Decimal('15.99'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        badge_text = promo.get_badge_text()
        self.assertEqual(badge_text, '-15.99€')
    
    def test_promotion_badge_custom(self):
        """Test texte de badge personnalisé"""
        promo = Promotion.objects.create(
            name='Test Custom Badge',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            badge_custom_text='SOLDES',
            created_by=self.user
        )
        
        badge_text = promo.get_badge_text()
        self.assertEqual(badge_text, 'SOLDES')


class PromotionUtilsTests(TestCase):
    """Tests des fonctions utilitaires"""
    
    def setUp(self):
        """Préparation des données de test"""
        self.user = User.objects.create_user(username='testuser', password='123456')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            selling_price=Decimal('100.00'),
            purchase_price=Decimal('50.00'),
            category=self.category,
            is_active=True
        )
    
    def test_calculate_product_price_without_promotion(self):
        """Test le calcul du prix sans promotion"""
        pricing = calculate_product_price(self.product)
        
        self.assertEqual(pricing['original_price'], Decimal('100.00'))
        self.assertEqual(pricing['discounted_price'], Decimal('100.00'))
        self.assertFalse(pricing['has_promotion'])
        self.assertIsNone(pricing['promotion'])
    
    def test_calculate_product_price_with_promotion(self):
        """Test le calcul du prix avec promotion"""
        promo = Promotion.objects.create(
            name='Test Promo',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        pricing = calculate_product_price(self.product)
        
        self.assertEqual(pricing['original_price'], Decimal('100.00'))
        self.assertEqual(pricing['discounted_price'], Decimal('80.00'))
        self.assertTrue(pricing['has_promotion'])
        self.assertEqual(pricing['promotion'].id, promo.id)
        self.assertEqual(pricing['discount_percent'], Decimal('20.00'))
    
    def test_get_active_promotions(self):
        """Test la récupération des promotions actives"""
        # Créer une promo active
        active_promo = Promotion.objects.create(
            name='Active Promo',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        # Créer une promo non active
        inactive_promo = Promotion.objects.create(
            name='Inactive Promo',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=False,
            created_by=self.user
        )
        
        # Récupérer les promos actives
        active_promos = get_active_promotions()
        
        self.assertIn(active_promo, active_promos)
        self.assertNotIn(inactive_promo, active_promos)


class PromotionLogsTests(TestCase):
    """Tests des logs de promotions"""
    
    def setUp(self):
        """Préparation des données de test"""
        self.user = User.objects.create_user(username='testuser', password='123456')
    
    def test_promotion_log_creation(self):
        """Test la création automatique d'un log"""
        # Les logs sont créés via les signaux
        # Ce test vérifie juste que le modèle fonctionne
        
        category = Category.objects.create(name='Test')
        product = Product.objects.create(
            name='Test',
            selling_price=100,
            purchase_price=50,
            category=category
        )
        
        promo = Promotion.objects.create(
            name='Test Log',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True,
            created_by=self.user
        )
        
        # Vérifier qu'un log a été créé
        logs = PromotionLog.objects.filter(promotion=promo)
        self.assertTrue(logs.exists())


class PromotionIntegrationTests(TestCase):
    """Tests d'intégration complets"""
    
    def setUp(self):
        """Préparation des données de test"""
        self.user = User.objects.create_user(username='testuser', password='123456')
        self.category = Category.objects.create(name='Mobilier')
        self.product1 = Product.objects.create(
            name='Chaise Design',
            selling_price=Decimal('120.00'),
            purchase_price=Decimal('60.00'),
            category=self.category,
            is_active=True
        )
        self.product2 = Product.objects.create(
            name='Table Basse',
            selling_price=Decimal('250.00'),
            purchase_price=Decimal('125.00'),
            category=self.category,
            is_active=True
        )
    
    def test_full_promotion_workflow(self):
        """Test le workflow complet d'une promotion"""
        # 1. Créer une promo
        promo = Promotion.objects.create(
            name='Soldes Printemps',
            discount_type='percentage',
            discount_value=Decimal('15.00'),
            scope='specific_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=24),
            is_active=True,
            created_by=self.user
        )
        promo.products.add(self.product1)
        
        # 2. Vérifier le prix du produit 1 (affecté)
        pricing1 = calculate_product_price(self.product1)
        self.assertTrue(pricing1['has_promotion'])
        self.assertEqual(pricing1['discounted_price'], Decimal('102.00'))
        
        # 3. Vérifier le prix du produit 2 (non affecté)
        pricing2 = calculate_product_price(self.product2)
        self.assertFalse(pricing2['has_promotion'])
        self.assertEqual(pricing2['discounted_price'], Decimal('250.00'))
        
        # 4. Vérifier que la promo est en cours
        self.assertEqual(promo.status, 'active')
        
        # 5. Vérifier le badge
        badge = promo.get_badge_text()
        self.assertEqual(badge, '-15%')
