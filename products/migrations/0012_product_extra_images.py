from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_customizablecomponent_customizationfont_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='extra_image_1',
            field=models.ImageField(blank=True, null=True, upload_to='products/', verbose_name='Image supplémentaire 1'),
        ),
        migrations.AddField(
            model_name='product',
            name='extra_image_2',
            field=models.ImageField(blank=True, null=True, upload_to='products/', verbose_name='Image supplémentaire 2'),
        ),
    ]
