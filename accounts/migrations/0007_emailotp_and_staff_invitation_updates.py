# Generated manually for OTP email authentication.

import accounts.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_shop_usd_to_cdf_rate_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cashierinvitation',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Invitation du personnel',
                'verbose_name_plural': 'Invitations du personnel',
            },
        ),
        migrations.AddField(
            model_name='cashierinvitation',
            name='email',
            field=models.EmailField(default='', max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cashierinvitation',
            name='expires_at',
            field=models.DateTimeField(default=accounts.models.default_invitation_expiry),
        ),
        migrations.AddField(
            model_name='cashierinvitation',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cashierinvitation',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cashierinvitation',
            name='role',
            field=models.CharField(
                choices=[('Manager', 'Manager'), ('Cashier', 'Caissier')],
                default='Cashier',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='EmailOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('purpose', models.CharField(choices=[('login', 'Connexion')], default='login', max_length=20)),
                ('account_space', models.CharField(choices=[('customer', 'Compte client boutique'), ('staff', 'Compte personnel boutique')], max_length=20)),
                ('code_hash', models.CharField(max_length=128)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_otps', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Code OTP email',
                'verbose_name_plural': 'Codes OTP email',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='emailotp',
            index=models.Index(fields=['email', 'account_space', 'purpose'], name='accounts_em_email_0cb8e3_idx'),
        ),
        migrations.AddIndex(
            model_name='emailotp',
            index=models.Index(fields=['user', 'purpose', 'created_at'], name='accounts_em_user_id_1533d7_idx'),
        ),
    ]
