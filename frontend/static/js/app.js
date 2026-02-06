class VehicleTracker {
    constructor() {
        this.map = null;
        this.vehicles = new Map();
        this.markers = new Map();
        this.ws = null;
        this.initMap();
        this.initWebSocket();
        this.loadInitialData();
        this.setupEventListeners();
    }
    
    initMap() {
        // Centro inicial (São Paulo)
        this.map = new mapboxgl.Map({
            container: 'map',
            style: 'mapbox://styles/mapbox/streets-v12',
            center: [-46.6333, -23.5505],
            zoom: 12
        });
        
        // Adicionar controles
        this.map.addControl(new mapboxgl.NavigationControl());
        this.map.addControl(new mapboxgl.FullscreenControl());
        
        this.map.on('load', () => {
            console.log('Mapa carregado');
        });
    }
    
    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/monitoring`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket conectado');
            this.updateConnectionStatus(true);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket desconectado');
            this.updateConnectionStatus(false);
            // Tentar reconectar após 5 segundos
            setTimeout(() => this.initWebSocket(), 5000);
        };
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'position_update':
                this.updateVehiclePosition(message.data);
                break;
            case 'vehicle_status':
                this.updateVehicleStatus(message.data);
                break;
            case 'new_vehicle':
                this.addVehicleMarker(message.data);
                break;
        }
        
        // Adicionar à lista de atualizações
        this.addUpdateMessage(message);
    }
    
    async loadInitialData() {
        try {
            const response = await fetch('/api/vehicles');
            const vehicles = await response.json();
            
            vehicles.forEach(vehicle => {
                this.vehicles.set(vehicle.id, vehicle);
                
                // Buscar última posição
                this.loadVehiclePosition(vehicle.id);
            });
            
            document.getElementById('active-vehicles').textContent = vehicles.length;
        } catch (error) {
            console.error('Erro ao carregar veículos:', error);
        }
    }
    
    async loadVehiclePosition(vehicleId) {
        try {
            const response = await fetch(`/api/vehicles/${vehicleId}/position/latest`);
            const position = await response.json();
            
            if (position.latitude && position.longitude) {
                this.addVehicleMarker({
                    vehicle_id: vehicleId,
                    license_plate: position.license_plate,
                    vehicle_type: position.vehicle_type,
                    latitude: position.latitude,
                    longitude: position.longitude,
                    speed: position.speed,
                    heading: position.heading
                });
            }
        } catch (error) {
            console.error(`Erro ao carregar posição do veículo ${vehicleId}:`, error);
        }
    }
    
    addVehicleMarker(data) {
        const { vehicle_id, license_plate, vehicle_type, latitude, longitude, speed, heading } = data;
        
        // Remover marcador existente
        if (this.markers.has(vehicle_id)) {
            this.markers.get(vehicle_id).remove();
        }
        
        // Criar elemento HTML personalizado
        const el = document.createElement('div');
        el.className = `vehicle-marker ${vehicle_type}`;
        el.innerHTML = vehicle_type === 'car' ? '🚗' : '🏍️';
        el.title = `${license_plate} - ${vehicle_type}`;
        
        // Criar marcador
        const marker = new mapboxgl.Marker(el)
            .setLngLat([longitude, latitude])
            .addTo(this.map);
        
        // Criar popup
        const popup = new mapboxgl.Popup({ offset: 25 })
            .setHTML(`
                <strong>${license_plate}</strong><br>
                Tipo: ${vehicle_type === 'car' ? 'Carro' : 'Moto'}<br>
                ${speed ? `Velocidade: ${speed.toFixed(1)} km/h<br>` : ''}
                ${heading ? `Direção: ${heading.toFixed(0)}°` : ''}
            `);
        
        marker.setPopup(popup);
        this.markers.set(vehicle_id, marker);
    }
    
    updateVehiclePosition(data) {
        this.addVehicleMarker(data);
        
        // Atualizar contador de cache
        this.updateCacheCount();
    }
    
    updateVehicleStatus(data) {
        const { vehicle_id, status } = data;
        const marker = this.markers.get(vehicle_id);
        
        if (marker) {
            const el = marker.getElement();
            if (status === 'inactive') {
                el.classList.add('inactive');
            } else {
                el.classList.remove('inactive');
            }
        }
    }
    
    addUpdateMessage(message) {
        const updatesDiv = document.getElementById('updates');
        const updateItem = document.createElement('div');
        updateItem.className = 'update-item';
        
        const time = new Date(message.timestamp).toLocaleTimeString();
        let text = '';
        
        switch (message.type) {
            case 'position_update':
                text = `${time}: ${message.data.license_plate} atualizou posição`;
                break;
            case 'vehicle_status':
                text = `${time}: ${message.data.vehicle_id} status: ${message.data.status}`;
                break;
            default:
                text = `${time}: Nova mensagem recebida`;
        }
        
        updateItem.textContent = text;
        updatesDiv.prepend(updateItem);
        
        // Manter apenas 10 atualizações
        while (updatesDiv.children.length > 10) {
            updatesDiv.removeChild(updatesDiv.lastChild);
        }
    }
    
    updateConnectionStatus(connected) {
        document.getElementById('ws-connections').textContent = connected ? '1' : '0';
    }
    
    async updateCacheCount() {
        try {
            // Esta é uma simulação - em produção você teria uma rota para isso
            const count = this.markers.size;
            document.getElementById('cached-positions').textContent = count;
        } catch (error) {
            console.error('Erro ao atualizar contador de cache:', error);
        }
    }
    
    setupEventListeners() {
        // Controle de raio
        const radiusSlider = document.getElementById('radius');
        const radiusValue = document.getElementById('radius-value');
        
        radiusSlider.addEventListener('input', (e) => {
            const value = e.target.value;
            radiusValue.textContent = `${value} km`;
        });
        
        // Buscar veículos próximos ao clicar no mapa
        this.map.on('click', async (e) => {
            const { lng, lat } = e.lngLat;
            
            try {
                const response = await fetch(`/api/positions/nearby?lat=${lat}&lng=${lng}&radius_km=5`);
                const data = await response.json();
                
                if (data.vehicles.length > 0) {
                    alert(`${data.vehicles.length} veículos encontrados em ${data.radius_km}km`);
                } else {
                    alert('Nenhum veículo encontrado na área');
                }
            } catch (error) {
                console.error('Erro ao buscar veículos próximos:', error);
            }
        });
    }
    
    async searchNearby(lat, lng, radius) {
        try {
            const response = await fetch(`/api/positions/nearby?lat=${lat}&lng=${lng}&radius_km=${radius}`);
            return await response.json();
        } catch (error) {
            console.error('Erro na busca por proximidade:', error);
            return { vehicles: [] };
        }
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.tracker = new VehicleTracker();
});