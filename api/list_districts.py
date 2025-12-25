from config import execute_query

districts = execute_query("SELECT id, name FROM districts ORDER BY id")

print("District ID Listesi:")
print("=" * 40)
for d in districts:
    print(f"ID {d['id']:2d}: {d['name']}")
