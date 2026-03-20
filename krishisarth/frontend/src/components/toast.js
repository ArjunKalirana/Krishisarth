/**
 * KrishiSarth Toast System
 * Provides non-intrusive feedback for hardware actions.
 */

let toastContainer = null;
const activeToasts = [];

function getContainer() {
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = "fixed bottom-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none";
        document.body.appendChild(toastContainer);
    }
    return toastContainer;
}

export function showToast(message, type = 'success', duration = 4000) {
    const container = getContainer();

    // Max 3 toasts
    if (activeToasts.length >= 3) {
        const oldest = activeToasts.shift();
        oldest.remove();
    }

    const toast = document.createElement('div');
    const colors = {
        success: 'bg-primary border-primary-light text-white',
        error: 'bg-red-600 border-red-400 text-white',
        warning: 'bg-amber-500 border-amber-300 text-white',
        info: 'bg-gray-800 border-gray-600 text-white'
    };

    toast.className = `
        ${colors[type] || colors.info} 
        px-6 py-4 rounded-xl border-2 shadow-2xl pointer-events-auto
        flex items-center gap-3 animate-in slide-in-from-right-10 duration-500
        min-w-[280px] max-w-[400px]
    `;

    const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'alert-octagon' : 'info';
    
    toast.innerHTML = `
        <i data-lucide="${icon}" class="w-5 h-5 shrink-0 opacity-80"></i>
        <div class="flex-grow">
            <p class="text-[10px] font-black uppercase tracking-widest opacity-60 mb-0.5">${type}</p>
            <p class="text-xs font-bold leading-tight uppercase tracking-tight">${message}</p>
        </div>
        <button class="opacity-40 hover:opacity-100 transition-opacity" onclick="this.parentElement.remove()">
            <i data-lucide="x" class="w-4 h-4"></i>
        </button>
    `;

    container.appendChild(toast);
    activeToasts.push(toast);

    if (window.lucide) window.lucide.createIcons();

    // Auto-dismiss
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.add('animate-out', 'fade-out', 'slide-out-to-right-10');
            setTimeout(() => {
                toast.remove();
                const idx = activeToasts.indexOf(toast);
                if (idx > -1) activeToasts.splice(idx, 1);
            }, 500);
        }
    }, duration);
}
