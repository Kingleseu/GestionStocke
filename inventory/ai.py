from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, F
from sales.models import SaleItem, Sale

class StockBrain:
    """
    Le Cerveau : Système de prédiction de stock
    Analyse les ventes passées pour prédire les ruptures futures.
    """
    
    def __init__(self, shop, analysis_period_days=30):
        self.shop = shop
        self.days = analysis_period_days
        self.now = timezone.now()
        
    def analyze_product(self, product):
        """
        Analyse un produit unique et retourne ses métriques prédictives.
        """
        # 1. Calculer les ventes sur la période (ex: 30 derniers jours)
        start_date = self.now - timedelta(days=self.days)
        
        # NOTE: product is already shop-filtered by caller, so we implicitly trust it.
        # But SaleItem query ensures we only look at relevant sales data.
        total_sold = SaleItem.objects.filter(
            product=product,
            sale__sale_date__gte=start_date
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # 2. Calculer la vélocité (Vitesse de vente par jour)
        daily_velocity = total_sold / self.days
        
        # 3. Prédire la date de rupture
        current_stock = product.current_stock
        days_left = 999  # Infini par défaut
        stockout_date = None
        
        if daily_velocity > 0:
            days_left = current_stock / daily_velocity
            stockout_date = self.now + timedelta(days=days_left)
            
        # 4. Statut de risque
        risk_level = 'LOW' # LOW, MEDIUM, HIGH, CRITICAL
        if current_stock <= 0:
            risk_level = 'OUT_OF_STOCK'
        elif days_left < 3:
            risk_level = 'CRITICAL'
        elif days_left < 7:
            risk_level = 'HIGH'
        elif days_left < 14:
            risk_level = 'MEDIUM'
            
        return {
            'product': product,
            'current_stock': current_stock,
            'velocity': round(daily_velocity, 2),
            'days_left': round(days_left, 1) if days_left != 999 else "∞",
            'stockout_date': stockout_date,
            'risk_level': risk_level,
            'recommendation': self._get_recommendation(risk_level, daily_velocity)
        }
    
    def _get_recommendation(self, risk_level, velocity):
        if risk_level == 'OUT_OF_STOCK':
            return "Commander URGEMMENT"
        elif risk_level == 'CRITICAL':
            # Suggérer une commande pour tenir 30 jours
            needed = velocity * 30
            return f"Commander {int(needed)} unités"
        elif risk_level == 'HIGH':
            return "Préparer commande"
        return "Stock sain"

    def get_dashboard_data(self):
        """
        Récupère les données pour tous les produits, triés par risque.
        """
        from products.models import Product
        # Filter by shop
        products = Product.objects.filter(shop=self.shop, is_active=True)
        analysis = []
        
        for p in products:
            data = self.analyze_product(p)
            # On ne garde que ceux qui ont une activité ou un stock critique
            if data['velocity'] > 0 or data['current_stock'] < 5:
                analysis.append(data)
                
        # Trier par urgence (jours restants croissant)
        # On gère le cas "∞" pour le tri
        def sort_key(x):
            val = x['days_left']
            return 999999 if val == "∞" else val
            
        return sorted(analysis, key=sort_key)
