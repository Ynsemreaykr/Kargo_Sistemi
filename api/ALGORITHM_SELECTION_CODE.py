"""
ROUTES.PY İÇİN ALGORİTMA SEÇİM KODU
Bu kodu routes.py satır 302'den itibaren ekleyin (mevcut kodu değiştirin)
"""

# ===== AŞAMA 3: ALGORİTMA SEÇİMİ =====
print(f"\n🔧 Algoritma: {algorithm_choice}")
print(f"📦 Kargo sayısı: {len(cargos)}")
print(f"📊 Senaryo tipi: {scenario_type}")

# ALGORİTMA SEÇİMİ: optimization vs greedy
if algorithm_choice == 'optimization':
    # ===== TAM OPTİMİZASYON SİSTEMİ =====
    print("\n🚀 TAM OPTİMİZASYON SİSTEMİ KULLANILIYOR...")
    
    # Kiralanabilir araç tipleri
    available_vehicle_types_query = """
        SELECT id, name, capacity_kg, rental_cost
        FROM vehicle_types
        ORDER BY capacity_kg
    """
    available_vehicle_types = execute_query(available_vehicle_types_query)
    for vt in available_vehicle_types:
        vt['capacity_kg'] = float(vt['capacity_kg'])
        vt['rental_cost'] = float(vt['rental_cost']) if vt['rental_cost'] else 0.0
        vt['is_rented'] = True
        vt['current_location_district_id'] = 12  # İzmit
    
    # Tam optimizasyon çalıştır
    optimization_result = full_optimization(
        cargos=cargos,
        districts=districts,
        own_vehicles=own_vehicles,
        available_vehicle_types=available_vehicle_types,
        cost_per_km=cost_per_km,
        distance_matrix=distance_matrix
    )
    
    if not optimization_result:
        return jsonify({
            'success': False,
            'error': 'Optimizasyon başarısız oldu'
        }), 500
    
    # Sonuçları routes formatına çevir
    routes = []
    for opt_route in optimization_result['routes']:
        route_dict = {
            'vehicle_id': opt_route['vehicle_id'],
            'vehicle_type': opt_route['vehicle'].get('name', 'Unknown'),
            'start_location_id': opt_route['start_location'],
            'end_location_id': opt_route['end_location'],
            'route': opt_route['path'],
            'cargos': opt_route['cargos'],
            'total_distance_km': opt_route['distance'],
            'total_weight_kg': opt_route['total_weight'],
            'capacity_utilization': opt_route['utilization']
        }
        routes.append(route_dict)
    
    # Maliyet bilgileri
    total_cost = optimization_result['total_cost']
    total_distance = optimization_result['total_distance']
    total_rental_cost = optimization_result.get('rental_cost', 0)
    rental_count = optimization_result['combination'].get('rental_count', 0)
    
    print(f"\n✅ OPTİMİZASYON TAMAMLANDI: {len(routes)} rota, {total_cost:.2f} TL")
    
else:
    # ===== GREEDY ALGORİTMASI (Mevcut) =====
    print("\n📊 GREEDY/HYBRID ALGORİTMASI KULLANILIYOR...")
    
    # 1. Greedy ile başlangıç rotaları (kendi araçlarla)
    initial_routes = nearest_neighbor_algorithm(
        cargos, 
        districts, 
        own_vehicles
    )
    
    print(f"\n✓ Kendi araçlarla {len(initial_routes)} rota oluşturuldu")
    
    # Buradan sonra mevcut kod devam eder (satır 316'dan itibaren)
    # 2. Teslim edilen vs edilmeyen kargolar
    # 3. LIMITED vs UNLIMITED kontrolü
    # vb...
