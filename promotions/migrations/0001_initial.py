from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0015_product_engraving_price_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="ex: 'Soldes Printemps 2026'", max_length=100, verbose_name='Nom de la promotion')),
                ('description', models.TextField(blank=True, verbose_name='Description détaillée')),
                ('discount_type', models.CharField(choices=[('percentage', 'Pourcentage (%)'), ('fixed', 'Montant fixe (€)')], default='percentage', max_length=20, verbose_name='Type de réduction')),
                ('discount_value', models.DecimalField(decimal_places=2, help_text='En pourcentage (0-100) ou montant en €', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Valeur de réduction')),
                ('scope', models.CharField(choices=[('all_products', 'Tous les produits'), ('specific_products', 'Produits sélectionnés'), ('specific_categories', 'Catégories sélectionnées')], default='all_products', max_length=30, verbose_name='Portée de la promotion')),
                ('start_date', models.DateTimeField(verbose_name='Date et heure de début')),
                ('end_date', models.DateTimeField(verbose_name='Date et heure de fin')),
                ('is_active', models.BooleanField(default=False, help_text='Cochez pour activer manuellement. Utilise start/end_date pour l\'automatisation.', verbose_name='Promotion active')),
                ('banner_image', models.ImageField(blank=True, help_text='Affiché en haut de la page pendant la promo', null=True, upload_to='promotions/banners/', verbose_name='Image de bannière')),
                ('banner_message', models.CharField(blank=True, help_text="ex: 'Soldes du Printemps! -20% tout!' ou '🎉 Promotion jusqu'au 15 mars!'", max_length=200, verbose_name='Message de la bannière')),
                ('display_badge', models.BooleanField(default=True, verbose_name='Afficher un badge sur les produits')),
                ('badge_custom_text', models.CharField(blank=True, default='', help_text="Si vide, le système génère automatiquement. ex: '-20% OFF' ou 'SOLDES'", max_length=50, verbose_name='Texte du badge personnalisé')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créée le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Modifiée le')),
                ('note_business', models.TextField(blank=True, help_text='Notes pour le gestionnaire (client, raison, etc.)', verbose_name='Notes internes')),
                ('categories', models.ManyToManyField(blank=True, related_name='promotions', to='products.category', verbose_name='Catégories concernées')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_promotions', to='auth.user', verbose_name='Créée par')),
                ('products', models.ManyToManyField(blank=True, related_name='promotions', to='products.product', verbose_name='Produits concernés')),
            ],
            options={
                'verbose_name': 'Promotion',
                'verbose_name_plural': 'Promotions',
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='PromotionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('created', 'Créée'), ('updated', 'Modifiée'), ('activated', 'Activée'), ('deactivated', 'Désactivée'), ('started', 'Débuté'), ('ended', 'Terminée'), ('deleted', 'Supprimée')], max_length=20, verbose_name='Action')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Horodatage')),
                ('details', models.JSONField(blank=True, default=dict, help_text='Détails additionnels en JSON (avant/après, etc.)', verbose_name='Détails')),
                ('performed_by', models.ForeignKey(blank=True, help_text="L'utilisateur qui a effectué l'action", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='promotion_logs', to='auth.user', verbose_name='Effectuée par')),
                ('promotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='promotions.promotion', verbose_name='Promotion')),
            ],
            options={
                'verbose_name': 'Journal de promotion',
                'verbose_name_plural': 'Journaux de promotions',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='promotion',
            index=models.Index(fields=['start_date', 'end_date'], name='promotions_p_start_d_idx'),
        ),
        migrations.AddIndex(
            model_name='promotion',
            index=models.Index(fields=['is_active'], name='promotions_p_is_act_idx'),
        ),
        migrations.AddIndex(
            model_name='promotionlog',
            index=models.Index(fields=['promotion', '-timestamp'], name='promotions_p_promot_d3ad4a_idx'),
        ),
    ]
