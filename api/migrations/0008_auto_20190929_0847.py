# Generated by Django 2.2.4 on 2019-09-29 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_individual_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='family',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='individual',
            name='baptism_date',
            field=models.DateField(blank=True, null=True, verbose_name='baptism date'),
        ),
        migrations.AddField(
            model_name='individual',
            name='baptism_location',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
