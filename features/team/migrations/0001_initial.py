# Generated by Django 5.2.3 on 2025-07-10 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tournament', '0006_alter_tournament_registration_end_date_and_more'),
        ('users', '0004_auto_20250617_1152'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('members', models.ManyToManyField(related_name='members', to='users.user')),
                ('tournament', models.ManyToManyField(related_name='tournament_team', to='tournament.tournament')),
            ],
        ),
    ]
