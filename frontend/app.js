/**
 * Kargo İşletme Sistemi - Frontend JavaScript
 * API URL: http://localhost:5001
 */

// API Base URL
const API_URL = 'http://localhost:5002/api';

// Global Variables
let map;
let districts = [];
let currentRoutes = [];
let routeLayers = [];
let districtMarkers = [];

// ===========================
// Initialize App
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadDistricts();
    setupEventListeners();
    addInitialCargoRow();
});

// ===========================
// Map Initialization
// ===========================
function initMap() {
    // Kocaeli merkezli harita
    map = L.map('map').setView([40.7654, 29.7400], 10);

    // OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
}

// ===========================
// Load Districts from API
// ===========================
async function loadDistricts() {
    try {
        const response = await fetch(`${API_URL}/districts`);
        const data = await response.json();

        if (data.success) {
            districts = data.data;
            addDistrictMarkers();
            console.log(`✓ ${districts.length} ilçe yüklendi`);
        } else {
            showError('İlçeler yüklenemedi');
        }
    } catch (error) {
        console.error('İlçe yükleme hatası:', error);
        showError('API bağlantı hatası. Backend çalışıyor mu?');
    }
}

// ===========================
// Add District Markers to Map
// ===========================
function addDistrictMarkers() {
    districts.forEach(district => {
        const marker = L.circleMarker([district.latitude, district.longitude], {
            radius: 8,
            fillColor: '#6366f1',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);

        marker.bindPopup(`
            <div style="text-align: center;">
                <strong style="font-size: 14px;">${district.name}</strong><br>
                <small style="color: #666;">İlçe Merkezi</small>
            </div>
        `);

        districtMarkers.push(marker);
    });
}

// ===========================
// Event Listeners
// ===========================
function setupEventListeners() {
    document.getElementById('addCargoBtn').addEventListener('click', addCargoRow);
    document.getElementById('createScenarioBtn').addEventListener('click', createScenario);
    document.getElementById('clearMapBtn').addEventListener('click', clearMap);
}

// ===========================
// Add Cargo Row
// ===========================
let cargoCounter = 0;

function addCargoRow() {
    cargoCounter++;
    const cargoList = document.getElementById('cargoList');

    const cargoRow = document.createElement('div');
    cargoRow.className = 'cargo-row';
    cargoRow.dataset.id = cargoCounter;

    cargoRow.innerHTML = `
        <div class="cargo-row-header">
            <span class="cargo-row-title">Kargo #${cargoCounter}</span>
            <button class="remove-cargo-btn" onclick="removeCargoRow(${cargoCounter})">×</button>
        </div>
        <div class="cargo-inputs">
            <select class="form-control cargo-district" required>
                <option value="">İlçe Seçin</option>
                ${districts.map(d => `<option value="${d.id}">${d.name}</option>`).join('')}
            </select>
            <div class="input-group">
                <input type="number" class="form-control cargo-weight" placeholder="Ağırlık (kg)" min="1" required>
                <input type="number" class="form-control cargo-quantity" placeholder="Adet" min="1" required>
            </div>
        </div>
    `;

    cargoList.appendChild(cargoRow);
}

function addInitialCargoRow() {
    // İlk kargo satırını otomatik ekle
    setTimeout(() => {
        if (districts.length > 0) {
            addCargoRow();
        }
    }, 500);
}

// ===========================
// Remove Cargo Row
// ===========================
function removeCargoRow(id) {
    const row = document.querySelector(`[data-id="${id}"]`);
    if (row) {
        row.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => row.remove(), 300);
    }
}

// ===========================
// Create Scenario
// ===========================
async function createScenario() {
    // Validate and collect cargo data
    const cargoRows = document.querySelectorAll('.cargo-row');
    if (cargoRows.length === 0) {
        showError('En az bir kargo ekleyin');
        return;
    }

    const cargos = [];
    let isValid = true;

    cargoRows.forEach(row => {
        const districtId = row.querySelector('.cargo-district').value;
        const weight = row.querySelector('.cargo-weight').value;
        const quantity = row.querySelector('.cargo-quantity').value;

        if (!districtId || !weight || !quantity) {
            isValid = false;
            return;
        }

        cargos.push({
            district_id: parseInt(districtId),
            weight_kg: parseFloat(weight),
            quantity: parseInt(quantity)
        });
    });

    if (!isValid) {
        showError('Lütfen tüm kargo bilgilerini doldurun');
        return;
    }

    const scenarioType = document.getElementById('scenarioType').value;

    // Show loading state
    showLoading(true);
    hideResults();

    try {
        const response = await fetch(`${API_URL}/scenarios`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scenario_type: scenarioType,
                cargos: cargos
            })
        });

        const data = await response.json();

        if (data.success) {
            console.log('✓ Senaryo oluşturuldu:', data.data);
            showResults(data.data);
            await loadAndDisplayRoutes(data.data.scenario_id);
        } else {
            showError(data.error || 'Senaryo oluşturulamadı');
        }
    } catch (error) {
        console.error('Senaryo oluşturma hatası:', error);
        showError('API bağlantı hatası');
    } finally {
        showLoading(false);
    }
}

// ===========================
// Load and Display Routes
// ===========================
async function loadAndDisplayRoutes(scenarioId) {
    try {
        const response = await fetch(`${API_URL}/routes/${scenarioId}`);
        const data = await response.json();

        if (data.success) {
            currentRoutes = data.data;
            displayRoutesOnMap(currentRoutes);
            console.log(`✓ ${currentRoutes.length} rota görselleştirildi`);
        } else {
            showError('Rotalar yüklenemedi');
        }
    } catch (error) {
        console.error('Rota yükleme hatası:', error);
        showError('Rotalar yüklenemedi');
    }
}

// ===========================
// Display Routes on Map
// ===========================
function displayRoutesOnMap(routes) {
    // Clear existing routes
    clearRoutes();

    const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];

    routes.forEach((route, index) => {
        const color = colors[index % colors.length];

        // Create coordinates array from stops
        const coordinates = route.stops.map(stop => [stop.latitude, stop.longitude]);

        // Draw polyline
        const polyline = L.polyline(coordinates, {
            color: color,
            weight: 4,
            opacity: 0.8,
            smoothFactor: 1
        }).addTo(map);

        // Add popup
        polyline.bindPopup(`
            <div style="min-width: 200px;">
                <strong style="font-size: 14px;">🚚 Rota ${index + 1}</strong><br>
                <hr style="margin: 8px 0; border-color: #ddd;">
                <strong>Araç Tipi:</strong> ${route.vehicle_type_name}<br>
                <strong>Mesafe:</strong> ${route.distance} km<br>
                <strong>Maliyet:</strong> ${route.cost} TL<br>
                <hr style="margin: 8px 0; border-color: #ddd;">
                <strong>Duraklar:</strong><br>
                ${route.stops.map((s, i) => `${i + 1}. ${s.name}`).join('<br>')}
            </div>
        `);

        routeLayers.push(polyline);

        // Add animated markers for route
        addRouteMarkers(route.stops, color);
    });

    // Fit map to show all routes
    if (routeLayers.length > 0) {
        const group = L.featureGroup(routeLayers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// ===========================
// Add Route Markers
// ===========================
function addRouteMarkers(stops, color) {
    stops.forEach((stop, index) => {
        const marker = L.circleMarker([stop.latitude, stop.longitude], {
            radius: 6,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
        }).addTo(map);

        marker.bindTooltip(`${index + 1}`, {
            permanent: false,
            direction: 'center',
            className: 'route-number-tooltip'
        });

        routeLayers.push(marker);
    });
}

// ===========================
// Clear Routes
// ===========================
function clearRoutes() {
    routeLayers.forEach(layer => map.removeLayer(layer));
    routeLayers = [];
}

// ===========================
// Clear Map
// ===========================
function clearMap() {
    clearRoutes();
    hideResults();
    console.log('✓ Harita temizlendi');
}

// ===========================
// UI Helper Functions
// ===========================
function showLoading(show) {
    const loadingState = document.getElementById('loadingState');
    loadingState.style.display = show ? 'block' : 'none';
}

function showResults(data) {
    const resultsPanel = document.getElementById('resultsPanel');
    document.getElementById('totalCost').textContent = `${data.total_cost.toFixed(2)} TL`;
    document.getElementById('totalDistance').textContent = `${data.total_distance.toFixed(2)} km`;
    document.getElementById('routeCount').textContent = data.route_count;
    resultsPanel.style.display = 'block';
}

function hideResults() {
    document.getElementById('resultsPanel').style.display = 'none';
}

function showError(message) {
    alert(`❌ Hata: ${message}`);
    console.error(message);
}

// ===========================
// CSS Animation for slideOut
// ===========================
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(-20px);
        }
    }
    
    .route-number-tooltip {
        background: transparent;
        border: none;
        box-shadow: none;
        font-weight: bold;
        font-size: 10px;
        color: white;
    }
`;
document.head.appendChild(style);
