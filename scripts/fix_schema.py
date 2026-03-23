"""One-time script to add missing columns after a faked migration."""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carpoolconfig.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Profile columns
alters = [
    "ALTER TABLE covoiturage_profile ADD COLUMN whatsapp_number varchar(20) NOT NULL DEFAULT ''",
    "ALTER TABLE covoiturage_profile ADD COLUMN mobile_money_number varchar(20) NOT NULL DEFAULT ''",
    "ALTER TABLE covoiturage_profile ADD COLUMN mobile_money_provider varchar(10) NOT NULL DEFAULT ''",
    "ALTER TABLE covoiturage_profile ADD COLUMN preferred_language varchar(5) NOT NULL DEFAULT 'fr'",
]

for sql in alters:
    try:
        cursor.execute(sql)
        print(f"OK: {sql[:60]}...")
    except Exception as e:
        print(f"SKIP (already exists?): {e}")

# Voyage columns
cursor.execute('PRAGMA table_info(covoiturage_voyage)')
vcols = [r[1] for r in cursor.fetchall()]

voyage_alters = []
if 'currency' not in vcols:
    voyage_alters.append("ALTER TABLE covoiturage_voyage ADD COLUMN currency varchar(3) NOT NULL DEFAULT 'XAF'")
if 'accept_mobile_money' not in vcols:
    voyage_alters.append("ALTER TABLE covoiturage_voyage ADD COLUMN accept_mobile_money bool NOT NULL DEFAULT 1")
if 'accept_cash' not in vcols:
    voyage_alters.append("ALTER TABLE covoiturage_voyage ADD COLUMN accept_cash bool NOT NULL DEFAULT 1")

for sql in voyage_alters:
    try:
        cursor.execute(sql)
        print(f"OK: {sql[:60]}...")
    except Exception as e:
        print(f"SKIP: {e}")

print("\nDone!")
