"""
Kargo İşletme Sistemi - Simulated Annealing Algoritması
Rota optimizasyonu için tavlama benzetimi
"""

import random
import math
from typing import List, Dict, Tuple
from .utils import calculate_route_distance



def simulated_annealing_optimize(
    initial_route: List[int],
    distance_matrix: Dict[Tuple[int, int], float],
    initial_temp: float = 1000.0,
    cooling_rate: float = 0.95,
    iterations: int = 1000,
    min_temp: float = 1.0
) -> List[int]:
    """
    Simulated Annealing ile rota optimizasyonu
    
    Args:
        initial_route: Başlangıç rotası [start, d1, d2, ..., start]
        distance_matrix: Mesafe matrisi
        initial_temp: Başlangıç sıcaklığı
        cooling_rate: Soğutma oranı (0-1 arası)
        iterations: Maksimum iterasyon sayısı
        min_temp: Minimum sıcaklık (algoritma durma kriteri)
    
    Returns:
        List[int]: Optimize edilmiş rota
    """
    current_route = initial_route.copy()
    current_cost = calculate_route_distance(current_route, distance_matrix)
    
    best_route = current_route.copy()
    best_cost = current_cost
    
    temperature = initial_temp
    iteration = 0
    
    while temperature > min_temp and iteration < iterations:
        # Yeni rota oluştur (2-opt swap)
        new_route = two_opt_swap(current_route)
        new_cost = calculate_route_distance(new_route, distance_matrix)
        
        # Maliyet farkı
        delta_cost = new_cost - current_cost
        
        # Kabul etme kararı
        if delta_cost < 0:
            # Daha iyi rota - direkt kabul et
            current_route = new_route
            current_cost = new_cost
            
            # En iyi rotayı güncelle
            if current_cost < best_cost:
                best_route = current_route.copy()
                best_cost = current_cost
        else:
            # Kötü rota - olasılıkla kabul et
            acceptance_prob = calculate_acceptance_probability(delta_cost, temperature)
            if random.random() < acceptance_prob:
                current_route = new_route
                current_cost = new_cost
        
        # Sıcaklığı azalt
        temperature *= cooling_rate
        iteration += 1
    
    return best_route


def two_opt_swap(route: List[int]) -> List[int]:
    """
    2-opt swap: Rotada rastgele iki segment'i ters çevir
    
    İlk ve son elemanlar (start/end) aynı olmalı, onları değiştirme
    
    Args:
        route: Rota [start, d1, d2, d3, start]
    
    Returns:
        List[int]: Yeni rota
    """
    new_route = route.copy()
    
    # İlk ve son elemanı atla (start ve end aynı)
    route_len = len(route) - 1  # Son eleman start'ın tekrarı
    
    if route_len < 3:
        # Çok kısa rota, swap yapılamaz
        return new_route
    
    # Rastgele iki index seç (start ve end hariç)
    i = random.randint(1, route_len - 2)
    j = random.randint(i + 1, route_len - 1)
    
    # i ile j arası segment'i ters çevir
    new_route[i:j+1] = reversed(new_route[i:j+1])
    
    return new_route


def calculate_acceptance_probability(delta_cost: float, temperature: float) -> float:
    """
    Simulated Annealing kabul olasılığı hesapla
    
    Metropolis kriteri: P = exp(-ΔE / T)
    
    Args:
        delta_cost: Maliyet farkı (yeni - eski)
        temperature: Mevcut sıcaklık
    
    Returns:
        float: Kabul olasılığı (0-1 arası)
    """
    if temperature == 0:
        return 0.0
    
    return math.exp(-delta_cost / temperature)


def optimize_route_with_sa(
    route_data: Dict,
    distance_matrix: Dict[Tuple[int, int], float],
    sa_params: Dict = None
) -> Dict:
    """
    Bir rota dict'ini Simulated Annealing ile optimize eder
    
    Args:
        route_data: Rota bilgisi (greedy'den gelen)
        distance_matrix: Mesafe matrisi
        sa_params: SA parametreleri (opsiyonel)
    
    Returns:
        Dict: Optimize edilmiş rota bilgisi
    """
    if sa_params is None:
        sa_params = {
            'initial_temp': 1000.0,
            'cooling_rate': 0.95,
            'iterations': 1000
        }
    
    initial_route = route_data['route']
    
    # Simulated Annealing uygula
    optimized_route = simulated_annealing_optimize(
        initial_route,
        distance_matrix,
        sa_params['initial_temp'],
        sa_params['cooling_rate'],
        sa_params['iterations']
    )
    
    # Yeni mesafeyi hesapla
    optimized_distance = calculate_route_distance(optimized_route, distance_matrix)
    
    # Rota bilgisini güncelle
    optimized_data = route_data.copy()
    optimized_data['route'] = optimized_route
    optimized_data['total_distance_km'] = optimized_distance
    optimized_data['optimization_method'] = 'simulated_annealing'
    optimized_data['distance_improvement'] = round(
        route_data['total_distance_km'] - optimized_distance, 2
    )
    optimized_data['improvement_percentage'] = round(
        ((route_data['total_distance_km'] - optimized_distance) / route_data['total_distance_km']) * 100, 1
    )
    
    return optimized_data
