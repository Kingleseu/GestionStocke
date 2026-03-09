/**
 * Open product update pages inside a modal iframe.
 * Links must use: data-edit-product-modal
 */
(function () {
    'use strict';

    let modalInstance = null;
    let currentEditUrl = null;
    let openingInProgress = false;
    let frameLoadTimer = null;

    function getElements() {
        return {
            modalEl: document.getElementById('productEditModal'),
            modalTitle: document.getElementById('productEditModalTitle'),
            frame: document.getElementById('productEditFrame'),
            loading: document.getElementById('productEditLoading'),
        };
    }

    function showLoading(loadingEl, frameEl) {
        if (loadingEl) loadingEl.classList.remove('d-none');
        if (frameEl) frameEl.classList.add('d-none');
    }

    function showFrame(loadingEl, frameEl) {
        if (loadingEl) loadingEl.classList.add('d-none');
        if (frameEl) frameEl.classList.remove('d-none');
    }

    function showLoadError(loadingEl, url) {
        if (!loadingEl) {
            return;
        }
        loadingEl.classList.remove('d-none');
        loadingEl.innerHTML = `
            <div class="text-center p-4">
                <div class="text-danger fw-bold mb-2">Impossible de charger le formulaire.</div>
                <div class="small text-muted mb-3">Cliquez ci-dessous pour ouvrir l'édition directement.</div>
                <a class="btn btn-outline-primary btn-sm" href="${url}" data-no-ajax>
                    Ouvrir la page d'édition
                </a>
            </div>
        `;
    }

    function isEditPath(pathname) {
        return /^\/products\/\d+\/edit\/?$/.test(pathname);
    }

    function openProductEditModal(url, title) {
        const { modalEl, modalTitle, frame, loading } = getElements();
        if (!modalEl || !frame || !loading || openingInProgress) {
            return;
        }

        openingInProgress = true;
        currentEditUrl = url;
        if (modalTitle) {
            modalTitle.textContent = title || 'Modifier le produit';
        }

        showLoading(loading, frame);
        frame.src = currentEditUrl;
        if (frameLoadTimer) {
            clearTimeout(frameLoadTimer);
        }
        frameLoadTimer = setTimeout(() => {
            showLoadError(loading, currentEditUrl);
        }, 10000);

        modalInstance = modalInstance || new bootstrap.Modal(modalEl);
        modalInstance.show();
        openingInProgress = false;
    }

    function handleFrameLoad() {
        const { frame, loading, modalEl } = getElements();
        if (!frame || !loading) {
            return;
        }

        if (frameLoadTimer) {
            clearTimeout(frameLoadTimer);
            frameLoadTimer = null;
        }

        showFrame(loading, frame);

        let frameUrl;
        try {
            frameUrl = new URL(frame.contentWindow.location.href);
        } catch (_) {
            return;
        }

        if (currentEditUrl && !isEditPath(frameUrl.pathname) && frameUrl.pathname.startsWith('/products/')) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) {
                modal.hide();
            }
            window.location.reload();
        }
    }

    function init() {
        const { modalEl, frame, loading } = getElements();
        if (!modalEl || !frame || !loading) {
            return;
        }

        document.addEventListener('click', function (event) {
            const link = event.target.closest('a[data-edit-product-modal]');
            if (!link) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();

            const href = link.getAttribute('href');
            if (!href) {
                return;
            }

            const productName = link.getAttribute('data-product-name');
            const title = productName ? `Modifier : ${productName}` : 'Modifier le produit';
            openProductEditModal(href, title);
        });

        frame.addEventListener('load', handleFrameLoad);

        modalEl.addEventListener('hidden.bs.modal', function () {
            currentEditUrl = null;
            if (frameLoadTimer) {
                clearTimeout(frameLoadTimer);
                frameLoadTimer = null;
            }
            frame.src = 'about:blank';
            loading.innerHTML = `
                <div class="spinner-border text-primary me-2" role="status" aria-hidden="true"></div>
                <span class="text-muted">Chargement du formulaire...</span>
            `;
            showLoading(loading, frame);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
