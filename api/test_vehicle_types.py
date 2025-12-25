"""
Veritabanında vehicle_types kontrolü
"""
import psycopg

conn = psycopg.connect("host=localhost dbname=cargo_db user=postgres password=postgres")
cur = conn.cursor()

print("=" * 60)
print("VEHICLE_TYPES KONTROL")
print("=" * 60)

cur.execute("SELECT id, name, capacity_kg, rental_cost FROM vehicle_types ORDER BY id")
rows = cur.fetchall()

print(f"\nToplam {len(rows)} araç tipi bulundu:\n")

for row in rows:
    print(f"ID: {row[0]}")
    print(f"  Name: {row[1]}")
    print(f"  Capacity: {row[2]} kg")
    print(f"  Rental Cost: {row[3]} TL")
    print()

cur.close()
conn.close()

print("=" * 60)
