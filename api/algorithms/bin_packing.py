"""
Bin Packing Algorithm - First Fit Decreasing
Kargoları araçlara optimal şekilde dağıtır
"""

from typing import List, Dict, Any


def bin_packing_first_fit_decreasing(cargos: List[Dict], vehicles: List[Dict]) -> List[Dict]:
    """
    First Fit Decreasing bin packing algoritması
    
    Mantık:
    1. Kargoları ağırlığa göre sırala (büyükten küçüğe)
    2. Her kargo için en uygun aracı bul
    3. Sığmazsa yeni araç aç
    
    Args:
        cargos: [{'district_id': 6, 'weight_kg': 500, 'quantity': 1}, ...]
        vehicles: [{'id': 1, 'capacity_kg': 500, 'type_name': 'Küçük'}, ...]
    
    Returns:
        [
            {
                'vehicle': {...},
                'cargos': [...],
                'total_weight': 450.0,
                'remaining_capacity': 50.0,
                'utilization': 90.0
            },
            ...
        ]
    """
    
    # 1. Kargoları ağırlığa göre sırala (büyükten küçüğe)
    sorted_cargos = sorted(
        cargos,
        key=lambda c: c['weight_kg'] * c.get('quantity', 1),
        reverse=True
    )
    
    # 2. Bins (araç atamaları)
    bins = []
    
    # 3. Her kargo için en uygun bin'i bul
    for cargo in sorted_cargos:
        cargo_weight = cargo['weight_kg'] * cargo.get('quantity', 1)
        
        # En uygun bin'i bul (en az boş yeri olan ama sığan)
        best_bin = None
        min_remaining = float('inf')
        
        for bin_item in bins:
            remaining = bin_item['remaining_capacity']
            if remaining >= cargo_weight and remaining < min_remaining:
                best_bin = bin_item
                min_remaining = remaining
        
        if best_bin:
            # Mevcut bin'e ekle
            best_bin['cargos'].append(cargo)
            best_bin['total_weight'] += cargo_weight
            best_bin['remaining_capacity'] -= cargo_weight
            best_bin['utilization'] = (best_bin['total_weight'] / best_bin['vehicle']['capacity_kg']) * 100
        else:
            # Yeni bin aç - en küçük uygun aracı bul
            suitable_vehicle = find_smallest_suitable_vehicle(cargo_weight, vehicles, bins)
            
            if suitable_vehicle:
                new_bin = {
                    'vehicle': suitable_vehicle,
                    'cargos': [cargo],
                    'total_weight': cargo_weight,
                    'remaining_capacity': suitable_vehicle['capacity_kg'] - cargo_weight,
                    'utilization': (cargo_weight / suitable_vehicle['capacity_kg']) * 100
                }
                bins.append(new_bin)
            else:
                # Hiçbir araç uygun değil - hata
                print(f"❌ HATA: {cargo_weight}kg kargo için uygun araç bulunamadı!")
    
    return bins


def find_smallest_suitable_vehicle(cargo_weight: float, vehicles: List[Dict], used_bins: List[Dict]) -> Dict:
    """
    Kargo için en küçük uygun aracı bul
    
    Args:
        cargo_weight: Kargo ağırlığı
        vehicles: Mevcut araçlar
        used_bins: Zaten kullanılan araçlar
    
    Returns:
        En küçük uygun araç veya None
    """
    
    # Kullanılmayan araçlar
    used_vehicle_ids = [b['vehicle']['id'] for b in used_bins]
    available_vehicles = [v for v in vehicles if v['id'] not in used_vehicle_ids]
    
    # Kapasiteye göre sırala (küçükten büyüğe)
    sorted_vehicles = sorted(available_vehicles, key=lambda v: v['capacity_kg'])
    
    # En küçük uygun aracı bul
    for vehicle in sorted_vehicles:
        if vehicle['capacity_kg'] >= cargo_weight:
            return vehicle
    
    # Hiçbiri uygun değil
    return None


def optimize_bin_assignments(bins: List[Dict]) -> List[Dict]:
    """
    Bin atamalarını optimize et
    
    İyileştirmeler:
    1. Küçük bin'leri birleştir
    2. Boş alanları minimize et
    3. Araç sayısını azalt
    """
    
    # Kullanım oranına göre sırala
    sorted_bins = sorted(bins, key=lambda b: b['utilization'])
    
    optimized = []
    merged_indices = set()
    
    for i, bin1 in enumerate(sorted_bins):
        if i in merged_indices:
            continue
        
        # Düşük kullanımlı bin'leri birleştirmeyi dene
        if bin1['utilization'] < 70:  # %70'in altı
            for j, bin2 in enumerate(sorted_bins[i+1:], start=i+1):
                if j in merged_indices:
                    continue
                
                # İki bin'i birleştirebilir miyiz?
                combined_weight = bin1['total_weight'] + bin2['total_weight']
                
                # Daha büyük bir araç var mı?
                for vehicle in [bin1['vehicle'], bin2['vehicle']]:
                    if vehicle['capacity_kg'] >= combined_weight:
                        # Birleştir
                        merged_bin = {
                            'vehicle': vehicle,
                            'cargos': bin1['cargos'] + bin2['cargos'],
                            'total_weight': combined_weight,
                            'remaining_capacity': vehicle['capacity_kg'] - combined_weight,
                            'utilization': (combined_weight / vehicle['capacity_kg']) * 100
                        }
                        optimized.append(merged_bin)
                        merged_indices.add(i)
                        merged_indices.add(j)
                        break
                
                if i in merged_indices:
                    break
        
        if i not in merged_indices:
            optimized.append(bin1)
    
    return optimized


def calculate_bin_packing_score(bins: List[Dict]) -> float:
    """
    Bin packing kalitesini skorla
    
    Kriterler:
    - Az araç = iyi
    - Yüksek kullanım = iyi
    - Dengeli dağılım = iyi
    """
    
    if not bins:
        return 0.0
    
    # Araç sayısı (az = iyi)
    vehicle_count_score = 100 / len(bins)
    
    # Ortalama kullanım (yüksek = iyi)
    avg_utilization = sum(b['utilization'] for b in bins) / len(bins)
    
    # Standart sapma (düşük = dengeli)
    utilizations = [b['utilization'] for b in bins]
    mean = sum(utilizations) / len(utilizations)
    variance = sum((u - mean) ** 2 for u in utilizations) / len(utilizations)
    std_dev = variance ** 0.5
    balance_score = max(0, 100 - std_dev)
    
    # Toplam skor
    total_score = (vehicle_count_score * 0.4 + 
                   avg_utilization * 0.4 + 
                   balance_score * 0.2)
    
    return total_score


print("✓ Bin Packing module loaded")
