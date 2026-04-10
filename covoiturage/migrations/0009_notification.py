from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('covoiturage', '0008_sync_voyage_flags_and_geo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('match', 'Nouveau match trouvé'), ('match_validated', 'Match validé'), ('match_refused', 'Match refusé'), ('review', 'Nouvel avis reçu'), ('trip_reminder', 'Rappel de trajet'), ('trip_completed', 'Trajet terminé'), ('message', 'Nouveau message')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('related_avis', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='covoiturage.avis')),
                ('related_correspondance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='covoiturage.correspondance')),
                ('related_voyage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='covoiturage.voyage')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='covoiturage_notification_user_is_read_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', '-created_at'], name='covoiturage_notification_user_created_idx'),
        ),
    ]