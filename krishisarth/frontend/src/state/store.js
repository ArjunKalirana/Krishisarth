/**
 * KrishiSarth Core State Management
 * Minimal Pub/Sub implementation for reactive UI updates.
 */

class Store {
    constructor() {
        this.state = {
            currentFarmer: JSON.parse(sessionStorage.getItem('ks_farmer')),
            currentFarm: JSON.parse(localStorage.getItem('ks_current_farm')),
            accessToken: localStorage.getItem('ks_access_token'),
            refreshToken: localStorage.getItem('ks_refresh_token'),
            activeZones: [],
            unreadAlertCount: 0,
            sensorData: {}, // Reactive telemetry cache
            activePage: window.location.hash || '#dashboard'
        };
        this.listeners = {};
    }

    /**
     * Subscribe to changes for a specific key
     */
    subscribe(key, callback) {
        if (!this.listeners[key]) {
            this.listeners[key] = [];
        }
        this.listeners[key].push(callback);
    }

    /**
     * Set state and notify all subscribers of the specific key
     */
    setState(key, value) {
        if (this.state[key] === value) return;
        
        this.state[key] = value;

        // Persistence Logic
        if (key === 'currentFarmer') {
            sessionStorage.setItem('ks_farmer', JSON.stringify(value));
        }
        if (key === 'currentFarm') {
            localStorage.setItem('ks_current_farm', JSON.stringify(value));
        }
        if (key === 'refreshToken') {
            localStorage.setItem('ks_refresh_token', value);
        }

        this.publish(key, value);
    }

    /**
     * Notify all listeners for a specific key
     */
    publish(key, value) {
        if (this.listeners[key]) {
            this.listeners[key].forEach(callback => callback(value));
        }
    }

    /**
     * Get current value for a key
     */
    getState(key) {
        return this.state[key];
    }
}

// Global Singleton Instance
export const store = new Store();
