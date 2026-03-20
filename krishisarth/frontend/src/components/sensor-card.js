/**
 * SensorCard Component
 * A reusable container for individual farm metrics.
 */
export function createSensorCard({ title, icon, value, unit, badgeType, badgeText, children = "" }) {
    const card = document.createElement('div');
    card.className = "ks-card p-6 flex flex-col h-full";
    
    card.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
                <div class="p-2 bg-primary/10 rounded-lg text-primary">
                    <i data-lucide="${icon}" class="w-5 h-5"></i>
                </div>
                <h3 class="font-bold text-gray-700 text-sm uppercase tracking-wider">${title}</h3>
            </div>
            ${badgeType ? `<span class="badge badge-${badgeType}">${badgeText}</span>` : ''}
        </div>
        
        <div class="flex items-baseline gap-1 mb-4">
            <span class="text-4xl font-extrabold tracking-tight text-gray-900">${value}</span>
            <span class="text-gray-400 font-semibold text-lg">${unit}</span>
        </div>
        
        <div class="mt-auto">
            ${children}
        </div>
    `;
    
    // Re-trigger icon rendering if needed after insertion
    return card;
}
