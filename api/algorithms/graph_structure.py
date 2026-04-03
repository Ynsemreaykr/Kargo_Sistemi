"""
Graph Structure - Temel Graph Yapısı
Node (Düğüm), Edge (Kenar), Graph sınıfları
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field



@dataclass
class DistrictNode:
    """
    İlçe düğümü
    
    Attributes:
        id: İlçe ID
        name: İlçe adı
        lat: Enlem
        lng: Boylam
        cargos: Bu ilçedeki kargolar
        total_weight: Toplam kargo ağırlığı
    """
    id: int
    name: str
    lat: float
    lng: float
    cargos: List[Dict] = field(default_factory=list)
    total_weight: float = 0.0
    
    def add_cargo(self, cargo: Dict):
        """Kargo ekle"""
        self.cargos.append(cargo)
        self.total_weight += cargo['weight_kg'] * cargo.get('quantity', 1)
    
    def __repr__(self):
        return f"Node({self.id}: {self.name}, {self.total_weight:.1f}kg)"


@dataclass
class RouteEdge:
    """
    Rota kenarı (iki ilçe arası bağlantı)
    
    Attributes:
        from_id: Başlangıç ilçe ID
        to_id: Bitiş ilçe ID
        distance: Mesafe (km)
        weight: Ağırlık (maliyet faktörü)
    """
    from_id: int
    to_id: int
    distance: float
    cost_per_km: float = 1.5  # TL/km
    
    @property
    def weight(self) -> float:
        """
        Edge ağırlığı = Mesafe + Maliyet faktörü
        
        Ağırlık càlışma mantığı:
        - Kısa mesafe = düşük ağırlık (tercih edilir)
        - Uzun mesafe = yüksek ağırlık (kaçınılır)
        - Maliyet faktörü de eklenir
        """
        return self.distance + (self.distance * self.cost_per_km * 0.01)
    
    @property
    def fuel_cost(self) -> float:
        """Yakıt maliyeti"""
        return self.distance * self.cost_per_km
    
    def __repr__(self):
        return f"Edge({self.from_id}→{self.to_id}: {self.distance:.1f}km, w={self.weight:.2f})"


class DeliveryGraph:
    """
    Teslimat Graph'ı
    
    İlçeler arası bağlantıları ve kargoları yöneten ana yapı
    """
    
    def __init__(self, districts: List[Dict], distance_matrix: Dict[Tuple[int, int], float], 
                 cost_per_km: float = 1.5):
        """
        Args:
            districts: İlçe listesi
            distance_matrix: Mesafe matrisi {(from_id, to_id): distance}
            cost_per_km: Km başı maliyet
        """
        self.nodes: Dict[int, DistrictNode] = {}
        self.edges: Dict[Tuple[int, int], RouteEdge] = {}
        self.cost_per_km = cost_per_km
        
        self._build_graph(districts, distance_matrix)
    
    def _build_graph(self, districts: List[Dict], distance_matrix: Dict):
        """Graph yapısını oluştur"""
        
        # Düğümleri ekle
        for district in districts:
            node = DistrictNode(
                id=district['id'],
                name=district['name'],
                lat=float(district['latitude']),
                lng=float(district['longitude'])
            )
            self.nodes[district['id']] = node
        
        # Kenarları ekle
        for (from_id, to_id), distance in distance_matrix.items():
            edge = RouteEdge(
                from_id=from_id,
                to_id=to_id,
                distance=distance,
                cost_per_km=self.cost_per_km
            )
            self.edges[(from_id, to_id)] = edge
    
    def add_cargos(self, cargos: List[Dict]):
        """Kargoları ilgili düğümlere ekle"""
        for cargo in cargos:
            node = self.nodes.get(cargo['district_id'])
            if node:
                node.add_cargo(cargo)
    
    def get_cargo_nodes(self) -> List[DistrictNode]:
        """Kargo olan düğümleri getir"""
        return [node for node in self.nodes.values() if node.total_weight > 0]
    
    def get_neighbors(self, node_id: int) -> List[Tuple[int, RouteEdge]]:
        """Bir düğümün komşularını getir"""
        neighbors = []
        for (from_id, to_id), edge in self.edges.items():
            if from_id == node_id:
                neighbors.append((to_id, edge))
        return neighbors
    
    def get_edge(self, from_id: int, to_id: int) -> Optional[RouteEdge]:
        """İki düğüm arası kenarı getir"""
        return self.edges.get((from_id, to_id))
    
    def calculate_route_cost(self, route: List[int]) -> float:
        """Rota maliyetini hesapla"""
        total_cost = 0.0
        
        for i in range(len(route) - 1):
            edge = self.get_edge(route[i], route[i + 1])
            if edge:
                total_cost += edge.fuel_cost
        
        return total_cost
    
    def calculate_route_distance(self, route: List[int]) -> float:
        """Rota mesafesini hesapla"""
        total_distance = 0.0
        
        for i in range(len(route) - 1):
            edge = self.get_edge(route[i], route[i + 1])
            if edge:
                total_distance += edge.distance
        
        return total_distance
    
    def get_route_info(self, route: List[int]) -> Dict:
        """Rota bilgilerini getir"""
        return {
            'route': route,
            'distance': self.calculate_route_distance(route),
            'cost': self.calculate_route_cost(route),
            'nodes': [self.nodes[node_id].name for node_id in route]
        }
    
    def __repr__(self):
        cargo_count = sum(len(node.cargos) for node in self.nodes.values())
        return f"DeliveryGraph({len(self.nodes)} nodes, {len(self.edges)} edges, {cargo_count} cargos)"


print("✓ Graph Structure module loaded")
