"""
ROUTES.PY GÜNCELLEMESI
Satır 364-374 arasını aşağıdaki kodla değiştirin:
"""

            # GREEDY+ (İYİLEŞTİRİLMİŞ)
            print("\n⚡ GREEDY+ KULLANILIYOR (İYİLEŞTİRİLMİŞ)...")
            
            from algorithms import improved_greedy_algorithm
            
            # 1. İyileştirilmiş Greedy ile rotalar (kendi araçlarla)
            initial_routes = improved_greedy_algorithm(
                cargos, 
                districts, 
                own_vehicles
            )
            
            print(f"\n✓ Kendi araçlarla {len(initial_routes)} rota oluşturuldu")
