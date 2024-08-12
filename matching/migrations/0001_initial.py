# Generated by Django 5.0.6 on 2024-08-12 09:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('entreprinder', '0003_alter_match_unique_together_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dislike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('disliked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dislikes_received', to='entreprinder.entrepreneurprofile')),
                ('disliker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dislikes_given', to='entreprinder.entrepreneurprofile')),
            ],
            options={
                'unique_together': {('disliker', 'disliked')},
            },
        ),
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('liked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes_received', to='entreprinder.entrepreneurprofile')),
                ('liker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes_given', to='entreprinder.entrepreneurprofile')),
            ],
            options={
                'unique_together': {('liker', 'liked')},
            },
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('entrepreneur1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_first', to='entreprinder.entrepreneurprofile')),
                ('entrepreneur2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_second', to='entreprinder.entrepreneurprofile')),
            ],
            options={
                'unique_together': {('entrepreneur1', 'entrepreneur2')},
            },
        ),
    ]
