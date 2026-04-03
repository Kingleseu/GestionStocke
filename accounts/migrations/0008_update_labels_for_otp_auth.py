# Generated manually to align labels/options after the OTP auth refactor.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_emailotp_and_staff_invitation_updates'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='useractivity',
            options={
                'ordering': ['-timestamp'],
                'verbose_name': 'Activite utilisateur',
                'verbose_name_plural': 'Activites utilisateurs',
            },
        ),
        migrations.AlterField(
            model_name='shop',
            name='phone',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Telephone'),
        ),
        migrations.AlterField(
            model_name='useractivity',
            name='activity_type',
            field=models.CharField(
                choices=[('LOGIN', 'Connexion'), ('LOGOUT', 'Deconnexion')],
                max_length=10,
            ),
        ),
    ]
