# Generated by Django 2.2.16 on 2023-01-27 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0029_auto_20230127_1534'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(help_text='Введите текст комментария, не более 200 символов', verbose_name='Текст комментария'),
        ),
    ]
