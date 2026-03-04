from django.core.management.base import BaseCommand
from django.utils import timezone
from promotions.utils import update_promotion_status
from promotions.models import Promotion


class Command(BaseCommand):
    help = 'Vérifie et met à jour le statut des promotions (activation/désactivation automatique)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("[Promotions] Vérification des promotions en cours..."))
        
        # Mettre à jour le statut
        stats = update_promotion_status()
        
        # Afficher le résumé
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Mise à jour effectuée:\n"
                f"   • {stats['activated']} promotion(s) activée(s)\n"
                f"   • {stats['deactivated']} promotion(s) désactivée(s)\n"
                f"   • Horodatage: {stats['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}"
            )
        )
        
        # Afficher les promos actuellement actives
        now = timezone.now()
        active_count = Promotion.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).count()
        
        self.stdout.write(self.style.WARNING(f"🎉 {active_count} promotion(s) actuellement actif(ve)"))
