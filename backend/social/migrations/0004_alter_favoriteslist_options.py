# Generated by Django 3.2.16 on 2022-12-19 16:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0003_auto_20221218_1827'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='favoriteslist',
            options={'default_related_name': 'favor', 'verbose_name': 'Избранное', 'verbose_name_plural': 'Избранные'},
        ),
    ]
