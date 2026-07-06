# Generated manually: Adds SupplyCategory model and new fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('supply', '0003_merchantaccount_business_age_and_more'),
    ]

    operations = [
        # Create SupplyCategory model
        migrations.CreateModel(
            name='SupplyCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom de la catégorie')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('image', models.ImageField(blank=True, null=True, upload_to='supply/categories/', verbose_name='Image')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('order', models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Catégorie fournisseur',
                'verbose_name_plural': 'Catégories fournisseurs',
                'ordering': ['order', 'name'],
            },
        ),
        # Add supply_category FK to Supplier
        migrations.AddField(
            model_name='supplier',
            name='description',
            field=models.TextField(blank=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='supplier',
            name='supply_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='suppliers', to='supply.supplycategory', verbose_name='Catégorie PEMBENY'),
        ),
        # Add description and supply_category to SupplyProduct
        migrations.AddField(
            model_name='supplyproduct',
            name='description',
            field=models.TextField(blank=True, verbose_name='Description du produit'),
        ),
        migrations.AddField(
            model_name='supplyproduct',
            name='supply_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='supply.supplycategory', verbose_name='Catégorie PEMBENY'),
        ),
    ]