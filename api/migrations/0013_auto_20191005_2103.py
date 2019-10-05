# Generated by Django 2.2.4 on 2019-10-05 21:03

from django.db import migrations

def create_editors_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    group, created = Group.objects.get_or_create(name='editors')

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_family_owner'),
    ]

    operations = [
        migrations.RunPython(create_editors_group)
    ]
