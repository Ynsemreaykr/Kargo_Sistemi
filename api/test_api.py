"""
Backend API test - system-parameters endpoint
"""
import requests

print("=" * 60)
print("TESTING: GET /api/system-parameters")
print("=" * 60)

try:
    response = requests.get("http://localhost:5002/api/system-parameters")
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse JSON:")
    import json
    data = response.json()
    print(json.dumps(data, indent=2))
    
    if data.get('success'):
        params = data.get('data', {})
        vehicle_types = params.get('vehicle_types', [])
        print(f"\n✓ Vehicle types count: {len(vehicle_types)}")
        
        if vehicle_types:
            print("\nVehicle Types:")
            for vt in vehicle_types:
                print(f"  - {vt}")
        else:
            print("\n❌ Vehicle types array is EMPTY!")
    else:
        print(f"\n❌ API returned success=false: {data.get('error')}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
