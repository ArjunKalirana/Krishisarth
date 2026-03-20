import { api, setToken, clearToken } from './client.js';
import { store } from '../state/store.js';

/**
 * Auth Service
 * High-level farmer session management.
 */

export async function login(email, password) {
    try {
        console.log("AUTH: Attempting login for", email);
        const response = await api('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        // Backend returns: { success: true, data: { access_token, ... } }
        const authData = response.data;
        console.log("AUTH: Login successful. Received data:", authData);

        // 1. Store tokens in state (which now persists to storage)
        setToken(authData.access_token);
        store.setState('refreshToken', authData.refresh_token);

        // 2. Update global state with farmer info
        console.log("AUTH: Setting currentFarmer state...");
        store.setState('currentFarmer', authData);
        console.log("AUTH: Farmer state set to:", store.getState('currentFarmer'));
        
        return response;
    } catch (err) {
        console.error("AUTH: Login failed:", err);
        throw err;
    }
}

export async function register(name, email, password, phone) {
    return await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ name, email, password, phone })
    });
}

export function logout() {
    clearToken();
    store.setState('currentFarmer', null);
    store.setState('accessToken', null);
    window.location.hash = "#login";
}
