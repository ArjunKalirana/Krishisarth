import { store } from '../state/store.js';
import { t, getLanguage, setLanguage, getAvailableLanguages } from '../utils/i18n.js';
import { clearToken } from '../api/client.js';

let _navbarMounted = false;

/**
 * Navbar Component
 * Renders the primary navigation system with mobile responsiveness.
 */
export function renderNavbar() {
    const root = document.getElementById('navbar-root');
    if (!root) return;

    const activePage = store.getState('activePage');
    const farmer = store.getState('currentFarmer');
    const unreadCount = store.getState('unreadAlertCount');

    const template = `
        <nav class="bg-white/80 backdrop-blur-md border-b border-gray-100 px-4 py-3 shadow-sm">
            <div class="container mx-auto flex items-center justify-between">
                <!-- Logo -->
                <a href="#dashboard" class="flex items-center gap-2">
                    <div class="text-primary">
                        <i data-lucide="droplets" class="w-8 h-8"></i>
                    </div>
                    <span class="text-xl font-bold tracking-tight text-gray-900">
                        Krishi<span class="text-primary">Sarth</span>
                    </span>
                    <div class="pulse-dot ml-1" title="Live System Connection"></div>
                </a>

                <!-- Desktop Navigation -->
                <div class="hidden md:flex items-center gap-8">
                    <a href="#dashboard" class="nav-link ${activePage === '#dashboard' ? 'active' : ''}" data-page="#dashboard">${t('nav_dashboard')}</a>
                    <a href="#ai" class="nav-link ${activePage === '#ai' ? 'active' : ''}" data-page="#ai">${t('nav_ai')}</a>
                    <a href="#control" class="nav-link ${activePage === '#control' ? 'active' : ''}" data-page="#control">${t('nav_control')}</a>
                    <a href="#analytics" class="nav-link ${activePage === '#analytics' ? 'active' : ''}" data-page="#analytics">${t('nav_analytics')}</a>
                    <a href="#farm3d" class="nav-link ${activePage === '#farm3d' ? 'active' : ''}" data-page="#farm3d">${t('nav_farm3d')}</a>
                </div>

                <!-- Farmer Actions -->
                <div class="flex items-center gap-4">
                    <!-- Language Switcher -->
                    <div class="flex items-center gap-1 bg-gray-100 rounded-lg p-1" id="lang-switcher">
                        ${getAvailableLanguages().map(l => `
                            <button
                                class="lang-btn px-2 py-1 rounded-md text-[10px] font-black transition-all
                                    ${getLanguage() === l.code
                                        ? 'bg-white text-primary shadow-sm'
                                        : 'text-gray-400 hover:text-gray-600'}"
                                data-lang="${l.code}"
                                title="${l.name}"
                            >${l.label}</button>
                        `).join('')}
                    </div>
                    <div class="relative cursor-pointer">
                        <i data-lucide="bell" class="w-6 h-6 text-gray-500 hover:text-primary transition-colors"></i>
                        ${unreadCount > 0 ? `<span class="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold px-1 rounded-full border-2 border-white">${unreadCount}</span>` : ''}
                    </div>
                    <div class="relative pl-4 border-l border-gray-200">
                        <div id="profile-menu-btn" class="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity">
                            <div class="w-9 h-9 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold text-sm">
                                ${farmer ? farmer.name.split(' ').map(n => n[0]).join('') : 'F'}
                            </div>
                            <span class="hidden lg:block font-semibold text-sm text-gray-700">${farmer ? farmer.name : 'Farmer'}</span>
                            <i data-lucide="chevron-down" class="w-4 h-4 text-gray-400"></i>
                        </div>
                        <!-- Dropdown Menu -->
                        <div id="profile-dropdown" class="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-2 hidden z-50">
                            <button id="logout-btn" class="w-full text-left px-4 py-3 text-sm font-semibold text-red-600 hover:bg-red-50 flex items-center gap-3 transition-colors">
                                <i data-lucide="log-out" class="w-4 h-4"></i>
                                Logout
                            </button>
                        </div>
                    </div>
                    
                    <!-- Mobile Menu Button -->
                    <button id="mobile-menu-btn" class="md:hidden text-gray-600 hover:text-primary">
                        <i data-lucide="menu" class="w-7 h-7"></i>
                    </button>
                </div>
            </div>
        </nav>

        <style>
            .nav-link {
                font-weight: 600;
                font-size: 0.925rem;
                color: #6B7280; /* text-gray-500 */
                transition: all 0.2s ease;
                position: relative;
                padding: 4px 0;
            }
            .nav-link:hover {
                color: var(--color-primary);
            }
            .nav-link.active {
                color: var(--color-primary);
            }
            .nav-link.active::after {
                content: '';
                position: absolute;
                bottom: -2px;
                left: 0;
                right: 0;
                height: 3px;
                background-color: var(--color-primary);
                border-radius: 99px;
            }
        </style>
    `;

    root.innerHTML = template;
    
    // Profile Dropdown Toggle
    const profileBtn = root.querySelector('#profile-menu-btn');
    const profileDropdown = root.querySelector('#profile-dropdown');
    const logoutBtn = root.querySelector('#logout-btn');

    if (profileBtn && profileDropdown) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profileDropdown.classList.toggle('hidden');
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!profileBtn.contains(e.target) && !profileDropdown.contains(e.target)) {
                profileDropdown.classList.add('hidden');
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            clearToken();
            store.setState('currentFarmer', null);
            store.setState('currentFarm', null);
            window.location.hash = '#login';
        });
    }

    // Language switcher
    root.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            setLanguage(btn.dataset.lang);
            // Re-render navbar to update active language
            _navbarMounted = false;
            renderNavbar();
            // Re-render current page to apply new language
            const event = new HashChangeEvent('hashchange');
            window.dispatchEvent(event);
        });
    });

    // Initialize Icons
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Hash change listener for re-render (Internal Navigation)
    if (!_navbarMounted) {
        window.addEventListener('hashchange', () => {
            const newHash = window.location.hash || '#dashboard';
            store.setState('activePage', newHash);
            renderNavbar();
        });
        _navbarMounted = true;
    }
}
