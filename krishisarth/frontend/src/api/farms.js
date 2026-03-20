import { api } from './client.js';

/**
 * Farm API Service
 * Manages agricultural land entities and dashboard telemetry.
 */

export async function listFarms() {
    return await api('/farms/');
}

export async function getDashboard(farmId) {
    if (!farmId) return null;
    return await api(`/farms/${farmId}/dashboard/`);
}
