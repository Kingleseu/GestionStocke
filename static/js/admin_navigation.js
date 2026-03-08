/**
 * Admin Navigation AJAX System - SIMPLIFIÉ ET OPTIMISÉ
 * Navigation fluide sans rechargement pour l'admin store
 */

(function() {
    'use strict';

    const ADMIN_AJAX = {
        // Configuration
        container: null,
        isLoading: false,
        currentUrl: window.location.href,

        // Initialisation
        init() {
            this.container = document.getElementById('admin-content-container');
            
            // Si pas de container, AJAX disabled
            if (!this.container) {
                return;
            }

            // Configurer les liens AJAX
            this.setupLinks();
            
            // Gérer le bouton retour/avant
            window.addEventListener('popstate', (e) => this.handlePopState(e));
        },

        // Setup les écouteurs de clics sur les liens admin
        setupLinks() {
            // Tous les liens /store/admin/
            document.addEventListener('click', (e) => {
                const link = e.target.closest('a');
                if (!link) return;

                const href = link.getAttribute('href');
                
                // Conditions pour charger en AJAX:
                // 1. URL contient /store/admin/
                // 2. Pas de target="_blank"
                // 3. Pas de data-no-ajax
                if (href && 
                    href.includes('/store/admin/') && 
                    link.getAttribute('target') !== '_blank' &&
                    !link.hasAttribute('data-no-ajax')) {
                    
                    e.preventDefault();
                    e.stopPropagation();
                    this.loadPage(href, link);
                }
            });
        },

        // Charger la page en AJAX
        loadPage(url, linkElement) {
            if (this.isLoading) return;

            this.isLoading = true;
            this.showLoading();
            this.setActiveLink(linkElement);

            // Fermer le sidebar en mobile
            const sidebar = document.getElementById('sidebar');
            if (window.innerWidth < 992 && sidebar && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
            }

            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.text())
            .then(html => {
                this.updateContent(html);
                window.history.pushState({url}, '', url);
                this.currentUrl = url;
            })
            .catch(err => {
                console.error('Erreur AJAX:', err);
                window.location.href = url; // Fallback
            })
            .finally(() => {
                this.isLoading = false;
                this.hideLoading();
            });
        },

        // Remplacer le contenu
        updateContent(html) {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Récupérer le contenu (chercher dans plusieurs endroits)
            const content = doc.querySelector('.main-content') ||
                          doc.querySelector('#admin-content-container') ||
                          doc.querySelector('[role="main"]');

            if (content && this.container) {
                // Fade out
                this.container.style.opacity = '0';
                
                setTimeout(() => {
                    this.container.innerHTML = content.innerHTML;
                    this.container.style.opacity = '1';
                    this.container.scrollTop = 0;
                    
                    // Réappliquer les écouteurs si besoin
                    if (typeof Turbo !== 'undefined') {
                        Turbo.visit(this.currentUrl);
                    }
                }, 150);
            }

            // Mettre à jour le titre
            const newTitle = doc.querySelector('title');
            if (newTitle) {
                document.title = newTitle.textContent;
            }
        },

        // Gérer le popstate (bouton retour)
        handlePopState(e) {
            if (e.state && e.state.url) {
                fetch(e.state.url)
                    .then(r => r.text())
                    .then(html => this.updateContent(html))
                    .catch(_ => window.location.reload());
            }
        },

        // UI helpers
        setActiveLink(link) {
            if (!link) return;
            document.querySelectorAll('.sidebar-menu a, .admin-nav a').forEach(a => {
                a.classList.remove('active');
            });
            link.classList.add('active');
        },

        showLoading() {
            if (this.container) {
                this.container.style.opacity = '0.5';
                this.container.style.pointerEvents = 'none';
            }
        },

        hideLoading() {
            if (this.container) {
                this.container.style.opacity = '1';
                this.container.style.pointerEvents = 'auto';
            }
        }
    };

    // Démarrer quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ADMIN_AJAX.init());
    } else {
        ADMIN_AJAX.init();
    }

    // Expose globally si besoin
    window.ADMIN_AJAX = ADMIN_AJAX;
})();
