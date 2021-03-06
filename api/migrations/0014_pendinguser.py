# Generated by Django 2.2.4 on 2019-10-09 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_auto_20191005_2103'),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=50)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('username', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=50)),
                ('expires', models.DateTimeField()),
            ],
        ),
    ]
