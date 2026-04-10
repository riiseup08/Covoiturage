# Generated manually to align Voyage schema with existing database columns
from django.db import migrations, models


def _add_columns_if_missing(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(covoiturage_voyage)")}

    def add(col_name, definition):
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE covoiturage_voyage ADD COLUMN {definition}")

    add('updated_at', "updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
    add('is_validated', "is_validated bool NOT NULL DEFAULT 0")
    add('status', "status varchar(20) NOT NULL DEFAULT 'pending'")
    add('driver_confirmed_pickup', "driver_confirmed_pickup bool NOT NULL DEFAULT 0")
    add('driver_confirmed_dropoff', "driver_confirmed_dropoff bool NOT NULL DEFAULT 0")
    add('start_latitude', "start_latitude REAL")
    add('start_longitude', "start_longitude REAL")
    add('end_latitude', "end_latitude REAL")
    add('end_longitude', "end_longitude REAL")


class Migration(migrations.Migration):

    dependencies = [
        ('covoiturage', '0007_profile_car_photo_profile_created_at_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(_add_columns_if_missing, migrations.RunPython.noop)],
            state_operations=[
                migrations.AddField(
                    model_name='voyage',
                    name='updated_at',
                    field=models.DateTimeField(auto_now=True),
                ),
                migrations.AddField(
                    model_name='voyage',
                    name='is_validated',
                    field=models.BooleanField(default=False, help_text="Trajet validé par l'équipe"),
                ),
                migrations.AddField(
                    model_name='voyage',
                    name='status',
                    field=models.CharField(default='pending', help_text='Statut global du trajet', max_length=20),
                ),
                migrations.AddField(
                    model_name='voyage',
                    name='driver_confirmed_pickup',
                    field=models.BooleanField(default=False, help_text='Le conducteur confirme la prise en charge'),
                ),
                migrations.AddField(
                    model_name='voyage',
                    name='driver_confirmed_dropoff',
                    field=models.BooleanField(default=False, help_text='Le conducteur confirme la dépose'),
                ),
                migrations.AddField(
                    model_name='voyage',
                    name='start_latitude',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='voyage',
                    name='start_longitude',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='voyage',
                    name='end_latitude',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='voyage',
                    name='end_longitude',
                    field=models.FloatField(blank=True, null=True),
                ),
            ],
        ),
    ]
