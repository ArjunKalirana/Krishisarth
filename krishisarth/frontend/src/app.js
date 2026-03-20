import { store } from './state/store.js';
import { telemetryWS } from './api/websocket.js';
import { listFarms } from './api/farms.js';
import { renderNavbar } from './components/navbar.js';
import { renderDashboard } from './pages/dashboard.js';
import { renderAIDecisions } from './pages/ai-decisions.js';
import { renderControl } from './pages/control.js';
import { renderAnalytics } from './pages/analytics.js';
import { renderLogin } from './pages/login.js';

/**
 * KrishiSarth App Coordinator
 * Manages the transition between pages and initializes global components.
 */
function initApp() {
    console.log("KrishiSarth: Booting frontend core...");
    
    // 1. Initial Render
    renderNavbar();

    // 2. Route Guard & Routing Engine
    const route = () => {
        const hash = window.location.hash || '#dashboard';
        const appRoot = document.getElementById('app-root');
        const farmer = store.getState('currentFarmer');

        console.log(`ROUTER: Navigating to ${hash}. currentFarmer:`, farmer);

        // Route Guard: Redirect to #login if unauthenticated, 
        // unless they are explicitly on #login or #register
        if (!farmer && hash !== '#login' && hash !== '#register') {
            console.warn("ROUTE_GUARD: Unauthenticated access. Redirecting to #login.");
            window.location.hash = "#login";
            return;
        }

        // Auto-select first farm if none selected
        if (farmer && !store.getState('currentFarm')) {
            console.log("ROUTER: Bootstrapping farm context...");
            listFarms().then(res => {
                if (res && res.data && res.data.length > 0) {
                    store.setState('currentFarm', res.data[0]);
                    telemetryWS.connect(res.data[0].id);
                }
            }).catch(err => console.error("ROUTER: Bootstrap failed:", err));
        }

        switch(hash) {
            case '#login':
                document.getElementById('navbar-root').classList.add('hidden'); // Hide Nav on Login
                appRoot.innerHTML = '';
                appRoot.appendChild(renderLogin());
                break;
            case '#dashboard':
                document.getElementById('navbar-root').classList.remove('hidden');
                appRoot.innerHTML = '';
                appRoot.appendChild(renderDashboard());
                break;
            case '#ai':
                document.getElementById('navbar-root').classList.remove('hidden');
                appRoot.innerHTML = '';
                appRoot.appendChild(renderAIDecisions());
                break;
            case '#control':
                document.getElementById('navbar-root').classList.remove('hidden');
                appRoot.innerHTML = '';
                appRoot.appendChild(renderControl());
                break;
            case '#analytics':
                document.getElementById('navbar-root').classList.remove('hidden');
                appRoot.innerHTML = '';
                appRoot.appendChild(renderAnalytics());
                break;
            default:
                appRoot.innerHTML = `<h1 class="text-3xl font-extrabold text-gray-900 mb-6 font-mono">404: PLOT_NOT_FOUND</h1>`;
        }
    };

    window.addEventListener('hashchange', route);
    route(); // Trigger initial route
}

// Start Application
document.addEventListener('DOMContentLoaded', initApp);
