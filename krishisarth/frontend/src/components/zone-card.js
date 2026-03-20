import { startIrrigation, stopIrrigation } from '../api/control.js';
import { showToast } from './toast.js';

/**
 * ZoneCard Component (Connected)
 * Integrates with the backend Command Engine.
 */
export function createZoneCard({ id, name, lastIrrig, moisture, initialState = false }) {
    const card = document.createElement('div');
    let isOn = initialState;
    let activeDuration = 20;

    const updateUI = () => {
        card.className = `ks-card p-6 transition-all duration-500 border-l-4 ${isOn ? 'bg-primary/5 border-l-primary-light shadow-inner shadow-primary/5' : 'bg-white border-l-gray-200'}`;
        
        card.innerHTML = `
            <div class="flex items-start justify-between mb-6">
                <div>
                    <h3 class="font-black text-gray-800 uppercase tracking-tight text-lg">${name}</h3>
                    <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-0.5">Last Irrig: ${lastIrrig}</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <span class="badge ${moisture < 30 ? 'badge-dry' : moisture < 70 ? 'badge-ok' : 'badge-wet'}">${moisture}% Moisture</span>
                    <div class="flex items-center gap-2">
                        <span class="text-[9px] font-black ${isOn ? 'text-primary animate-pulse' : 'text-gray-400'} uppercase tracking-tighter">
                            ${isOn ? 'Irrigating...' : 'Status: Idle'}
                        </span>
                        <!-- Toggle Switch -->
                        <button class="toggle-btn w-12 h-6 rounded-full relative transition-colors ${isOn ? 'bg-primary' : 'bg-gray-200'}" id="toggle-${id}">
                            <div class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform transform ${isOn ? 'translate-x-6' : ''}"></div>
                        </button>
                    </div>
                </div>
            </div>

            <div class="space-y-4">
                <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest">Select duration</p>
                <div class="flex gap-2">
                    ${[10, 20, 30].map(dur => `
                        <button class="dur-btn flex-1 py-2 rounded-lg text-xs font-black transition-all border-2 ${activeDuration === dur ? 'bg-primary text-white border-primary shadow-sm' : 'bg-gray-50 text-gray-500 border-gray-100 hover:border-primary/30'}" data-dur="${dur}">
                            ${dur}M
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        // Logic Attachment
        const toggle = card.querySelector(`#toggle-${id}`);
        toggle.onclick = async (e) => {
            e.stopPropagation();
            toggle.disabled = true; // Prevent double-tap
            
            try {
                if (!isOn) {
                    await startIrrigation(id, activeDuration);
                    isOn = true;
                    showToast(`${name}: Irrigation Initialized`, 'success');
                } else {
                    const res = await stopIrrigation(id);
                    isOn = false;
                    showToast(`Stopped. ${res.data?.water_used_l || 0}L Used`, 'success');
                }
            } catch (err) {
                // Conflict Handling
                const codes = {
                    'PUMP_ALREADY_RUNNING': 'System Conflict: Pump is already in use by another zone.',
                    'TANK_LEVEL_CRITICAL': 'Access Denied: Tank below 10% safety limit.',
                    'DEVICE_OFFLINE': 'Network Error: Command queued for LoRa node.'
                };
                showToast(codes[err.message] || "Command failed: Hardware verification error", 'error');
            } finally {
                toggle.disabled = false;
                updateUI();
            }
        };

        card.querySelectorAll('.dur-btn').forEach(btn => {
            btn.onclick = () => {
                activeDuration = parseInt(btn.dataset.dur);
                updateUI();
            };
        });
    };

    updateUI();
    return card;
}
