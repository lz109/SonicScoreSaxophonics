# Generated by Django 4.2.11 on 2024-04-03 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_remove_customuser_email_remove_customuser_username_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='user',
        ),
        migrations.AddField(
            model_name='customuser',
            name='userId',
            field=models.IntegerField(default=0),
        ),
    ]
