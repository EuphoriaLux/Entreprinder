# Generated by Django 5.0.6 on 2024-08-12 09:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entreprinder', '0002_alter_entrepreneurprofile_industry_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='match',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='match',
            name='entrepreneur1',
        ),
        migrations.RemoveField(
            model_name='match',
            name='entrepreneur2',
        ),
        migrations.DeleteModel(
            name='Like',
        ),
        migrations.DeleteModel(
            name='Match',
        ),
    ]
