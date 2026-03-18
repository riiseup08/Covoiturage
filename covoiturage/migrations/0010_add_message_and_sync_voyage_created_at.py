# Sync Voyage.created_at back into migration state and add Message model
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def _add_created_at_if_missing(apps, schema_editor):
    """Add created_at column to covoiturage_voyage if it doesn't already exist."""
    try:
        schema_editor.connection.cursor().execute(
            "ALTER TABLE covoiturage_voyage ADD COLUMN created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP"
        )
    except Exception:
        # Column already exists
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('covoiturage', '0009_notification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Re-add created_at (column may or may not exist depending on DB history)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(_add_created_at_if_missing, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='voyage',
                    name='created_at',
                    field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
                    preserve_default=False,
                ),
            ],
        ),
        # Create Message model
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('correspondance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='covoiturage.correspondance',
                )),
                ('sender', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sent_messages',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['created_at'],
                'indexes': [
                    models.Index(fields=['correspondance', 'created_at'], name='covoiturage_m_corresp_idx'),
                ],
            },
        ),
    ]
