from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_product_extra_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='color_choice',
            field=models.CharField(choices=[('argent', 'Argent'), ('or', 'Or'), ('autre', 'Autre')], default='argent', max_length=20, verbose_name='Couleur'),
        ),
        migrations.AddField(
            model_name='product',
            name='custom_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Couleur personnalisée'),
        ),
    ]
