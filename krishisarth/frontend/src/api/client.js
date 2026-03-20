/**
 * KrishiSarth Secure API Client
 * Features: In-memory only tokens, silent refresh, automatic retry.
 */
import { store } from '../state/store.js';

const BASE_URL = 'http://localhost:8001/v1';

/**
 * Update the in-memory and persistent access token.
 */
export function setToken(token) {
    if (token) {
        localStorage.setItem('ks_access_token', token);
    } else {
        localStorage.removeItem('ks_access_token');
    }
}

/**
 * Clear the session.
 */
export function clearToken() {
    localStorage.removeItem('ks_access_token');
    localStorage.removeItem('ks_refresh_token');
    sessionStorage.removeItem('ks_farmer');
}

/**
 * Standardized API call with automatic 401 handling.
 */
export async function api(path, options = {}) {
    try {
        const response = await fetchWithAuth(path, options);

        if (response.status === 401) {
            console.warn("API: 401 detected. Attempting silent refresh...");
            const refreshed = await refreshAccessToken();
            
            if (refreshed) {
                // Retry once with new token
                return await api(path, options);
            } else {
                // Refresh failed, force logout
                clearToken();
                window.location.hash = "#login";
                return;
            }
        }

        const data = await response.json();

        if (!response.ok) {
            // Standard KrishiSarth error envelope: { success: false, error: { code, message } }
            throw new Error(data.error?.code || 'API_ERROR');
        }

        return data;
    } catch (err) {
        console.error(`API Error [${path}]:`, err.message);
        throw err;
    }
}

/**
 * Internal fetch with Bearer token injection.
 */
async function fetchWithAuth(path, options) {
    const url = `${BASE_URL}${path}`;
    const token = localStorage.getItem('ks_access_token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return await fetch(url, {
        ...options,
        headers,
        credentials: 'include' // Required for HttpOnly refresh cookie
    });
}

/**
 * Silent Refresh Logic
 */
async function refreshAccessToken() {
    try {
        const refreshToken = store.getState('refreshToken');
        if (!refreshToken) return false;

        console.log("API: Refreshing tokens...");
        const response = await fetch(`${BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
            credentials: 'include'
        });

        if (response.ok) {
            const result = await response.json();
            // Backend returns: { success: true, data: { access_token, ... } }
            setToken(result.data.access_token);
            store.setState('refreshToken', result.data.refresh_token);
            return true;
        }
        return false;
    } catch (err) {
        return false;
    }
}
