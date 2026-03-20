import { api } from './client.js';

/**
 * AI Logic API Service
 * Interacts with the KrishiSarth Decision Engine.
 */

export async function getDecisions(zoneId, limit = 10, type = null) {
    let url = `/zones/${zoneId}/ai-decisions/?limit=${limit}`;
    if (type) url += `&type=${type}`;
    return await api(url);
}

export async function runDecision(zoneId) {
    return await api(`/zones/${zoneId}/ai-decisions/run/`, {
        method: 'POST'
    });
}
