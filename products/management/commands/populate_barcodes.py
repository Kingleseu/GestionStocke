from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Generate barcodes for products that do not have one'

    def handle(self, *args, **options):
        products = Product.objects.filter(barcode__isnull=True)
        count = products.count()
        
        self.stdout.write(f'Found {count} products without barcodes...')
        
        for product in products:
            product.barcode = product.generate_barcode()
            product.save()
            self.stdout.write(f'Generated barcode for: {product.name}')
            
        self.stdout.write(self.style.SUCCESS(f'Successfully generated barcodes for {count} products'))
