# Generated by Django 2.2.4 on 2019-10-05 07:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0010_delete_familyindex'),
    ]

    operations = [
        migrations.AddField(
            model_name='individual',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='individuals', to=settings.AUTH_USER_MODEL),
        ),
    ]