"""
Optimized Distribution Algorithm
Handles vehicle selection, capacity optimization, and route planning
"""

from typing import List, Dict, Any, Optional
import math


class DistributionOptimizer:
    """
    Advanced distribution algorithm with bin packing and route optimization
    """
    
    def __init__(self, cursor, system_params):
        self.cursor = cursor
        self.system_params = system_params
        self.cost_per_km = float(system_params.get('cost_per_km', 5.0))
    
    def optimize_distribution(self, cargos: List[Dict], mode: str, start_location: int) -> Dict[str, Any]:
        """
        Main optimization function
        
        Args:
            cargos: List of cargo dictionaries with id, weight_kg, quantity, destination_district_id
            mode: 'LIMITED', 'UNLIMITED', or 'RENTAL'
            start_location: Starting district ID
            
        Returns:
            Dictionary with success status, vehicle assignments, and routes
        """
        # Step 1: Get available vehicles
        vehicles = self._get_available_vehicles(mode)
        
        if not vehicles:
            return {
                'success': False,
                'error': 'Kullanılabilir araç bulunamadı!'
            }
        
        # Step 2: Expand cargos by quantity (each item separately)
        expanded_cargos = self._expand_cargos(cargos)
        
        # Step 3: Sort cargos by weight (descending) for First Fit Decreasing
        expanded_cargos.sort(key=lambda c: c['weight_kg'], reverse=True)
        
        # Step 4: Assign cargos to vehicles using bin packing
        assignments = self._assign_cargos_to_vehicles(expanded_cargos, vehicles, mode)
        
        if not assignments['success']:
            return assignments
        
        # Step 5: Optimize routes for each vehicle
        optimized_routes = self._optimize_routes(assignments['vehicle_assignments'], start_location)
        
        # Step 6: Calculate total costs
        total_cost = sum(route['cost'] for route in optimized_routes)
        total_distance = sum(route['distance'] for route in optimized_routes)
        
        return {
            'success': True,
            'routes': optimized_routes,
            'total_cost': total_cost,
            'total_distance': total_distance,
            'delivered_count': len(expanded_cargos),
            'vehicle_count': len(optimized_routes)
        }
    
    def _get_available_vehicles(self, mode: str) -> List[Dict]:
        """
        Get available vehicles based on mode
        """
        if mode == 'RENTAL':
            # For rental mode, get vehicle types that can be rented
            self.cursor.execute("""
                SELECT 
                    vt.id as vehicle_type_id,
                    vt.name,
                    vt.capacity_kg,
                    100.0 as cost_per_route,
                    TRUE as is_rented
                FROM vehicle_types vt
                ORDER BY vt.capacity_kg ASC
            """)
        else:
            # For LIMITED/UNLIMITED, get owned vehicles
            self.cursor.execute("""
                SELECT 
                    v.id as vehicle_id,
                    vt.id as vehicle_type_id,
                    vt.name,
                    vt.capacity_kg,
                    100.0 as cost_per_route,
                    v.is_rented
                FROM vehicles v
                JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
                WHERE v.is_rented = FALSE
                ORDER BY vt.capacity_kg ASC
            """)
        
        vehicles = self.cursor.fetchall()
        return [dict(v) for v in vehicles]
    
    def _expand_cargos(self, cargos: List[Dict]) -> List[Dict]:
        """
        Expand cargos by quantity (treat each item separately)
        
        Example: 1 cargo with weight=200kg, quantity=3 
                 becomes 3 separate items of 200kg each
        """
        expanded = []
        for cargo in cargos:
            quantity = cargo.get('quantity', 1)
            for i in range(quantity):
                expanded.append({
                    'id': cargo['id'],
                    'weight_kg': cargo['weight_kg'],
                    'destination_district_id': cargo['destination_district_id'],
                    'user_id': cargo.get('user_id'),
                    'item_index': i  # Track which item this is
                })
        return expanded
    
    def _assign_cargos_to_vehicles(self, cargos: List[Dict], vehicles: List[Dict], mode: str) -> Dict:
        """
        Assign cargos to vehicles using First Fit Decreasing bin packing
        
        This is optimal for minimizing number of vehicles used
        """
        vehicle_assignments = []
        remaining_cargos = cargos.copy()
        
        # Sort vehicles by capacity (smallest first) to minimize cost
        vehicles_sorted = sorted(vehicles, key=lambda v: v['capacity_kg'])
        
        while remaining_cargos:
            # Try to fit remaining cargos into smallest available vehicle
            assigned = False
            
            for vehicle in vehicles_sorted:
                batch = []
                batch_weight = 0
                capacity = vehicle['capacity_kg']
                
                # Greedy: pack as many cargos as possible into this vehicle
                for cargo in remaining_cargos[:]:
                    if batch_weight + cargo['weight_kg'] <= capacity:
                        batch.append(cargo)
                        batch_weight += cargo['weight_kg']
                        remaining_cargos.remove(cargo)
                
                if batch:
                    vehicle_assignments.append({
                        'vehicle': vehicle.copy(),
                        'cargos': batch,
                        'total_weight': batch_weight,
                        'capacity': capacity,
                        'utilization': (batch_weight / capacity) * 100
                    })
                    assigned = True
                    break  # Move to next batch
            
            if not assigned:
                # No vehicle can fit remaining cargos
                if mode == 'LIMITED':
                    return {
                        'success': False,
                        'error': f'Yetersiz araç kapasitesi! {len(remaining_cargos)} kargo taşınamıyor.',
                        'remaining_cargos': remaining_cargos,
                        'total_remaining_weight': sum(c['weight_kg'] for c in remaining_cargos)
                    }
                elif mode == 'UNLIMITED':
                    # Rent additional vehicle
                    rented_vehicle = self._rent_vehicle(remaining_cargos)
                    vehicles_sorted.append(rented_vehicle)
                    continue
                else:
                    return {
                        'success': False,
                        'error': 'Kiralık araç bulunamadı!'
                    }
        
        return {
            'success': True,
            'vehicle_assignments': vehicle_assignments
        }
    
    def _rent_vehicle(self, remaining_cargos: List[Dict]) -> Dict:
        """
        Rent smallest vehicle that can fit remaining cargos
        """
        total_weight = sum(c['weight_kg'] for c in remaining_cargos)
        
        # Get vehicle types
        self.cursor.execute("""
            SELECT id, name, capacity_kg
            FROM vehicle_types
            WHERE capacity_kg >= %s
            ORDER BY capacity_kg ASC
            LIMIT 1
        """, (total_weight,))
        
        vehicle_type = self.cursor.fetchone()
        
        if not vehicle_type:
            # Get largest vehicle if none can fit all
            self.cursor.execute("""
                SELECT id, name, capacity_kg
                FROM vehicle_types
                ORDER BY capacity_kg DESC
                LIMIT 1
            """)
            vehicle_type = self.cursor.fetchone()
        
        return {
            'vehicle_type_id': vehicle_type['id'],
            'name': vehicle_type['name'],
            'capacity_kg': vehicle_type['capacity_kg'],
            'cost_per_route': 100.0,  # Default cost
            'is_rented': True
        }
    
    def _optimize_routes(self, vehicle_assignments: List[Dict], start_location: int) -> List[Dict]:
        """
        Optimize delivery routes using nearest neighbor heuristic
        """
        optimized_routes = []
        
        for assignment in vehicle_assignments:
            vehicle = assignment['vehicle']
            cargos = assignment['cargos']
            
            # Get unique destinations
            destinations = list(set(c['destination_district_id'] for c in cargos))
            
            # Optimize order using nearest neighbor
            route_order = self._nearest_neighbor_tsp(start_location, destinations)
            
            # Calculate total distance
            total_distance = self._calculate_route_distance(start_location, route_order)
            
            # Calculate cost
            distance_cost = total_distance * self.cost_per_km
            vehicle_cost = float(vehicle.get('cost_per_route', 100.0))
            total_cost = distance_cost + vehicle_cost
            
            optimized_routes.append({
                'vehicle': vehicle,
                'cargos': cargos,
                'route_order': [start_location] + route_order,
                'distance': total_distance,
                'distance_cost': distance_cost,
                'vehicle_cost': vehicle_cost,
                'cost': total_cost,
                'total_weight': assignment['total_weight'],
                'utilization': assignment['utilization']
            })
        
        return optimized_routes
    
    def _nearest_neighbor_tsp(self, start: int, destinations: List[int]) -> List[int]:
        """
        Nearest neighbor heuristic for TSP
        """
        if not destinations:
            return []
        
        route = []
        current = start
        remaining = destinations.copy()
        
        while remaining:
            # Find nearest destination
            nearest = min(remaining, key=lambda d: self._get_distance(current, d))
            route.append(nearest)
            remaining.remove(nearest)
            current = nearest
        
        return route
    
    def _calculate_route_distance(self, start: int, route_order: List[int]) -> float:
        """
        Calculate total distance for a route
        """
        total_distance = 0
        current = start
        
        for dest in route_order:
            total_distance += self._get_distance(current, dest)
            current = dest
        
        # Return to start
        total_distance += self._get_distance(current, start)
        
        return total_distance
    
    def _get_distance(self, from_id: int, to_id: int) -> float:
        """
        Get distance between two districts (Haversine formula)
        """
        self.cursor.execute("""
            SELECT latitude, longitude
            FROM districts
            WHERE id IN (%s, %s)
            ORDER BY id
        """, (from_id, to_id))
        
        districts = self.cursor.fetchall()
        
        if len(districts) < 2:
            return 0
        
        lat1, lon1 = math.radians(districts[0]['latitude']), math.radians(districts[0]['longitude'])
        lat2, lon2 = math.radians(districts[1]['latitude']), math.radians(districts[1]['longitude'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return 6371 * c  # Earth radius in km
