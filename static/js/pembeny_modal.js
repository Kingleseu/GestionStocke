(function (window, document) {
    'use strict';

    function getElements() {
        return {
            overlay: document.getElementById('pbModalOverlay'),
            modal: document.querySelector('#pbModalOverlay .pb-modal'),
            title: document.getElementById('pbModalTitle'),
            body: document.getElementById('pbModalBody'),
            footer: document.getElementById('pbModalFooter'),
            submit: document.getElementById('pbModalSubmit'),
            submitText: document.getElementById('pbModalSubmitText'),
        };
    }

    function getCookie(name) {
        const value = document.cookie
            .split('; ')
            .find((row) => row.startsWith(name + '='));
        return value ? decodeURIComponent(value.split('=')[1]) : '';
    }

    function getCSRFToken(form) {
        const input = form ? form.querySelector('input[name="csrfmiddlewaretoken"]') : null;
        if (input) {
            return input.value;
        }
        return getCookie('csrftoken');
    }

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function notify(type, message) {
        let container = document.getElementById('pbToastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'pbToastContainer';
            container.className = 'pb-toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = 'pb-toast pb-toast-' + type;
        toast.textContent = message;
        container.appendChild(toast);

        window.setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(18px)';
            window.setTimeout(() => toast.remove(), 200);
        }, 2600);
    }

    function setLoading(elements) {
        elements.footer.hidden = true;
        elements.body.innerHTML = [
            '<div class="pb-modal-loader">',
            '<div class="pb-spinner"></div>',
            '<p>Chargement...</p>',
            '</div>',
        ].join('');
    }

    function setError(elements, message) {
        elements.footer.hidden = true;
        elements.body.innerHTML = [
            '<div class="pb-modal-error">',
            '<i class="bi bi-exclamation-triangle"></i>',
            '<p>' + escapeHtml(message) + '</p>',
            '<button type="button" class="pb-secondary pb-link-button" data-modal-close>Fermer</button>',
            '</div>',
        ].join('');
    }

    function decorateForm(form) {
        form.querySelectorAll('input:not([type="checkbox"]):not([type="radio"]):not([type="file"]), select, textarea')
            .forEach((field) => field.classList.add('pb-input'));
        form.querySelectorAll('input[type="checkbox"]').forEach((field) => field.classList.add('pb-checkbox'));
        form.querySelectorAll('input[type="file"]').forEach((field) => field.classList.add('pb-file-input'));
    }

    function bindForm(elements, url, options) {
        const form = elements.body.querySelector('form');
        if (!form) {
            elements.footer.hidden = true;
            return;
        }

        decorateForm(form);
        elements.footer.hidden = false;

        const submitHandler = function (event) {
            event.preventDefault();
            submitForm(elements, form, url, options);
        };

        form.addEventListener('submit', submitHandler);
        elements.submit.onclick = function () {
            if (form.requestSubmit) {
                form.requestSubmit();
            } else {
                form.dispatchEvent(new Event('submit', { cancelable: true }));
            }
        };
    }

    async function loadForm(url, options) {
        const elements = getElements();
        if (!elements.overlay || !elements.body) {
            return;
        }

        setLoading(elements);

        try {
            const response = await fetch(url, {
                headers: {
                    'Accept': 'text/html',
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                throw new Error('Impossible de charger le formulaire.');
            }

            elements.body.innerHTML = await response.text();
            bindForm(elements, url, options);
        } catch (error) {
            setError(elements, error.message);
        }
    }

    async function submitForm(elements, form, fallbackUrl, options) {
        const submitInitialHtml = elements.submit.innerHTML;
        const actionUrl = form.getAttribute('action') || fallbackUrl;
        elements.submit.disabled = true;
        elements.submit.innerHTML = '<span class="pb-spinner-sm"></span>Enregistrement...';

        try {
            const response = await fetch(actionUrl, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken(form),
                },
            });

            const contentType = response.headers.get('content-type') || '';
            const payload = contentType.includes('application/json')
                ? await response.json()
                : { success: response.ok, html: await response.text() };

            if (response.ok && payload.success) {
                notify('success', options.successMessage || 'Enregistrement effectue.');
                close();
                if (typeof options.onSave === 'function') {
                    options.onSave(payload);
                    return;
                }
                window.setTimeout(() => window.location.reload(), 250);
                return;
            }

            if (payload.html) {
                elements.body.innerHTML = payload.html;
                bindForm(elements, actionUrl, options);
                return;
            }

            notify('error', payload.error || 'Le formulaire contient une erreur.');
        } catch (error) {
            notify('error', error.message || 'Erreur reseau.');
        } finally {
            elements.submit.disabled = false;
            elements.submit.innerHTML = submitInitialHtml;
        }
    }

    function open(title, url, options) {
        const elements = getElements();
        if (!elements.overlay || !elements.modal || !url) {
            return;
        }

        const modalOptions = Object.assign({
            submitText: 'Enregistrer',
            width: '',
            successMessage: 'Enregistrement effectue.',
        }, options || {});

        elements.title.textContent = title || 'Formulaire';
        elements.submitText.textContent = modalOptions.submitText;
        elements.modal.style.width = modalOptions.width ? 'min(94vw, ' + modalOptions.width + ')' : '';
        elements.overlay.classList.add('is-open');
        document.body.style.overflow = 'hidden';
        loadForm(url, modalOptions);
    }

    function close() {
        const elements = getElements();
        if (!elements.overlay) {
            return;
        }
        elements.overlay.classList.remove('is-open');
        document.body.style.overflow = '';
        window.setTimeout(() => {
            const nextElements = getElements();
            if (nextElements.body && !nextElements.overlay.classList.contains('is-open')) {
                nextElements.body.innerHTML = '';
                nextElements.footer.hidden = true;
            }
        }, 180);
    }

    document.addEventListener('click', function (event) {
        const closeTarget = event.target.closest('[data-modal-close], .pb-modal-close');
        if (closeTarget) {
            event.preventDefault();
            close();
            return;
        }

        const elements = getElements();
        if (elements.overlay && event.target === elements.overlay) {
            close();
            return;
        }

        const trigger = event.target.closest('[data-modal]');
        if (!trigger) {
            return;
        }

        const url = trigger.dataset.url || trigger.getAttribute('href');
        if (!url) {
            return;
        }

        event.preventDefault();
        open(trigger.dataset.title || trigger.textContent.trim() || 'Formulaire', url, {
            submitText: trigger.dataset.submit || 'Enregistrer',
            width: trigger.dataset.width || '',
            successMessage: trigger.dataset.success || 'Enregistrement effectue.',
        });
    });

    document.addEventListener('keydown', function (event) {
        const elements = getElements();
        if (event.key === 'Escape' && elements.overlay && elements.overlay.classList.contains('is-open')) {
            close();
        }
    });

    window.pbModal = {
        open,
        close,
    };
})(window, document);
