import { api } from './client.js';

/**
 * Historical Analytics API Service
 * Metrics aggregation and raw data export.
 */

export async function getAnalytics(farmId, from, to, zoneId = null) {
    let url = `/farms/${farmId}/analytics/`;
    const params = new URLSearchParams({ from, to });
    if (zoneId) params.append('zone_id', zoneId);
    
    return await api(`${url}?${params.toString()}`);
}

export function exportCSV(farmId, from, to) {
    // Need absolute URL for direct browser access
    const BASE_URL = 'http://localhost:8001/v1';
    const url = `${BASE_URL}/farms/${farmId}/analytics/export/?from=${from}&to=${to}`;
    window.location.href = url;
}
