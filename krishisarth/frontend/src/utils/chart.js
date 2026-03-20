/**
 * KrishiSarth Charting Utility
 * Zero-dependency SVG and CSS-based visualizations.
 */

/**
 * Draws a multi-line SVG chart
 * @param {Object} options { width, height, padding, datasets: [{ color, data: [] }], labels: [] }
 */
export function drawLineChart(options) {
    const { width = 600, height = 300, padding = 40, datasets, labels } = options;
    const chartW = width - padding * 2;
    const chartH = height - padding * 2;

    const maxVal = 100; // Moisture % scale
    const getY = (v) => padding + chartH - (v / maxVal) * chartH;
    const getX = (i) => padding + (i / (labels.length - 1)) * chartW;

    let svgContent = `
        <svg viewBox="0 0 ${width} ${height}" class="w-full h-full font-mono">
            <!-- Grid Lines -->
            ${[20, 40, 60, 80].map(v => `
                <line x1="${padding}" y1="${getY(v)}" x2="${width - padding}" y2="${getY(v)}" stroke="#f3f4f6" stroke-width="1" />
                <text x="${padding - 10}" y="${getY(v) + 4}" text-anchor="end" fill="#9ca3af" style="font-size: 10px; font-weight: bold;">${v}%</text>
            `).join('')}

            <!-- X Axis Labels -->
            ${labels.map((l, i) => `
                <text x="${getX(i)}" y="${height - padding + 20}" text-anchor="middle" fill="#9ca3af" style="font-size: 10px; font-weight: bold;">${l}</text>
            `).join('')}

            <!-- Data Lines -->
            ${datasets.map(ds => {
                const points = ds.data.map((v, i) => `${getX(i)},${getY(v)}`).join(' ');
                return `<polyline fill="none" stroke="${ds.color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${points}" class="transition-all duration-700 hover:stroke-width-4" />`;
            }).join('')}
        </svg>
    `;

    return svgContent;
}

/**
 * Draws a CSS-based bar chart
 * @param {Array} data [{ label, value, highlight }]
 */
export function drawBarChart(data) {
    const maxVal = Math.max(...data.map(d => d.value)) * 1.2;
    
    return `
        <div class="flex items-end justify-between h-48 gap-2 pt-8">
            ${data.map(d => `
                <div class="flex-1 flex flex-col items-center group">
                    <span class="text-[10px] font-black text-gray-400 mb-2 opacity-0 group-hover:opacity-100 transition-opacity">${d.value}L</span>
                    <div class="w-full bg-primary/20 rounded-t-md relative transition-all duration-500 hover:bg-primary/40 ${d.highlight ? 'bg-primary ring-4 ring-primary/10' : ''}" 
                         style="height: ${(d.value / maxVal) * 100}%">
                    </div>
                    <span class="text-[10px] font-bold text-gray-500 mt-2 uppercase tracking-tighter">${d.label}</span>
                </div>
            `).join('')}
        </div>
    `;
}
