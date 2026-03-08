/**
 * Admin Navigation AJAX System
 * Permet la navigation entre les onglets sans rechargement de page
 */

class AdminNavigation {
    constructor() {
        this.contentContainer = document.getElementById('admin-content-container');
        this.currentUrl = window.location.href;
        this.isLoading = false;
        this.init();
    }

    init() {
        if (!this.contentContainer) {
            console.warn('Admin content container not found');
            return;
        }

        // Détecter et récupérer le contenu initial
        this.setupAjaxLinks();
        this.handlePopState();
    }

    setupAjaxLinks() {
        // Sélectionner tous les liens du store admin qui doivent charger en AJAX
        const adminLinks = document.querySelectorAll(
            'a[href*="/store/admin/"], .admin-nav a, .sidebar-menu a[href*="/admin/"]'
        );

        adminLinks.forEach(link => {
            // Ignorer les liens vers l'extérieur (target="_blank")
            if (link.getAttribute('target') === '_blank') {
                return;
            }

            // Ignorer si le lien a déjà un listener AJAX
            if (link.dataset.ajaxBound === 'true') {
                return;
            }

            link.dataset.ajaxBound = 'true';

            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                
                // Si c'est une URL admin interne, charger en AJAX
                if (href && (href.includes('/store/admin/') || href.includes('/admin/')) && !href.includes('delete')) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.loadContent(href, link);
                }
            });
        });
    }

    loadContent(url, clickedElement) {
        if (this.isLoading) {
            console.warn('Chargement en cours, veuillez attendre');
            return;
        }

        this.isLoading = true;
        this.showLoadingState();
        this.removeActiveStates();
        this.setActive(clickedElement);

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'text/html'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Erreur réseau: ' + response.status);
            return response.text();
        })
        .then(html => {
            this.updateContent(html, url);
            window.history.pushState({ url }, document.title, url);
            this.currentUrl = url;
        })
        .catch(error => {
            console.error('Erreur lors du chargement:', error);
            this.showError('Erreur lors du chargement du contenu');
            // Fallback: charger normalement
            window.location.href = url;
        })
        .finally(() => {
            this.isLoading = false;
            this.hideLoadingState();
        });
    }

    updateContent(html, url) {
        // Parser le HTML pour extraire le contenu principal
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Chercher le contenu principal
        const mainContent = doc.querySelector('.main-content') || 
                           doc.querySelector('[role="main"]') ||
                           doc.querySelector('body');

        if (mainContent && this.contentContainer) {
            // Animation fade out
            this.contentContainer.style.opacity = '0';
            
            setTimeout(() => {
                this.contentContainer.innerHTML = mainContent.innerHTML;
                this.contentContainer.style.opacity = '1';
                
                // Réinitialiser les écouteurs pour les nouveaux liens
                this.setupAjaxLinks();
                
                // Scroller vers le haut
                this.contentContainer.scrollTop = 0;
                
                // Exécuter les scripts inline si présents
                this.executeScripts(mainContent);
            }, 150);
        }

        // Mettre à jour le titre
        const titleTag = doc.querySelector('title');
        if (titleTag) {
            document.title = titleTag.textContent;
        }
    }

    executeScripts(element) {
        const scripts = element.querySelectorAll('script');
        scripts.forEach(script => {
            if (script.textContent) {
                try {
                    // eslint-disable-next-line no-eval
                    eval(script.textContent);
                } catch (e) {
                    console.warn('Script execution error:', e);
                }
            }
        });
    }

    removeActiveStates() {
        document.querySelectorAll('.sidebar-menu a, .admin-nav a').forEach(link => {
            link.classList.remove('active');
        });
    }

    setActive(element) {
        if (element) {
            element.classList.add('active');
        }
    }

    showLoadingState() {
        if (this.contentContainer) {
            this.contentContainer.style.opacity = '0.5';
            this.contentContainer.style.pointerEvents = 'none';
        }
    }

    hideLoadingState() {
        if (this.contentContainer) {
            this.contentContainer.style.opacity = '1';
            this.contentContainer.style.pointerEvents = 'auto';
        }
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        if (this.contentContainer) {
            this.contentContainer.insertBefore(alert, this.contentContainer.firstChild);
        }
    }

    handlePopState() {
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.url) {
                // Recharger le contenu sans l'ajouter à l'historique
                fetch(event.state.url, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'text/html'
                    }
                })
                .then(response => response.text())
                .then(html => {
                    this.updateContent(html, event.state.url);
                })
                .catch(error => {
                    console.error('Erreur navigation:', error);
                    window.location.href = event.state.url;
                });
            }
        });
    }
}

// Initialiser au chargement du document
document.addEventListener('DOMContentLoaded', () => {
    new AdminNavigation();
});
