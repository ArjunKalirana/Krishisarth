/**
 * KrishiSarth Formatting Utilities
 * Standardizes agricultural data presentation.
 */

export function formatDate(isoString) {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-IN', { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

export function formatLitres(value) {
    const num = parseFloat(value) || 0;
    return new Intl.NumberFormat('en-IN').format(num) + ' L';
}

export function formatDuration(minutes) {
    if (minutes < 60) return `${minutes} min`;
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return m > 0 ? `${h}h ${m}min` : `${h}h`;
}

export function roundTo(value, decimals = 1) {
    const factor = Math.pow(10, decimals);
    return Math.round(value * factor) / factor;
}

export function getMoistureStatus(pct) {
    if (pct < 20) return { label: 'CRITICAL', class: 'badge-dry' };
    if (pct < 40) return { label: 'DRY', class: 'badge-dry' };
    if (pct < 75) return { label: 'OPTIMAL', class: 'badge-ok' };
    return { label: 'SATURATED', class: 'badge-wet' };
}
