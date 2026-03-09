/**
 * Unified admin navigation + sidebar behavior.
 * - Sidebar toggle on mobile
 * - AJAX navigation for inventory and store admin pages
 */
(function () {
    'use strict';

    const MOBILE_BREAKPOINT = 768;
    const AJAX_PATH_PREFIXES = ['/inventory/', '/store/admin/'];

    const APP_UI = {
        contentContainer: null,
        isLoading: false,
        currentUrl: window.location.href,
        loadedExternalScripts: new Set(),
        resizeTimer: null,

        init() {
            this.contentContainer = document.getElementById('admin-content-container');
            this.cacheLoadedExternalScripts();

            this.applySidebarState();
            this.syncActiveLinks(window.location.href);

            if (!window.history.state || !window.history.state.url) {
                window.history.replaceState({ url: window.location.href }, '', window.location.href);
            }

            document.addEventListener('click', (event) => this.handleDocumentClick(event));
            window.addEventListener('resize', () => this.handleResize());
            window.addEventListener('popstate', (event) => this.handlePopState(event));
        },

        cacheLoadedExternalScripts() {
            document.querySelectorAll('script[src]').forEach((script) => {
                try {
                    const absoluteSrc = new URL(script.getAttribute('src'), window.location.origin).href;
                    this.loadedExternalScripts.add(absoluteSrc);
                } catch (_) {
                    // Ignore malformed URLs
                }
            });
        },

        isMobile() {
            return window.innerWidth < MOBILE_BREAKPOINT;
        },

        getSidebarElements() {
            return {
                sidebar: document.getElementById('sidebar'),
                toggleButton: document.getElementById('sidebarCollapse'),
                body: document.body,
            };
        },

        setSidebarAriaExpanded(isExpanded) {
            const { toggleButton } = this.getSidebarElements();
            const value = isExpanded ? 'true' : 'false';
            if (toggleButton) {
                toggleButton.setAttribute('aria-expanded', value);
            }
        },

        applySidebarState() {
            const { sidebar, body } = this.getSidebarElements();
            if (!sidebar) {
                return;
            }

            if (this.isMobile()) {
                sidebar.classList.remove('active');
                body.classList.remove('sidebar-open');
                this.setSidebarAriaExpanded(false);
                return;
            }

            sidebar.classList.remove('active');
            body.classList.remove('sidebar-open');
            body.classList.remove('sidebar-collapsed');
            this.setSidebarAriaExpanded(false);
        },

        toggleSidebar() {
            const { sidebar, body } = this.getSidebarElements();
            if (!sidebar) {
                return;
            }

            if (!this.isMobile()) {
                return;
            }

            const isOpen = sidebar.classList.toggle('active');
            body.classList.toggle('sidebar-open', isOpen);
            this.setSidebarAriaExpanded(isOpen);
        },

        closeSidebarOnMobile() {
            if (!this.isMobile()) {
                return;
            }

            const { sidebar, body } = this.getSidebarElements();
            if (!sidebar) {
                return;
            }

            sidebar.classList.remove('active');
            body.classList.remove('sidebar-open');
            this.setSidebarAriaExpanded(false);
        },

        handleResize() {
            clearTimeout(this.resizeTimer);
            this.resizeTimer = setTimeout(() => {
                this.applySidebarState();
            }, 120);
        },

        handleDocumentClick(event) {
            const toggleButton = event.target.closest('#sidebarCollapse');
            if (toggleButton) {
                event.preventDefault();
                event.stopPropagation();
                this.toggleSidebar();
                return;
            }

            if (this.isMobile()) {
                const { sidebar } = this.getSidebarElements();
                if (sidebar && sidebar.classList.contains('active') && !sidebar.contains(event.target)) {
                    this.closeSidebarOnMobile();
                }
            }

            this.handleAjaxNavigation(event);
        },

        handleAjaxNavigation(event) {
            if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
                return;
            }

            const link = event.target.closest('a');
            if (!link) {
                return;
            }

            if (!this.contentContainer || !this.shouldHandleLinkInAjax(link)) {
                return;
            }

            event.preventDefault();
            this.loadPage(link.href, link, true);
        },

        shouldHandleLinkInAjax(link) {
            const href = link.getAttribute('href');
            if (!href) {
                return false;
            }

            if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) {
                return false;
            }

            if (link.hasAttribute('download') || link.hasAttribute('data-no-ajax')) {
                return false;
            }

            const target = (link.getAttribute('target') || '').toLowerCase();
            if (target && target !== '_self') {
                return false;
            }

            let url;
            try {
                url = new URL(href, window.location.origin);
            } catch (_) {
                return false;
            }

            if (url.origin !== window.location.origin) {
                return false;
            }

            if (url.pathname.includes('/logout')) {
                return false;
            }

            return AJAX_PATH_PREFIXES.some((prefix) => url.pathname.startsWith(prefix));
        },

        async loadPage(url, clickedLink, pushHistory) {
            if (this.isLoading) {
                return;
            }

            const targetUrl = new URL(url, window.location.origin).href;
            if (targetUrl === this.currentUrl) {
                return;
            }

            this.isLoading = true;
            this.showLoading();
            this.closeSidebarOnMobile();
            if (clickedLink) {
                this.setActiveLink(clickedLink);
            }

            try {
                const response = await fetch(targetUrl, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const html = await response.text();
                const parsedDocument = new DOMParser().parseFromString(html, 'text/html');
                const nextContent = parsedDocument.getElementById('admin-content-container');

                if (!nextContent || !this.contentContainer) {
                    window.location.assign(targetUrl);
                    return;
                }

                this.contentContainer.innerHTML = nextContent.innerHTML;
                this.contentContainer.scrollTop = 0;

                const nextTitle = parsedDocument.querySelector('title');
                if (nextTitle) {
                    document.title = nextTitle.textContent;
                }

                await this.executeScriptsIn(this.contentContainer);

                this.currentUrl = targetUrl;
                if (pushHistory) {
                    window.history.pushState({ url: targetUrl }, '', targetUrl);
                }

                this.syncActiveLinks(targetUrl);
            } catch (error) {
                console.error('AJAX navigation failed:', error);
                window.location.assign(targetUrl);
            } finally {
                this.isLoading = false;
                this.hideLoading();
            }
        },

        async executeScriptsIn(rootElement) {
            const scripts = Array.from(rootElement.querySelectorAll('script'));
            for (const script of scripts) {
                await this.executeScript(script);
            }
        },

        executeScript(oldScript) {
            return new Promise((resolve, reject) => {
                const newScript = document.createElement('script');

                for (const attribute of oldScript.attributes) {
                    newScript.setAttribute(attribute.name, attribute.value);
                }

                if (oldScript.src) {
                    let absoluteSrc;
                    try {
                        absoluteSrc = new URL(oldScript.getAttribute('src'), window.location.origin).href;
                    } catch (_) {
                        oldScript.remove();
                        resolve();
                        return;
                    }

                    if (this.loadedExternalScripts.has(absoluteSrc)) {
                        oldScript.remove();
                        resolve();
                        return;
                    }

                    newScript.src = absoluteSrc;
                    newScript.onload = () => {
                        this.loadedExternalScripts.add(absoluteSrc);
                        oldScript.remove();
                        resolve();
                    };
                    newScript.onerror = () => {
                        oldScript.remove();
                        reject(new Error(`Failed to load script: ${absoluteSrc}`));
                    };

                    document.body.appendChild(newScript);
                    return;
                }

                newScript.text = oldScript.textContent || '';
                document.body.appendChild(newScript);
                newScript.remove();
                oldScript.remove();
                resolve();
            });
        },

        handlePopState(event) {
            if (event.state && event.state.url) {
                this.loadPage(event.state.url, null, false);
                return;
            }

            this.currentUrl = window.location.href;
            this.syncActiveLinks(this.currentUrl);
        },

        setActiveLink(link) {
            if (!link) {
                return;
            }

            document.querySelectorAll('.sidebar-menu a, .admin-nav a').forEach((anchor) => {
                anchor.classList.remove('active');
            });
            link.classList.add('active');
        },

        syncActiveLinks(url) {
            let parsedUrl;
            try {
                parsedUrl = new URL(url, window.location.origin);
            } catch (_) {
                return;
            }

            document.querySelectorAll('.sidebar-menu a, .admin-nav a').forEach((anchor) => {
                try {
                    const anchorUrl = new URL(anchor.getAttribute('href'), window.location.origin);
                    const isActive = anchorUrl.pathname === parsedUrl.pathname;
                    anchor.classList.toggle('active', isActive);
                } catch (_) {
                    anchor.classList.remove('active');
                }
            });
        },

        showLoading() {
            if (!this.contentContainer) {
                return;
            }

            this.contentContainer.style.opacity = '0.55';
            this.contentContainer.style.pointerEvents = 'none';
        },

        hideLoading() {
            if (!this.contentContainer) {
                return;
            }

            this.contentContainer.style.opacity = '1';
            this.contentContainer.style.pointerEvents = 'auto';
        },
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => APP_UI.init());
    } else {
        APP_UI.init();
    }

    window.ADMIN_AJAX = APP_UI;
})();
