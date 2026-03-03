// Data - Injected from Django
const products = window.djangoProducts || [];
let adminSettings = window.storeSettings || {
    deliveryPrice: 5.99,
    freeShippingThreshold: 100000,
    taxRate: 0.2,
    bannerText: '🎁 Livraison gratuite dès 100 000 FC d\'achat',
    bannerActive: true,
};

// State
let cart = window.djangoCart || [];
let expandedCardId = null;
let currentView = 'home';
let currentSort = 'newest';

let filters = {
    category: 'Tous',
    material: 'Tous',
    priceRange: 'Tous',
    customizable: 'Tous',
};

let productCustomizations = {};

const DEFAULT_FONTS = [
    { name: 'Arial', family: 'sans-serif' },
    { name: 'Playfair Display', family: 'serif' },
    { name: 'Dancing Script', family: 'cursive' },
    { name: 'Courier New', family: 'monospace' },
    { name: 'Great Vibes', family: 'cursive' }
];

const DEFAULT_SYMBOLS = [
    { id: 'heart', label: 'Cœur', icon: '♥', path: 'M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z' },
    { id: 'star', label: 'Étoile', icon: '★', path: 'M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z' },
    { id: 'infinity', label: 'Infini', icon: '∞', path: 'M18.6 6.62c-1.44 0-2.8.56-3.77 1.58L12 11.66 9.17 8.2c-.97-1.02-2.33-1.58-3.77-1.58-2.97 0-5.4 2.42-5.4 5.38s2.43 5.38 5.4 5.38c1.44 0 2.8-.56 3.77-1.58L12 12.34l2.83 3.46c.97 1.02 2.33 1.58 3.77 1.58 2.97 0 5.4-2.42 5.4-5.38s-2.43-5.38-5.4-5.38z' },
    { id: 'moon', label: 'Lune', icon: '☽', path: 'M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z' },
    { id: 'sun', label: 'Soleil', icon: '☀', path: 'M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10z M1 12h2 M21 12h2 M12 1h2 M12 21h2 M4.22 4.22l1.42 1.42 M18.36 18.36l1.42 1.42 M18.36 4.22l-1.42 1.42 M4.22 18.36l-1.42 1.42' }
];


// Site content (hero, hero-grid, about) - editable from admin
const defaultSiteContent = {
    hero: {
        title: "L'elegance redefinie",
        subtitle: "Decouvrez notre nouvelle collection de bijoux artisanaux, concus pour sublimer chaque instant.",
        image: ""
    },
    heroGrid: [
        {
            title: "Bijoux uniques",
            subtitle: "Des pieces d'exception",
            image: "",
            category: "Bijoux"
        },
        {
            title: "Collection mariage",
            subtitle: "Pour le plus beau jour",
            image: "",
            category: "Mariage"
        }
    ],
    about: {
        title: "L'excellence depuis 1985",
        paragraph1: "Mkaribu est une maison de joaillerie francaise reconnue pour son savoir-faire et ses creations uniques.",
        paragraph2: "Notre engagement : offrir des bijoux d'exception, personnalisables selon vos envies, pour celebrer chaque moment precieux de votre vie.",
        stats: [
            { value: "38+", label: "Annees d'experience" },
            { value: "50K+", label: "Clients satisfaits" },
            { value: "100%", label: "Atelier local" }
        ],
        image: ""
    }
};

let siteContent = null;
let initialContentDefaults = null;
let saveContentTimeout;
let contentFormInitialized = false;

// Helper to update main page price display (SPA detail page)
function updateMainPagePrice(product) {
    const displayPrice = document.getElementById('displayPrice');
    if (displayPrice) {
        const total = calculateTotalPrice(product);
        displayPrice.innerText = total.toLocaleString();
    }
}

// Cart Persistence
let saveCartTimeout;
async function saveCart() {
    clearTimeout(saveCartTimeout);
    saveCartTimeout = setTimeout(async () => {
        if (!window.urls || !window.urls.syncCart) return;
        try {
            await fetch(window.urls.syncCart, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                },
                body: JSON.stringify({ cart: cart })
            });
        } catch (e) {
            console.error("Cart sync failed", e);
        }
    }, 500);
}

// Toggle Cart Drawer
function toggleCart() {
    const cartDrawer = document.getElementById('cartDrawer');
    if (cartDrawer) {
        cartDrawer.classList.toggle('open');
        document.body.classList.toggle('cart-open');
    }
}

// Update Cart UI
function updateCartUI() {
    const cartBadge = document.getElementById('cartBadge');
    const cartCount = document.getElementById('cartCount');
    const cartItems = document.getElementById('cartItems');
    const cartSubtotal = document.getElementById('cartSubtotal');
    const cartTotal = document.getElementById('cartTotal');

    const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
    const subtotal = cart.reduce((sum, item) => {
        const price = item.customization_price || item.price || 0;
        return sum + (price * (item.quantity || 1));
    }, 0);

    // Update badge
    if (cartBadge) cartBadge.textContent = totalItems;
    if (cartCount) cartCount.textContent = totalItems;

    // Update totals
    if (cartSubtotal) cartSubtotal.textContent = `${subtotal.toFixed(2)} FC`;
    if (cartTotal) cartTotal.textContent = `${subtotal.toFixed(2)} FC`;

    // Render cart items
    if (cartItems) {
        if (cart.length === 0) {
            cartItems.innerHTML = '<div style="text-align:center; padding:2rem; color:#999;">Votre panier est vide</div>';
        } else {
            cartItems.innerHTML = cart.map((item, index) => {
                const price = item.customization_price || item.price || 0;
                const itemTotal = price * (item.quantity || 1);
                return `
                    <div class="cart-item" style="display:flex; gap:1rem; padding:1rem; border-bottom:1px solid #eee;">
                        <img src="${item.image || '/static/img/placeholder.png'}" alt="${item.name}" style="width:80px; height:80px; object-fit:cover; border-radius:8px;">
                        <div style="flex:1;">
                            <h4 style="margin:0 0 0.5rem; font-size:14px;">${item.name}</h4>
                            <p style="margin:0; font-size:12px; color:#666;">Quantité: ${item.quantity || 1}</p>
                            <p style="margin:0.25rem 0 0; font-weight:600;">${itemTotal.toFixed(2)} FC</p>
                        </div>
                        <button onclick="removeFromCart(${index})" style="background:none; border:none; cursor:pointer; color:#999;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                `;
            }).join('');
        }
    }
}

// Remove from cart
function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartUI();
    saveCart();
}

// Proceed to checkout
function proceedToCheckout() {
    if (cart.length === 0) {
        alert('Votre panier est vide');
        return;
    }
    if (window.urls && window.urls.checkout) {
        window.location.href = window.urls.checkout;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    const preloader = document.getElementById('premiumPreloader');

    // Robust Preloader Removal
    const removePreloader = () => {
        setTimeout(() => {
            if (preloader) {
                preloader.classList.add('fade-out');
                console.log("Preloader removed");
            }
            if (typeof initPremiumAnimations === 'function') initPremiumAnimations();
        }, 800);
    };

    if (document.readyState === 'complete') {
        removePreloader();
    } else {
        window.addEventListener('load', removePreloader);
    }

    // Initialize with Error Safety
    const initFunctions = [
        { name: 'initSiteContent', fn: initSiteContent },
        { name: 'renderFeaturedProducts', fn: renderFeaturedProducts },
        { name: 'renderCatalogueProducts', fn: renderCatalogueProducts },
        { name: 'renderProductsTable', fn: renderProductsTable },
        { name: 'renderTopProducts', fn: renderTopProducts },
        { name: 'updateCartUI', fn: updateCartUI }
    ];

    initFunctions.forEach(item => {
        try {
            if (typeof item.fn === 'function') {
                item.fn();
            }
        } catch (e) {
            console.error(`Error during ${item.name}:`, e);
        }
    });

    const checkoutView = document.getElementById('checkoutView');
    if (checkoutView && checkoutView.classList.contains('active')) {
        currentView = 'checkout';
        try {
            renderCheckoutSummary();
        } catch (e) {
            console.error('Error during renderCheckoutSummary:', e);
        }
        if (typeof initCheckoutStepper === 'function') initCheckoutStepper();
    }

    // Enhanced Scroll Logic for Header
    const header = document.getElementById('mainNav');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 40) {
            header?.classList.add('scrolled');
        } else {
            header?.classList.remove('scrolled');
        }
    });

    // Drag-to-Scroll Logic for Zag Collections
    const slider = document.querySelector('.zag-grid');
    if (slider) {
        let isDown = false;
        let startX;
        let scrollLeft;

        slider.addEventListener('mousedown', (e) => {
            isDown = true;
            slider.style.cursor = 'grabbing';
            startX = e.pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
            slider.style.scrollBehavior = 'auto'; // Disable smooth scroll for direct control
        });

        slider.addEventListener('mouseleave', () => {
            isDown = false;
            slider.style.cursor = 'grab';
        });

        slider.addEventListener('mouseup', () => {
            isDown = false;
            slider.style.cursor = 'grab';
            slider.style.scrollBehavior = 'smooth';
        });

        slider.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - slider.offsetLeft;
            const walk = (x - startX) * 1.5; // Scroll-fast multiplier
            slider.scrollLeft = scrollLeft - walk;
        });

        // --- Center Detection & Animation Logic ---
        const updateActiveCard = () => {
            const sliderRect = slider.getBoundingClientRect();
            const center = sliderRect.left + (sliderRect.width / 2);

            const cards = slider.querySelectorAll('.zag-card');
            let minDiff = Infinity;
            let activeCard = null;

            cards.forEach(card => {
                const cardRect = card.getBoundingClientRect();
                const cardCenter = cardRect.left + (cardRect.width / 2);
                const diff = Math.abs(center - cardCenter);

                if (diff < minDiff) {
                    minDiff = diff;
                    activeCard = card;
                }
            });

            cards.forEach(c => c.classList.remove('active'));
            if (activeCard) {
                activeCard.classList.add('active');
            }
        };

        // Robust Initial centering
        const centerSlider = () => {
            if (!slider) return;
            // Temporarily disable snap to force the scroll position
            slider.style.scrollSnapType = 'none';
            slider.scrollLeft = 0;

            // Restore snap and update active card after a brief paint cycle
            setTimeout(() => {
                slider.style.scrollSnapType = 'x mandatory';
                updateActiveCard();
            }, 50);
        };

        // Run on scroll
        slider.addEventListener('scroll', () => {
            if (!isDown) requestAnimationFrame(updateActiveCard);
        });

        // Also run on resize
        window.addEventListener('resize', () => {
            centerSlider();
            updateActiveCard();
        });

        // Initial run - progressive attempts for paint stability
        centerSlider();
        setTimeout(centerSlider, 100);
        setTimeout(centerSlider, 300);
        setTimeout(centerSlider, 1000);
        window.addEventListener('load', centerSlider);

        // --- Navigation Buttons Logic ---
        const prevBtn = document.querySelector('.zag-nav-btn.prev');
        const nextBtn = document.querySelector('.zag-nav-btn.next');

        if (prevBtn && nextBtn) {
            // Scroll by one full card (width + margin)
            // Card is 300px, margin is 30px on each side = 360px total
            const scrollDistance = 360;

            prevBtn.addEventListener('click', () => {
                slider.scrollBy({ left: -scrollDistance, behavior: 'smooth' });
                setTimeout(updateActiveCard, 500); // Check after scroll animation
            });

            nextBtn.addEventListener('click', () => {
                slider.scrollBy({ left: scrollDistance, behavior: 'smooth' });
                setTimeout(updateActiveCard, 500); // Check after scroll animation
            });
        }
    }

    // Click outside to close expanded cards
    document.addEventListener('click', function (e) {
        if (expandedCardId && !e.target.closest('.product-card')) {
            closeExpandedCard();
        }
    });
});

// Navigation Functions
function showView(view) {
    currentView = view;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const viewEl = document.getElementById(view + 'View');
    if (viewEl) viewEl.classList.add('active');
    window.scrollTo(0, 0);

    if (view === 'checkout') {
        renderCheckoutSummary();
        if (typeof initCheckoutStepper === 'function') initCheckoutStepper();
    }
}

function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('active');
}

// Product Rendering
function renderFeaturedProducts() {
    const container = document.getElementById('featuredProducts');
    if (!container) return;
    const featured = products.slice(0, 6);
    container.innerHTML = featured.map(product => createProductCard(product)).join('');
}

function renderCatalogueProducts() {
    const container = document.getElementById('catalogueProducts');
    const noResults = document.getElementById('noResults');
    if (!container) return;

    const filtered = filterProducts();
    const sorted = sortProducts(filtered);

    if (sorted.length === 0) {
        container.innerHTML = '';
        noResults.style.display = 'block';
    } else {
        noResults.style.display = 'none';
        container.innerHTML = sorted.map(product => createProductCard(product)).join('');
    }

    // Update counts
    const countEl = document.getElementById('productCount');
    if (countEl) countEl.textContent = `${products.length} produits`;

    const resultEl = document.getElementById('resultCount');
    if (resultEl) resultEl.textContent = `${sorted.length} résultat${sorted.length > 1 ? 's' : ''}`;

    updateCategoryUI();
}

function updateCategoryUI() {
    const currentCat = filters.category;

    // Desktop Tabs
    document.querySelectorAll('.tab-item').forEach(tab => {
        const catName = tab.getAttribute('data-category');
        if (catName === currentCat || (currentCat === 'Tous' && tab.textContent.trim() === 'TOUS')) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Mobile Pills
    document.querySelectorAll('.pill-item').forEach(pill => {
        const pillText = pill.textContent.trim();
        if (pillText === currentCat || (currentCat === 'Tous' && pillText === 'Tous')) {
            pill.classList.add('active');
        } else {
            pill.classList.remove('active');
        }
    });

    // Mobile sub-menu items (if any remain)
    document.querySelectorAll('.mobile-subcategories button').forEach(btn => {
        if (btn.textContent.trim() === currentCat) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}


// --- New Overlay Card Logic ---

// Product Detail Modal Logic
// Product Detail Sidebar Logic (Replaces old Modal)
// Product Detail Sidebar Logic (Replaces old Modal)
function openProductModal(productId) {
    // Force redirect to new Sidebar UI
    openSidebar(productId);
}

function closeProductModal() {
    closeSidebar();
}

function closeExpandedCard() {
    closeProductModal();
}

function renderSidebarControls(product) {
    const customization = productCustomizations[product.id];
    if (!customization) return '';

    // Reuse existing logic but wrap simply
    let html = '<div class="customization-form-sidebar">';

    if (customization.isStudio) {
        html += renderStudioSteps(product, customization);
    } else {
        html += renderGenericZones(product, customization);
    }

    // Common Quantity Control
    html += `
        <div class="form-field sidebar-qty" style="margin-top: 20px;">
            <label style="display: block; font-weight: 500; margin-bottom: 8px;">Quantité</label>
            <div class="quantity-controls" style="display: flex; align-items: center; border: 1px solid #e2e8f0; width: fit-content; border-radius: 4px;">
                <button class="qty-btn" onclick="updateQuantity('${product.id}', -1)" style="padding: 10px 15px; border-right: 1px solid #e2e8f0;">-</button>
                <input type="text" class="qty-input" value="${customization.quantity}" readonly style="width: 50px; text-align: center; border: none; font-weight: 600;">
                <button class="qty-btn" onclick="updateQuantity('${product.id}', 1)" style="padding: 10px 15px; border-left: 1px solid #e2e8f0;">+</button>
            </div>
        </div>
    `;

    // ADD TO CART BUTTON
    html += `
        <button class="add-to-cart-btn-sidebar" onclick="addToCart('${product.id}')" style="margin-top: 30px;">
            AJOUTER AU PANIER — ${calculateTotalPrice(product).toLocaleString()} FC
        </button>
    `;

    html += '</div>';
    return html;
}

// Use sidebar when available, otherwise fall back to product detail page
function openProductQuick(productId) {
    const sidebar = document.querySelector('.product-sidebar');
    const overlay = document.querySelector('.product-sidebar-overlay');
    if (sidebar && overlay && typeof openSidebar === 'function') {
        openSidebar(productId);
        return;
    }
    const detailUrl = window.urls && window.urls.productDetail
        ? window.urls.productDetail.replace('0', productId)
        : `/store/product/${productId}/`;
    window.location.href = detailUrl;
}

function createProductCard(product) {
    const priceValue = product.price || product.selling_price || 0;
    const categoryLabel = product.category || 'Collection';
    const isCustomizable = !!product.customizable;

    return `
        <div class="product-card" data-id="${product.id}" onclick="openProductQuick('${product.id}')">
            <div class="product-image-wrapper${product.secondary_image ? ' has-secondary' : ''}">
                <button class="wishlist-icon" type="button" onclick="event.stopPropagation(); this.classList.toggle('active');">
                    <i class="bi bi-heart"></i>
                </button>
                ${product.image
            ? `
                <img src="${product.image}" alt="${product.name}" class="product-image primary-img">
                ${product.secondary_image ? `<img src="${product.secondary_image}" alt="${product.name}" class="product-image secondary-img">` : ''}
              `
            : `<div class="product-image-placeholder"><i class="bi bi-image"></i></div>`}
                <button class="add-btn-overlay" type="button" onclick="event.stopPropagation(); ${isCustomizable
            ? `openProductQuick('${product.id}')`
            : `addToCart('${product.id}')`}">
                    Ajouter au panier
                </button>
            </div>
            <div class="product-info">
                <div class="product-category-label">${categoryLabel}</div>
                <h3 class="product-name">${product.name}</h3>
                <div class="product-price">${priceValue.toLocaleString()} FC</div>
            </div>
        </div>
    `;
}

function createProductCardContent(product, isExpanded) { return ''; } // Deprecated

function toggleFavorite(productId) {
    const btn = event.target.closest('.favorite-btn');
    btn.classList.toggle('liked');
}

function initCustomizationState(productId) {
    const product = products.find(p => String(p.id) === String(productId));
    if (!product) return;

    if (!productCustomizations[productId]) {
        productCustomizations[productId] = {
            choices: {},
            quantity: 1,
            extra_cost: 0,
            currentStep: 1,
            isStudio: !!(product.customization_rules?.is_studio)
        };
    }

    // Set defaults from rules if not already set (MERGE logic)
    if (product.customization_rules && product.customization_rules.zones) {
        product.customization_rules.zones.forEach(zone => {
            if (zone.type === 'selection' && zone.required) {
                if (!productCustomizations[productId].choices[zone.id]) {
                    productCustomizations[productId].choices[zone.id] = zone.options[0].value;
                }
            }
            if (zone.type === 'text') {
                if (!productCustomizations[productId].choices[zone.id]) {
                    productCustomizations[productId].choices[zone.id] = {
                        text: '',
                        font: zone.constraints?.allowed_fonts?.[0] || 'Arial'
                    };
                }
            }
        });
    }
}

function updateChoiceValue(productId, zoneId, subfield, value) {
    if (!productCustomizations[productId]) {
        initCustomizationState(productId);
    }

    if (subfield) {
        if (!productCustomizations[productId].choices[zoneId]) {
            productCustomizations[productId].choices[zoneId] = {};
        }
        productCustomizations[productId].choices[zoneId][subfield] = value;
    } else {
        productCustomizations[productId].choices[zoneId] = value;
    }

    updateOverlayContent(productId);
    // Use requestAnimationFrame for smoother preview updates
    requestAnimationFrame(() => renderLivePreview(productId));
}

function handleChoiceImageUpload(productId, zoneId, input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            updateChoiceValue(productId, zoneId, 'url', e.target.result);
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function updateQuantity(productId, delta) {
    const custom = productCustomizations[productId];
    const product = products.find(p => p.id === productId);
    if (!custom) return;

    custom.quantity = Math.max(1, Math.min(product.stock || 99, custom.quantity + delta));
    updateOverlayContent(productId);
}

function calculateTotalPrice(product) {
    if (!product) return 0;
    const basePrice = product.selling_price || product.price || 0;
    const custom = productCustomizations[product.id];
    if (!custom) return basePrice;

    let extra = 0;

    // Add product-specific engraving base price if customization is active
    // NOTE: For Studio products, this is usually handled by the 'studio_engraving' zone's price_formula.
    // We only add it here if it's NOT already accounted for in a zone.
    let hasEngravingZone = product.customization_rules?.zones?.some(z => z.type === 'text' && (z.price_formula?.base > 0));

    if (product.engraving_price && !hasEngravingZone) {
        // We consider engraving active if at least one side is active OR if the user has explicitly opened the customization sidebar
        const isCustomizing = custom.isCustomizing; // Flag to indicate user intent to customize
        if (custom.choices?.recto?.active || custom.choices?.verso?.active || custom.choices?.engraving?.active || isCustomizing) {
            extra += parseFloat(product.engraving_price) || 0;
        }
    }

    if (product.customization_rules) {
        product.customization_rules.zones.forEach(zone => {
            // Check condition
            const isVisible = !zone.conditions || Object.entries(zone.conditions).every(([k, v]) => custom.choices?.[k] === v);
            if (!isVisible) return;

            const val = custom.choices?.[zone.id];
            if (!val) return;

            if (zone.type === 'text') {
                const text = val.text || '';
                const formula = zone.price_formula || {};
                if (text.length > 0) {
                    extra += (formula.base || 0) + (text.length * (formula.per_char || 0));
                }
            } else if (zone.type === 'selection') {
                const opt = (zone.options || []).find(o => o.value === val);
                if (opt) extra += (opt.price_modifier || 0);
            } else if (zone.type === 'image') {
                if (val.url) extra += (zone.price_formula?.base || 0);
            }
        });
    }

    // Add extra cost from premium engraving if available (legacy/fallback)
    if (custom.extra_cost) extra += custom.extra_cost;

    return basePrice + extra;
}

function renderLivePreview(productId) {
    const product = products.find(p => p.id === productId);
    const canvas = document.getElementById(`canvas-${productId}`);
    if (!canvas || !product.customization_rules) return;

    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    const img = container.querySelector('.mockup-bg');

    // Ensure image is loaded before drawing
    if (!img.complete) {
        img.onload = () => renderLivePreview(productId);
        return;
    }

    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const custom = productCustomizations[productId];
    if (!custom) return;

    // Special Studio Mode: Draw component image first, then text on top
    if (custom.isStudio && custom.choices.studio_component) {
        const componentId = custom.choices.studio_component;
        const compZone = product.customization_rules.zones.find(z => z.id === 'studio_component');
        const compOption = compZone?.options.find(o => o.value === componentId);

        if (compOption && compOption.image_url) {
            // Load and draw the component image
            const componentImg = new Image();
            componentImg.onload = function () {
                // 1. Position and scale calculations
                const scale = Math.min(canvas.width / componentImg.width, canvas.height / componentImg.height) * 0.7;
                const w = componentImg.width * scale;
                const h = componentImg.height * scale;
                const x = (canvas.width - w) / 2;
                const y = (canvas.height - h) / 2;

                // 2. Clear and setup text rendering first (Below product)
                const engravingChoice = custom.choices.studio_engraving;
                if (engravingChoice && engravingChoice.text) {
                    const text = engravingChoice.text;
                    const font = engravingChoice.font || 'Arial';
                    const fontSize = Math.max(16, canvas.width / 20);

                    ctx.font = `${fontSize}px "${font}"`;
                    ctx.fillStyle = '#1a1a1a';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(text, canvas.width / 2, canvas.height / 2);
                }

                // 3. Draw component image ON TOP with multiply for realistic texture
                ctx.globalCompositeOperation = 'multiply';
                ctx.drawImage(componentImg, x, y, w, h);
                ctx.globalCompositeOperation = 'source-over'; // Reset
            };
            componentImg.src = compOption.image_url;
            return; // Exit early, the onload will handle the rest
        }
    }

    // Generic zones rendering (for non-studio products)
    // Note: These are drawn on top of the existing .mockup-bg in the DOM.
    // If we want a realistic look here too, we might need a similar approach 
    // but usually these are simpler overlays.
    product.customization_rules.zones.forEach(zone => {
        const isVisible = !zone.conditions || Object.entries(zone.conditions).every(([k, v]) => custom.choices?.[k] === v);
        if (!isVisible) return;

        const val = custom.choices?.[zone.id];
        if (!val) return;

        const config = zone.preview_config;
        if (!config) return;

        const x = (config.position.x * canvas.width) / 100;
        const y = (config.position.y * canvas.height) / 100;

        if (zone.type === 'text') {
            const text = val.text || '';
            if (!text) return;
            const font = val.font || 'Arial';
            const size = (config.size * canvas.width) / 500;

            ctx.font = `${size}px "${font}"`;
            ctx.fillStyle = config.color || '#1a1a1a';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(text, x, y);
        } else if (zone.type === 'selection' && (zone.id.includes('shape') || zone.id.includes('symbol'))) {
            const size = (config.size * canvas.width) / 200;
            const symbol = DEFAULT_SYMBOLS.find(s => s.id === val);

            ctx.save();
            ctx.translate(x, y);
            ctx.fillStyle = config.color || '#1a1a1a';

            if (symbol && symbol.path) {
                // Render SVG Path on Canvas
                const p = new Path2D(symbol.path);
                const scale = size / 24; // Original paths are usually 24x24
                ctx.scale(scale, scale);
                ctx.translate(-12, -12); // Center the path
                ctx.fill(p);
            } else {
                // Fallback to emoji/text
                ctx.font = `${size}px Arial`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                const opt = (zone.options || []).find(o => o.value === val);
                const displayText = opt ? opt.label.split(' ').pop() : val;
                ctx.fillText(displayText, 0, 0);
            }
            ctx.restore();
        } else if (zone.type === 'image' && val.url) {
            // Handle user-uploaded images
            const userImg = new Image();
            userImg.onload = function () {
                const size = (config.size * canvas.width) / 200;
                ctx.drawImage(userImg, x - size / 2, y - size / 2, size, size);
            };
            userImg.src = val.url;
        }
    });
}


function renderStudioSteps(product, customization) {
    const step = customization.currentStep || 1;
    const rules = product.customization_rules;
    const compZone = rules.zones.find(z => z.id === 'studio_component');
    const engravingZone = rules.zones.find(z => z.id === 'studio_engraving');

    return `
        <div class="studio-container">
            <!-- Step Navigation -->
            <div class="studio-nav">
                <div class="step-pill ${step === 1 ? 'active' : 'completed'}" onclick="setStudioStep('${product.id}', 1)">
                    <span class="step-num">1</span>
                    <span class="step-label">Modèle</span>
                </div>
                <div class="step-line"></div>
                <div class="step-pill ${step === 2 ? 'active' : ''}" onclick="${customization.choices.studio_component ? `setStudioStep('${product.id}', 2)` : ''}">
                    <span class="step-num">2</span>
                    <span class="step-label">Gravure</span>
                </div>
            </div>

            <div class="studio-steps-wrapper">
                <!-- Step 1: Component -->
                <div class="studio-step ${step === 1 ? 'active' : 'hidden-left'}">
                    <h5 class="studio-step-title">Sélectionnez votre bijou</h5>
                    <div class="selection-grid-premium">
                        ${compZone.options.map(opt => `
                            <button class="choice-card-premium ${customization.choices.studio_component === opt.value ? 'active' : ''}" 
                                    onclick="updateChoiceValue('${product.id}', 'studio_component', null, '${opt.value}'); setTimeout(() => setStudioStep('${product.id}', 2), 300)">
                                <div class="card-image">
                                    <img src="${opt.image_url}" alt="${opt.label}">
                                </div>
                                <div class="card-info">
                                    <span class="opt-label">${opt.label}</span>
                                    <span class="opt-price">+${opt.price_modifier.toLocaleString()} FC</span>
                                </div>
                                <div class="check-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                </div>
                            </button>
                        `).join('')}
                    </div>
                </div>

                <!-- Step 2: Engraving -->
                <div class="studio-step ${step === 2 ? 'active' : 'hidden-right'}">
                    <h5 class="studio-step-title">Personnalisez votre message</h5>
                    <div class="engraving-pane">
                        <div class="form-group-premium">
                            <label>Texte à graver</label>
                            <div class="input-glow-wrapper">
                                <input type="text" 
                                       class="premium-input"
                                       value="${customization.choices.studio_engraving?.text || ''}" 
                                       placeholder="Votre message ici..." 
                                       maxlength="${engravingZone.constraints?.max_length || 25}"
                                       oninput="updateChoiceValue('${product.id}', 'studio_engraving', 'text', this.value)">
                                <span class="char-counter">${(customization.choices.studio_engraving?.text || '').length} / ${engravingZone.constraints?.max_length || 15}</span>
                            </div>
                        </div>

                        <div class="form-group-premium">
                            <label>Style de police</label>
                            <div class="font-grid-premium">
                                ${engravingZone.constraints.allowed_fonts.map(fontName => `
                                    <button class="font-card ${customization.choices.studio_engraving?.font === fontName ? 'active' : ''}"
                                            onclick="updateChoiceValue('${product.id}', 'studio_engraving', 'font', '${fontName}')"
                                            style="font-family: '${fontName}'">
                                        ${fontName}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderGenericZones(product, customization) {
    if (!product.customization_rules) return '';
    return `
        <div class="generic-zones-wrapper">
            ${product.customization_rules.zones.map(zone => {
        const isVisible = !zone.conditions || Object.entries(zone.conditions).every(([k, v]) => customization.choices?.[k] === v);
        if (!isVisible) return '';

        return `
            <div class="form-field">
                <label>${zone.label} ${zone.required ? '*' : ''}</label>
                ${zone.type === 'text' ? `
                    <div class="text-input-group">
                        <input type="text" value="${customization.choices?.[zone.id]?.text || ''}" 
                               oninput="updateChoiceValue('${product.id}', '${zone.id}', 'text', this.value)">
                        <select onchange="updateChoiceValue('${product.id}', '${zone.id}', 'font', this.value)">
                            ${(zone.constraints?.allowed_fonts || []).map(f => `<option value="${f}" ${customization.choices?.[zone.id]?.font === f ? 'selected' : ''}>${f}</option>`).join('')}
                        </select>
                    </div>
                ` : ''}
                ${zone.type === 'selection' ? `
                    <div class="selection-grid">
                        ${zone.options.map(opt => `
                            <button class="choice-btn ${customization.choices?.[zone.id] === opt.value ? 'active' : ''}" 
                                    onclick="updateChoiceValue('${product.id}', '${zone.id}', null, '${opt.value}')">${opt.label}</button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('')}
        </div>
    `;
}

function setStudioStep(productId, step) {
    if (productCustomizations[productId]) {
        productCustomizations[productId].currentStep = step;
        updateOverlayContent(productId);
    }
}

function updateOverlayContent(productId) {
    const product = products.find(p => p.id === productId || String(p.id) === String(productId));
    const customization = productCustomizations[productId];
    if (!product || !customization) return;

    // Support both activeOverlayCard (Legacy/Sidebar) and productDetailModal (Premium)
    const overlay = document.getElementById('activeOverlayCard');
    const premiumModal = document.getElementById('productDetailModal');

    if (premiumModal && premiumModal.classList.contains('active')) {
        const priceEl = premiumModal.querySelector('.modal-product-price');
        if (priceEl) {
            priceEl.textContent = `${calculateTotalPrice(product).toLocaleString()} FC`;
        }

        const controls = premiumModal.querySelector('.customization-controls');
        if (controls) {
            controls.innerHTML = renderSidebarControls(product);
        }
    } else if (overlay) {
        // ... (existing legacy logic below)
        const controlsContainer = overlay.querySelector('.customization-controls');
        if (controlsContainer) {
            // ... (keep legacy logic for sidebar)
            const zoneContainer = controlsContainer.querySelector('.studio-container') || controlsContainer.querySelector('.generic-zones-container');
            if (zoneContainer) {
                const stepsWrapper = zoneContainer.querySelector('.studio-steps-wrapper');
                if (stepsWrapper) {
                    stepsWrapper.innerHTML = `
                        <div class="studio-step ${customization.currentStep === 1 ? 'active' : 'hidden-left'}">${renderStep1Html(product, customization)}</div>
                        <div class="studio-step ${customization.currentStep === 2 ? 'active' : 'hidden-right'}">${renderStep2Html(product, customization)}</div>
                    `;
                    const nav = zoneContainer.querySelector('.studio-nav');
                    if (nav) nav.innerHTML = renderStudioNavHtml(product, customization);
                } else {
                    controlsContainer.innerHTML = `${customization.isStudio ? renderStudioSteps(product, customization) : renderGenericZones(product, customization)}${renderCommonControls(product, customization)}`;
                }
            } else {
                controlsContainer.innerHTML = `${customization.isStudio ? renderStudioSteps(product, customization) : renderGenericZones(product, customization)}${renderCommonControls(product, customization)}`;
            }
        }
    }

    requestAnimationFrame(() => renderLivePreview(productId));
}

// Helper functions for surgical updates
function renderStep1Html(product, customization) {
    const rules = product.customization_rules;
    const compZone = rules.zones.find(z => z.id === 'studio_component');
    return `
        <h5 class="studio-step-title">Sélectionnez votre bijou</h5>
        <div class="selection-grid-premium">
            ${compZone.options.map(opt => `
                <button class="choice-card-premium ${customization.choices.studio_component === opt.value ? 'active' : ''}" 
                        onclick="updateChoiceValue('${product.id}', 'studio_component', null, '${opt.value}'); setTimeout(() => setStudioStep('${product.id}', 2), 300)">
                    <div class="card-image">
                        <img src="${opt.image_url}" alt="${opt.label}">
                    </div>
                    <div class="card-info">
                        <span class="opt-label">${opt.label}</span>
                        <span class="opt-price">+${opt.price_modifier.toLocaleString()} FC</span>
                    </div>
                    <div class="check-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </div>
                </button>
            `).join('')}
        </div>
    `;
}

function renderStep2Html(product, customization) {
    const rules = product.customization_rules;
    const engravingZone = rules.zones.find(z => z.id === 'studio_engraving');
    return `
        <h5 class="studio-step-title">Personnalisez votre message</h5>
        <div class="engraving-pane">
            <div class="form-group-premium">
                <label>Texte à graver</label>
                <div class="input-glow-wrapper">
                    <input type="text" 
                           class="premium-input"
                           value="${customization.choices.studio_engraving?.text || ''}" 
                           placeholder="Votre message ici..." 
                           maxlength="${engravingZone.constraints?.max_length || 25}"
                           oninput="updateChoiceValue('${product.id}', 'studio_engraving', 'text', this.value)">
                    <span class="char-counter">${(customization.choices.studio_engraving?.text || '').length} / ${engravingZone.constraints?.max_length || 15}</span>
                </div>
            </div>

            <div class="form-group-premium">
                <label>Style de police</label>
                <div class="font-grid-premium">
                    ${engravingZone.constraints.allowed_fonts.map(fontName => `
                        <button class="font-card ${customization.choices.studio_engraving?.font === fontName ? 'active' : ''}"
                                onclick="updateChoiceValue('${product.id}', 'studio_engraving', 'font', '${fontName}')"
                                style="font-family: '${fontName}'">
                            ${fontName}
                        </button>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

function renderStudioNavHtml(product, customization) {
    const step = customization.currentStep || 1;
    return `
        <div class="step-pill ${step === 1 ? 'active' : 'completed'}" onclick="setStudioStep('${product.id}', 1)">
            <span class="step-num">1</span>
            <span class="step-label">Modèle</span>
        </div>
        <div class="step-line"></div>
        <div class="step-pill ${step === 2 ? 'active' : ''}" onclick="${customization.choices.studio_component ? `setStudioStep('${product.id}', 2)` : ''}">
            <span class="step-num">2</span>
            <span class="step-label">Gravure</span>
        </div>
    `;
}

function renderCommonControls(product, customization) {
    return `
        <div class="form-field">
            <label>Quantité</label>
            <div class="quantity-controls">
                <button class="qty-btn" onclick="updateQuantity('${product.id}', -1)">−</button>
                <input type="number" class="qty-input" value="${customization.quantity}" 
                       min="1" max="${product.stock}" readonly>
                <button class="qty-btn" onclick="updateQuantity('${product.id}', 1)">+</button>
            </div>
        </div>

        ${product.customization_rules?.special_rules?.legal_notice ? `
            <p class="legal-notice">${product.customization_rules.special_rules.legal_notice}</p>
        ` : ''}

        <button class="add-to-cart-btn" 
                onclick="addToCart('${product.id}')">
            Ajouter au panier • ${calculateTotalPrice(product).toLocaleString()} FC
        </button>
    `;
}

// Cart Functions
// Helper aliases
function addToCartFromOverlay(productId) {
    addToCart(productId);
}

function addToCartQuick(btnElement) {
    if (!btnElement) return;
    // Attempt to find productId from the button context or parent
    // Usually passed as element, but we need ID.
    // However, the legacy call was addToCartQuick(document.querySelector...)
    // Let's assume we can get ID from the element passed if needed,
    // or we just rely on standard addToCart if ID is passed.
    // If the argument is an element, we need to extract ID.

    // But mostly we just want to ensure it works.
    // If the legacy HTML called it with an element, we might need to handle it.
    // But since we removed the legacy HTML in openProductModal, this might only be called 
    // from other legacy parts (if any).
    // Let's make it robust.
}

async function addToCart(productId) {
    console.log("Adding product to cart:", productId);
    const product = products.find(p => String(p.id) === String(productId));
    if (!product) {
        if (typeof productId === 'object' && productId.dataset && productId.dataset.id) {
            return addToCart(productId.dataset.id);
        }
        console.error("Product not found:", productId);
        return;
    }

    if (!productCustomizations[productId]) {
        initCustomizationState(productId);
    }

    const custom = productCustomizations[productId];

    // ALLOW ADDING WITHOUT ENGRAVING (User request)
    // We no longer block if customization is incomplete, unless it's strictly required by complex logic not yet defined.
    // For now, if they click add, we add what they have (even if empty).

    try {
        // 📸 CAPTURE THE COMPLETE PRODUCT PREVIEW (What the customer sees)
        let cartPreview = null;

        // PRIORITY 1: Capture the live preview box (medallion + chain + engraving)
        const previewBox = document.querySelector('.engraving-preview-box svg');
        if (previewBox) {
            try {
                console.log("📸 Capturing complete product preview from live SVG...");
                cartPreview = await captureSVGToDataURL(previewBox);
                console.log("✅ Complete product preview captured successfully");
            } catch (captureErr) {
                console.error("❌ Live preview capture failed:", captureErr);
            }
        }

        // PRIORITY 2: If live capture failed or sidebar not open, use headless compositor
        if (!cartPreview) {
            try {
                console.log("ℹ️ Trying headless compositor...");
                cartPreview = await generateHeadlessMockup(product, custom);
                console.log("✅ Headless mockup generated successfully");
            } catch (headlessErr) {
                console.warn("⚠️ Headless compositor also failed:", headlessErr);
            }
        }

        // PRIORITY 3: Final fallback to stored preview
        if (!cartPreview) {
            cartPreview = custom.choices?.recto?.image_preview || null;
            console.log("ℹ️ Using stored preview as final fallback");
        }

        const cartItem = {
            id: Date.now().toString(),
            productId: productId,
            name: product.name,
            price: calculateTotalPrice(product),
            basePrice: product.selling_price || product.price,
            extraCost: custom ? (custom.extra_cost || 0) : 0,
            image: product.image,
            quantity: custom ? custom.quantity : 1,
            customization: product.customizable ? {
                choices: JSON.parse(JSON.stringify(custom.choices)), // deep copy
                preview: cartPreview
            } : null
        };

        cart.push(cartItem);
        updateCartUI();
        saveCart();

        if (expandedCardId === productId) {
            closeExpandedCard();
        }
        closeSidebar();

        // RESET FORM AFTER ADDING TO CART
        clearCustomizationForm(productId);

        // RE-INIT STATE (Empty)
        initCustomizationState(productId);

    } catch (error) {
        console.error("Error adding to cart:", error);
    }
}

function clearCustomizationForm(productId) {
    // Reset inputs
    const inputs = document.querySelectorAll(`input[data-product-id="${productId}"], textarea[data-product-id="${productId}"]`);
    inputs.forEach(input => input.value = '');

    // Reset file inputs
    const fileInputs = document.querySelectorAll(`input[type="file"]`);
    fileInputs.forEach(input => input.value = '');

    console.log("🧹 Customization form cleared for product", productId);
}

function isCustomizationComplete(product) {
    if (!product.customizable || !product.customization_rules) return true;
    const custom = productCustomizations[product.id];
    if (!custom) return false;

    const engravingMode = product.engraving_mode || custom.choices.engraving_mode || 'text';
    if (engravingMode === 'text' || engravingMode === 'image' || engravingMode === 'both') {
        const checkSide = (side) => {
            const choice = custom.choices[side];
            if (!choice || !choice.active) return true;
            const hasText = !!(choice.text && choice.text.trim());
            const hasImage = !!choice.image_data;
            if (engravingMode === 'text') return hasText;
            if (engravingMode === 'image') return hasImage;
            return hasText && hasImage;
        };
        if (!checkSide('recto')) return false;
        if (!checkSide('verso')) return false;
    }

    return product.customization_rules.zones.every(zone => {
        if (!zone.required) return true;
        const isVisible = !zone.conditions || Object.entries(zone.conditions).every(([k, v]) => custom.choices?.[k] === v);
        if (!isVisible) return true;
        const val = custom.choices?.[zone.id];
        if (!val) return false;
        if (zone.type === 'text') return val.text && val.text.trim().length > 0;
        if (zone.type === 'image') return val.url;
        return true;
    });
}

function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    updateCartUI();
    saveCart();
}

function updateCartQuantity(itemId, delta) {
    const item = cart.find(i => i.id === itemId);
    if (!item) return;

    const newQty = item.quantity + delta;
    if (newQty <= 0) {
        removeFromCart(itemId);
    } else {
        item.quantity = newQty;
        updateCartUI();
        saveCart();
    }
}

function updateCartUI() {
    const itemCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    const badge = document.getElementById('cartBadge');
    const count = document.getElementById('cartCount');
    if (badge) badge.textContent = itemCount;
    if (count) count.textContent = itemCount;

    const cartItems = document.getElementById('cartItems');
    const cartFooter = document.getElementById('cartFooter');

    if (!cartItems || !cartFooter) return;

    if (cart.length === 0) {
        cartItems.innerHTML = `
            <div class="cart-empty">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <path d="M16 10a4 4 0 0 1-8 0"></path>
                </svg>
                <p>Votre panier est vide</p>
                <p class="cart-empty-subtitle">Ajoutez des produits pour commencer</p>
            </div>
        `;
        cartFooter.style.display = 'none';
    } else {
        cartItems.innerHTML = cart.map(item => `
            <div class="cart-item">
                <img src="${item.image}" alt="${item.name}" class="cart-item-image">
                <div class="cart-item-info">
                    <div class="cart-item-header">
                        <h3 class="cart-item-name">${item.name}</h3>
                        <button class="remove-item-btn" onclick="removeFromCart('${item.id}')">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </div>
                        ${(item.customization && item.customization.choices) ? `
                        <div class="cart-item-customization">
                            ${item.customization.preview ? `
                                <div style="margin-bottom:8px;">
                                    <img src="${item.customization.preview}" style="width:100px;height:auto;border-radius:8px;border:1px solid #eee;">
                                </div>` : ''}
                            
                            ${(() => {
                    const choices = item.customization.choices || {};
                    let detailsHtml = '';

                    // Gravure Premium (Recto/Verso)
                    if (choices.recto && choices.recto.active && choices.recto.text) {
                        detailsHtml += `
                                        <div class="custom-detail-line">
                                            <span class="detail-label">Recto :</span>
                                            <span class="detail-value">"${choices.recto.text}"</span>
                                        </div>
                                    `;
                    }
                    if (choices.verso && choices.verso.active && choices.verso.text) {
                        detailsHtml += `
                                        <div class="custom-detail-line">
                                            <span class="detail-label">Verso :</span>
                                            <span class="detail-value">"${choices.verso.text}"</span>
                                        </div>
                                    `;
                    }

                    // Legacy Gravure support
                    if (choices.studio_engraving && choices.studio_engraving.text && !choices.recto) {
                        detailsHtml += `
                                        <div class="custom-detail-line">
                                            <span class="detail-label">Gravure :</span>
                                            <span class="detail-value">"${choices.studio_engraving.text}"</span>
                                        </div>
                                    `;
                    }

                    // Modèle / Forme
                    const modelName = choices.studio_component_label || choices.studio_component;
                    if (modelName) {
                        detailsHtml += `
                                        <div class="custom-detail-line">
                                            <span class="detail-label">Modèle :</span>
                                            <span class="detail-value">${modelName}</span>
                                        </div>
                                    `;
                    }

                    return detailsHtml;
                })()}
                            
                            <button class="btn-edit-custom-cart" onclick="editCustomization('${item.id}')">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-1">
                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                </svg>
                                Modifier
                            </button>
                        </div>
                        ` : ''}
                    <div class="cart-item-price-qty">
                        <div class="qty-control">
                            <button class="qty-btn" onclick="updateCartQuantity('${item.id}', -1)">-</button>
                            <span class="qty-value">${item.quantity}</span>
                            <button class="qty-btn" onclick="updateCartQuantity('${item.id}', 1)">+</button>
                        </div>
                        <span class="item-price">${(item.price * item.quantity).toLocaleString()} FC</span>
                    </div>
                </div>
            </div>
        `).join('');

        cartFooter.style.display = 'block';
        updateCartSummary();
    }
}

function updateCartSummary() {
    // Robust defaults for settings
    const settings = adminSettings || {};
    const freeThreshold = settings.freeShippingThreshold || 100000;
    const delivery = settings.deliveryPrice || 0;
    const taxRate = settings.taxRate || 0;

    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const deliveryFee = subtotal >= freeThreshold ? 0 : delivery;
    const tax = subtotal * taxRate;
    const total = subtotal + deliveryFee + tax;

    document.getElementById('cartSubtotal').textContent = `${subtotal.toFixed(2)} FC`;
    const deliveryEl = document.getElementById('cartDelivery');
    if (deliveryEl) {
        deliveryEl.innerHTML = deliveryFee === 0
            ? '<span class="free-delivery">Gratuit</span>'
            : `${deliveryFee.toFixed(2)} FC`;
    }
    document.getElementById('cartTax').textContent = `${tax.toFixed(2)} FC`;
    document.getElementById('cartTotal').textContent = `${total.toFixed(2)} FC`;
}

function toggleCart() {
    const drawer = document.getElementById('cartDrawer');
    if (drawer) drawer.classList.toggle('active');
}

// Checkout Logic - Added for Django Integration
let checkoutStepperInitialized = false;

function initCheckoutStepper() {
    const stepper = document.getElementById('checkoutStepper');
    const steps = document.querySelectorAll('.checkout-step');
    if (!stepper || steps.length === 0) return;

    if (!checkoutStepperInitialized) {
        stepper.addEventListener('click', (e) => {
            const stepEl = e.target.closest('.step');
            if (stepEl && stepEl.dataset.step) {
                const nextStep = parseInt(stepEl.dataset.step, 10);
                if (!Number.isNaN(nextStep)) setCheckoutStep(nextStep);
            }
        });

        document.querySelectorAll('[data-step-next]').forEach(btn => {
            btn.addEventListener('click', () => {
                const nextStep = parseInt(btn.getAttribute('data-step-next'), 10);
                if (!validateCheckoutStep(getActiveCheckoutStep())) return;
                setCheckoutStep(nextStep);
            });
        });

        document.querySelectorAll('[data-step-prev]').forEach(btn => {
            btn.addEventListener('click', () => {
                const prevStep = parseInt(btn.getAttribute('data-step-prev'), 10);
                setCheckoutStep(prevStep);
            });
        });

        checkoutStepperInitialized = true;
    }

    setCheckoutStep(1);
}

function getActiveCheckoutStep() {
    const active = document.querySelector('.checkout-step.active');
    if (!active) return 1;
    const step = parseInt(active.dataset.step, 10);
    return Number.isNaN(step) ? 1 : step;
}

function setCheckoutStep(stepNumber) {
    const steps = document.querySelectorAll('.checkout-step');
    const stepIndicators = document.querySelectorAll('.checkout-stepper .step');
    steps.forEach(step => {
        step.classList.toggle('active', parseInt(step.dataset.step, 10) === stepNumber);
    });
    stepIndicators.forEach(step => {
        step.classList.toggle('active', parseInt(step.dataset.step, 10) === stepNumber);
    });
}

function validateCheckoutStep(stepNumber) {
    const stepEl = document.querySelector(`.checkout-step[data-step="${stepNumber}"]`);
    if (!stepEl) return true;
    const requiredInputs = stepEl.querySelectorAll('input[required], textarea[required], select[required]');
    for (const input of requiredInputs) {
        if (!input.checkValidity()) {
            input.reportValidity();
            return false;
        }
    }
    return true;
}

async function proceedToCheckout() {
    if (cart.length === 0) return;

    const checkoutBtn = document.querySelector('.checkout-btn');
    const originalText = checkoutBtn ? checkoutBtn.innerHTML : '';
    if (checkoutBtn) {
        checkoutBtn.innerHTML = 'Traitement...';
        checkoutBtn.disabled = true;
    }

    // Force sync before verify
    await saveCart();

    const checkoutView = document.getElementById('checkoutView');
    if (checkoutView) {
        showView('checkout');
        if (checkoutBtn) {
            checkoutBtn.innerHTML = originalText;
            checkoutBtn.disabled = false;
        }
    } else {
        // Redirection for standalone pages (like catalog.html)
        window.location.href = window.urls.checkout;
    }
}

function renderCheckoutSummary() {
    const list = document.getElementById('checkoutOrderItems');
    if (!list) return;

    // Separate customized and standard items
    const customItems = cart.filter(item => item.customization && item.customization.choices);
    const standardItems = cart.filter(item => !item.customization || !item.customization.choices);

    let html = '';

    // Render Custom Items Section (if any)
    if (customItems.length > 0) {
        html += `
            <div class="checkout-section-divider" style="margin: 15px 0 10px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px;">
                <h5 style="font-family: 'Playfair Display', serif; color: #1a1a1a; margin: 0; font-size: 16px;">Vos Créations Personnalisées</h5>
            </div>
        `;
        html += customItems.map(item => `
            <div class="order-item custom-order-item" style="background: #fafaf9; border: 1px solid #e7e5e4; border-radius: 8px; margin-bottom: 10px; padding: 10px;">
                <div class="order-item-image" style="position: relative;">
                    ${item.customization && item.customization.preview
                ? `<img src="${item.customization.preview}" alt="${item.name}" style="object-fit: contain; background: #fff; border-radius: 4px; border: 1px solid #eee;">`
                : `<img src="${item.image}" alt="${item.name}">`
            }
                    <span class="item-qty-badge">${item.quantity}</span>
                </div>
                <div class="order-item-details" style="flex: 1; padding-left: 10px;">
                    <h4 style="font-size: 14px; margin-bottom: 4px;">${item.name}</h4>
                    
                    ${item.customization && item.customization.choices ? (() => {
                const choices = item.customization.choices;
                let detailHtml = '<div class="custom-specs" style="font-size: 12px; color: #57534e;">';

                // Studio workflow
                if (choices.studio_engraving && choices.studio_engraving.text) {
                    detailHtml += `<div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                                        <span>Gravure:</span> 
                                        <span style="font-weight:600;">"${choices.studio_engraving.text}"</span>
                                     </div>`;
                    detailHtml += `<div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                                        <span>Police:</span> 
                                        <span>${choices.studio_engraving.font}</span>
                                     </div>`;
                } else {
                    Object.entries(choices).forEach(([key, val]) => {
                        if (key.startsWith('studio_')) return;
                        let displayVal = val;
                        if (typeof val === 'object' && val.text) displayVal = val.text;
                        if (displayVal) {
                            detailHtml += `<div>${displayVal}</div>`;
                        }
                    });
                }

                // Show extra cost breakdown if applicable
                if (item.extraCost > 0) {
                    detailHtml += `<div style="margin-top: 4px; font-size: 11px; color: #78716c; border-top: 1px dashed #e7e5e4; padding-top: 2px;">
                                        Base: ${(item.basePrice).toLocaleString()} FC <br>
                                        + Perso: ${(item.extraCost).toLocaleString()} FC
                                     </div>`;
                }

                detailHtml += '</div>';
                return detailHtml;
            })() : ''}
                </div>
                <div class="order-item-price" style="font-weight: 600; align-self: flex-start;">
                    ${(item.price * item.quantity).toLocaleString()} FC
                </div>
            </div>
        `).join('');
    }

    // Render Standard Items Section
    if (standardItems.length > 0) {
        if (customItems.length > 0) {
            html += `
                <div class="checkout-section-divider" style="margin: 20px 0 10px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px;">
                    <h5 style="font-family: 'Playfair Display', serif; color: #1a1a1a; margin: 0; font-size: 16px;">Articles Standards</h5>
                </div>
            `;
        }
        html += standardItems.map(item => `
            <div class="order-item">
                <div class="order-item-image">
                    <img src="${item.image}" alt="${item.name}">
                    <span class="item-qty-badge">${item.quantity}</span>
                </div>
                <div class="order-item-details">
                    <h4>${item.name}</h4>
                    <p class="text-muted" style="font-size:12px;">${item.material || 'Standard'}</p>
                </div>
                <div class="order-item-price">
                    ${(item.price * item.quantity).toLocaleString()} FC
                </div>
            </div>
        `).join('');
    }

    list.innerHTML = html;

    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const deliveryFee = subtotal >= adminSettings.freeShippingThreshold ? 0 : adminSettings.deliveryPrice;
    const tax = subtotal * adminSettings.taxRate;
    const total = subtotal + deliveryFee + tax;

    const subEl = document.getElementById('checkoutSubtotal');
    if (subEl) subEl.textContent = `${subtotal.toFixed(2)} FC`;

    const delEl = document.getElementById('checkoutDelivery');
    if (delEl) delEl.innerHTML = deliveryFee === 0 ? '<span class="free-delivery">Gratuit</span>' : `${deliveryFee.toFixed(2)} FC`;

    const taxEl = document.getElementById('checkoutTax');
    if (taxEl) taxEl.textContent = `${tax.toFixed(2)} FC`;

    const totEl = document.getElementById('checkoutTotal');
    if (totEl) totEl.textContent = `${total.toFixed(2)} FC`;
}

// Filter Functions
function filterProducts() {
    return products.filter(product => {
        if (filters.category !== 'Tous' && product.category.toUpperCase() !== filters.category.toUpperCase()) return false;
        if (filters.material !== 'Tous' && product.material !== filters.material) return false;

        if (filters.priceRange !== 'Tous') {
            if (filters.priceRange === '0-100000' && product.price >= 100000) return false;
            if (filters.priceRange === '100000-500000' && (product.price < 100000 || product.price >= 500000)) return false;
            if (filters.priceRange === '500000-1000000' && (product.price < 500000 || product.price >= 1000000)) return false;
            if (filters.priceRange === '1000000+' && product.price < 1000000) return false;
        }

        if (filters.customizable === 'Oui' && !product.customizable) return false;
        if (filters.customizable === 'Non' && product.customizable) return false;

        return true;
    });
}

function sortProducts(productsList) {
    const sorted = [...productsList];

    if (currentSort === 'price-asc') {
        sorted.sort((a, b) => a.price - b.price);
    } else if (currentSort === 'price-desc') {
        sorted.sort((a, b) => b.price - a.price);
    }

    return sorted;
}

function applyFilters() {
    const cat = document.querySelector('input[name="category"]:checked');
    if (cat) filters.category = cat.value;
    const mat = document.querySelector('input[name="material"]:checked');
    if (mat) filters.material = mat.value;
    const price = document.querySelector('input[name="price"]:checked');
    if (price) filters.priceRange = price.value;
    const cust = document.querySelector('input[name="customizable"]:checked');
    if (cust) filters.customizable = cust.value;

    renderCatalogueProducts();
}

function resetFilters() {
    filters = {
        category: 'Tous',
        material: 'Tous',
        priceRange: 'Tous',
        customizable: 'Tous',
    };
    document.querySelectorAll('.filter-options input[type="radio"]').forEach(input => {
        input.checked = input.value === 'Tous';
    });
    renderCatalogueProducts();
}

function handleSort(value) {
    currentSort = value;
    const sortMob = document.getElementById('sortMobile');
    if (sortMob) sortMob.value = value;
    const sortDesk = document.getElementById('sortDesktop');
    if (sortDesk) sortDesk.value = value;
    renderCatalogueProducts();
}

function toggleFilters() {
    const sidebar = document.getElementById('filtersSidebar');
    if (sidebar) sidebar.classList.toggle('active');
}

// -------- Site content editor (hero, hero grid, about) ----------
function initSiteContent() {
    initialContentDefaults = buildDefaultContentFromDom();
    const stored = loadStoredContent();
    siteContent = stored || JSON.parse(JSON.stringify(initialContentDefaults));
    setupContentFormListeners();
    renderSiteContent();
}

function buildDefaultContentFromDom() {
    const base = JSON.parse(JSON.stringify(defaultSiteContent));

    const heroImg = document.getElementById('heroMainImage');
    if (heroImg && heroImg.src) base.hero.image = heroImg.src;
    const heroTitle = document.getElementById('heroMainTitle');
    if (heroTitle) base.hero.title = heroTitle.textContent.trim() || base.hero.title;
    const heroSubtitle = document.getElementById('heroMainSubtitle');
    if (heroSubtitle) base.hero.subtitle = heroSubtitle.textContent.trim() || base.hero.subtitle;

    const cards = document.querySelectorAll('.hero-card[data-hero-card]');
    cards.forEach(card => {
        const idx = parseInt(card.dataset.heroCard || '0', 10);
        if (!base.heroGrid[idx]) base.heroGrid[idx] = { title: '', subtitle: '', image: '', category: 'Tous' };
        const titleEl = card.querySelector('.hero-card-content h2');
        const subEl = card.querySelector('.hero-card-content p');
        const imgEl = card.querySelector('img');
        if (titleEl) base.heroGrid[idx].title = titleEl.textContent.trim() || base.heroGrid[idx].title;
        if (subEl) base.heroGrid[idx].subtitle = subEl.textContent.trim() || base.heroGrid[idx].subtitle;
        if (imgEl && imgEl.src) base.heroGrid[idx].image = imgEl.src;
        base.heroGrid[idx].category = card.dataset.category || base.heroGrid[idx].category || 'Tous';
    });

    const aboutTitle = document.getElementById('aboutTitle');
    if (aboutTitle) base.about.title = aboutTitle.textContent.trim() || base.about.title;
    const aboutP1 = document.getElementById('aboutParagraph1');
    if (aboutP1) base.about.paragraph1 = aboutP1.textContent.trim() || base.about.paragraph1;
    const aboutP2 = document.getElementById('aboutParagraph2');
    if (aboutP2) base.about.paragraph2 = aboutP2.textContent.trim() || base.about.paragraph2;
    const aboutImg = document.getElementById('aboutImage');
    if (aboutImg && aboutImg.src) base.about.image = aboutImg.src;
    for (let i = 0; i < 3; i++) {
        if (!base.about.stats[i]) base.about.stats[i] = { value: '', label: '' };
        const valEl = document.getElementById(`aboutStat${i}Value`);
        const labelEl = document.getElementById(`aboutStat${i}Label`);
        if (valEl) base.about.stats[i].value = valEl.textContent.trim() || base.about.stats[i].value;
        if (labelEl) base.about.stats[i].label = labelEl.textContent.trim() || base.about.stats[i].label;
    }
    return base;
}

function loadStoredContent() {
    try {
        const raw = localStorage.getItem('siteContent');
        if (raw) return JSON.parse(raw);
    } catch (e) {
        console.warn('Cannot load site content', e);
    }
    return null;
}

function saveContentToStorage() {
    try {
        localStorage.setItem('siteContent', JSON.stringify(siteContent));
    } catch (e) {
        console.warn('Cannot save site content', e);
    }
}

function renderSiteContent() {
    renderHeroSection();
    renderHeroGrid();
    renderAboutSection();
    renderContentPreview();
}

function renderHeroSection() {
    if (!siteContent) return;
    const hero = siteContent.hero;
    const titleEl = document.getElementById('heroMainTitle');
    const subEl = document.getElementById('heroMainSubtitle');
    const imgEl = document.getElementById('heroMainImage');
    if (titleEl && hero.title) titleEl.textContent = hero.title;
    if (subEl && hero.subtitle) subEl.textContent = hero.subtitle;
    if (imgEl && hero.image) imgEl.src = hero.image;
}

function renderHeroGrid() {
    if (!siteContent) return;
    siteContent.heroGrid.forEach((card, idx) => {
        const cardEl = document.querySelector(`.hero-card[data-hero-card=\"${idx}\"]`);
        if (!cardEl) return;
        const titleEl = cardEl.querySelector('.hero-card-content h2');
        const subEl = cardEl.querySelector('.hero-card-content p');
        const imgEl = cardEl.querySelector('img');
        if (titleEl && card.title) titleEl.textContent = card.title;
        if (subEl && card.subtitle) subEl.textContent = card.subtitle;
        if (imgEl && card.image) imgEl.src = card.image;
        const category = card.category || 'Tous';
        cardEl.dataset.category = category;
        cardEl.onclick = () => {
            filters.category = category;
            showView('catalogue');
            renderCatalogueProducts();
        };
    });
}

function renderAboutSection() {
    if (!siteContent) return;
    const about = siteContent.about;
    const titleEl = document.getElementById('aboutTitle');
    const p1El = document.getElementById('aboutParagraph1');
    const p2El = document.getElementById('aboutParagraph2');
    const imgEl = document.getElementById('aboutImage');
    if (titleEl && about.title) titleEl.textContent = about.title;
    if (p1El && about.paragraph1) p1El.textContent = about.paragraph1;
    if (p2El && about.paragraph2) p2El.textContent = about.paragraph2;
    if (imgEl && about.image) imgEl.src = about.image;
    if (about.stats) {
        for (let i = 0; i < about.stats.length; i++) {
            const stat = about.stats[i];
            const valEl = document.getElementById(`aboutStat${i}Value`);
            const labelEl = document.getElementById(`aboutStat${i}Label`);
            if (valEl && stat.value !== undefined) valEl.textContent = stat.value;
            if (labelEl && stat.label !== undefined) labelEl.textContent = stat.label;
        }
    }
}

function renderContentPreview() {
    const preview = document.getElementById('contentPreview');
    if (!preview || !siteContent) return;
    const hero = siteContent.hero;
    const about = siteContent.about;
    preview.innerHTML = `
        <div class="preview-card">
            <h4>Hero</h4>
            ${hero.image ? `<img src="${hero.image}" alt="Hero preview">` : ''}
            <p><strong>${hero.title || ''}</strong></p>
            <p style="color:#cbd5e1;">${hero.subtitle || ''}</p>
        </div>
        <div class="preview-card">
            <h4>Hero grid</h4>
            ${siteContent.heroGrid.map(card => `
                <div style="margin-bottom:0.5rem;">
                    ${card.image ? `<img src="${card.image}" alt="${card.title}">` : ''}
                    <p><strong>${card.title || ''}</strong></p>
                    <p style="color:#cbd5e1;">${card.subtitle || ''}</p>
                    <p style="color:#9ca3af; font-size:12px;">Catégorie: ${card.category || 'Tous'}</p>
                </div>
            `).join('')}
        </div>
        <div class="preview-card">
            <h4>A propos</h4>
            ${about.image ? `<img src="${about.image}" alt="About preview">` : ''}
            <p><strong>${about.title || ''}</strong></p>
            <p style="color:#cbd5e1;">${about.paragraph1 || ''}</p>
            <p style="color:#cbd5e1;">${about.paragraph2 || ''}</p>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:0.35rem;margin-top:0.35rem;">
                ${about.stats ? about.stats.map(stat => `
                    <div style="background:#0b1220;border:1px solid #1f2937;border-radius:6px;padding:0.35rem;">
                        <div style="font-weight:700;">${stat.value || ''}</div>
                        <div style="color:#9ca3af;font-size:12px;">${stat.label || ''}</div>
                    </div>
                `).join('') : ''}
            </div>
        </div>
    `;
}

function setupContentFormListeners() {
    const fields = [
        { id: 'adminHeroTitle', path: ['hero', 'title'] },
        { id: 'adminHeroSubtitle', path: ['hero', 'subtitle'] },
        { id: 'adminHeroImage', path: ['hero', 'image'] },
        { id: 'adminCard0Title', path: ['heroGrid', 0, 'title'] },
        { id: 'adminCard0Subtitle', path: ['heroGrid', 0, 'subtitle'] },
        { id: 'adminCard0Image', path: ['heroGrid', 0, 'image'] },
        { id: 'adminCard0Category', path: ['heroGrid', 0, 'category'] },
        { id: 'adminCard1Title', path: ['heroGrid', 1, 'title'] },
        { id: 'adminCard1Subtitle', path: ['heroGrid', 1, 'subtitle'] },
        { id: 'adminCard1Image', path: ['heroGrid', 1, 'image'] },
        { id: 'adminCard1Category', path: ['heroGrid', 1, 'category'] },
        { id: 'adminAboutTitle', path: ['about', 'title'] },
        { id: 'adminAboutP1', path: ['about', 'paragraph1'] },
        { id: 'adminAboutP2', path: ['about', 'paragraph2'] },
        { id: 'adminStat0Value', path: ['about', 'stats', 0, 'value'] },
        { id: 'adminStat0Label', path: ['about', 'stats', 0, 'label'] },
        { id: 'adminStat1Value', path: ['about', 'stats', 1, 'value'] },
        { id: 'adminStat1Label', path: ['about', 'stats', 1, 'label'] },
        { id: 'adminStat2Value', path: ['about', 'stats', 2, 'value'] },
        { id: 'adminStat2Label', path: ['about', 'stats', 2, 'label'] },
        { id: 'adminAboutImage', path: ['about', 'image'] },
    ];

    fields.forEach(field => {
        const el = document.getElementById(field.id);
        if (!el) return;
        const current = getNested(siteContent, field.path) || '';
        el.value = current;
        if (!contentFormInitialized) {
            el.addEventListener('input', () => {
                setNested(siteContent, field.path, el.value);
                renderSiteContent();
                scheduleContentSave();
            });
        }
    });
    contentFormInitialized = true;
}

function scheduleContentSave() {
    clearTimeout(saveContentTimeout);
    saveContentTimeout = setTimeout(() => {
        saveContentToStorage();
        const msg = document.getElementById('contentSavedMessage');
        if (msg) {
            msg.textContent = 'Previsualisation mise a jour';
            setTimeout(() => { msg.textContent = ''; }, 1200);
        }
    }, 300);
}

function saveContentSettings() {
    saveContentToStorage();
    const msg = document.getElementById('contentSavedMessage');
    if (msg) {
        msg.textContent = 'Contenu enregistre';
        setTimeout(() => { msg.textContent = ''; }, 1500);
    }
}

function resetContentDefaults() {
    siteContent = JSON.parse(JSON.stringify(initialContentDefaults || defaultSiteContent));
    setupContentFormListeners();
    renderSiteContent();
    saveContentSettings();
}

function getNested(obj, path) {
    return path.reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : ''), obj);
}

function setNested(obj, path, value) {
    let ref = obj;
    for (let i = 0; i < path.length - 1; i++) {
        const key = path[i];
        if (ref[key] === undefined) {
            ref[key] = typeof path[i + 1] === 'number' ? [] : {};
        }
        ref = ref[key];
    }
    ref[path[path.length - 1]] = value;
}
// ---------------------------------------------------------------

// Admin Functions
function showAdminTab(tab) {
    const tabs = document.querySelectorAll('.admin-tab');
    const contents = document.querySelectorAll('.admin-content');
    if (!tabs.length || !contents.length) return;
    tabs.forEach(t => t.classList.remove('active'));
    contents.forEach(c => c.classList.remove('active'));

    event.target.closest('.admin-tab').classList.add('active');
    document.getElementById('admin' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
}


function renderFeaturedProducts() {
    const container = document.getElementById('featuredProducts');
    if (!container) return;

    // Use top 4 most recent products (already sorted by ID desc in views.py)
    const featured = products.slice(0, 4);

    container.innerHTML = featured.map(product => createProductCard(product)).join('');
}

function renderProductsTable() {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) return;
    tbody.innerHTML = products.map(product => {
        let stockClass = 'high';
        if (product.stock < 10) stockClass = 'low';
        else if (product.stock < 20) stockClass = 'medium';

        return `
            <tr>
                <td>
                    <div class="product-table-info">
                        <img src="${product.image}" alt="${product.name}" class="product-table-image">
                        <div>
                            <p class="product-table-name">${product.name}</p>
                            <p class="product-table-meta">${product.material}</p>
                        </div>
                    </div>
                </td>
                <td>${product.category}</td>
                <td>${product.price ? product.price.toLocaleString() : '0'} FC</td>
                <td>
                    <span class="stock-status ${stockClass}">${product.stock} unités</span>
                </td>
                <td>
                    ${product.badge ? `<span class="product-status-badge">${product.badge}</span>` : ''}
                </td>
                <td>
                    <button class="edit-btn">Edit</button>
                </td>
            </tr>
        `;
    }).join('');
}

function renderTopProducts() {
    const container = document.getElementById('topProductsList');
    if (!container) return;
    container.innerHTML = products.slice(0, 5).map((product, index) => {
        const sales = 45 - index * 8;
        const revenue = sales * (product.price || 0);

        return `
            <div class="top-product-item">
                <div class="top-product-left">
                    <span class="top-product-rank">#${index + 1}</span>
                    <img src="${product.image}" alt="${product.name}" class="top-product-image">
                    <div>
                        <p class="top-product-name">${product.name}</p>
                        <p class="top-product-category">${product.category}</p>
                    </div>
                </div>
                <div class="top-product-right">
                    <p class="top-product-sales">${sales} ventes</p>
                    <p class="top-product-revenue">${revenue.toLocaleString()} FC</p>
                </div>
            </div>
        `;
    }).join('');
}

function updateNavActive(clickedItem) {
    if (!clickedItem) return;

    // Toggle for desktop tabs
    const tabs = document.querySelectorAll('.tab-item');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab === clickedItem || (clickedItem.dataset && tab.dataset.category === clickedItem.dataset.category)) {
            tab.classList.add('active');
        }
    });

    // Toggle for mobile pills
    const pills = document.querySelectorAll('.pill-item');
    pills.forEach(pill => {
        pill.classList.remove('active');
        if (pill === clickedItem || (clickedItem.dataset && pill.textContent.trim().toUpperCase() === clickedItem.textContent.trim().toUpperCase())) {
            pill.classList.add('active');
        }
    });

    // Handle scroll to top when switching categories
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Premium Scroll Reveal Animations
 */
function initPremiumAnimations() {
    const observerOptions = {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
    revealElements.forEach(el => observer.observe(el));
}
// Sidebar Logic
// Sidebar Logic
function openSidebar(productId) {
    console.log("Opening Sidebar for Product:", productId);
    const product = products.find(p => String(p.id) === String(productId));
    if (!product) return;

    // Ensure Base State
    if (!productCustomizations[productId]) {
        if (typeof initCustomizationState === 'function') {
            initCustomizationState(productId);
        } else {
            productCustomizations[productId] = { quantity: 1, extra_cost: 0, choices: {} };
        }
    }

    // Ensure Premium Engraving State (Recto/Verso)
    const custom = productCustomizations[productId];
    if (product.customizable) {
        custom.isCustomizing = true; // Mark as customizing to trigger price update
        if (!custom.choices) custom.choices = {};
        if (!custom.choices.recto) custom.choices.recto = { active: false, text: '', font: 'Minion Pro', image_data: '', image_scale: 1, image_x: 0, image_y: 0, image_preview: '' };
        if (!custom.choices.verso) custom.choices.verso = { active: false, text: '', font: 'Minion Pro', image_data: '', image_scale: 1, image_x: 0, image_y: 0, image_preview: '' };

        // Update price display on main page immediately
        updateMainPagePrice(product);
    }

    const sidebar = document.querySelector('.product-sidebar');
    const overlay = document.querySelector('.product-sidebar-overlay');

    if (sidebar && overlay) {
        sidebar.classList.add('active');
        overlay.classList.add('active');

        // Reset State
        sidebar.classList.add('glass-sidebar');
        document.body.classList.add('sidebar-open');

        // Logic routing: Customizable vs Standard
        if (product.customizable) {
            renderEngravingUI(product);
        } else {
            // Standard Product View
            const content = document.getElementById('sidebarContent');
            content.innerHTML = `
                <div class="product-header-sidebar">
                    <img src="${product.image}" class="sidebar-hero-img">
                    <h2 class="sidebar-product-title">${product.name}</h2>
                    <p class="sidebar-product-desc">${product.description || ''}</p>
                </div>
            `;
            // Update footer
            renderSidebarFooter(product);
        }
    }
}

function closeSidebar() {
    const sidebar = document.querySelector('.product-sidebar');
    const overlay = document.querySelector('.product-sidebar-overlay');
    if (sidebar) sidebar.classList.remove('active');
    if (overlay) overlay.classList.remove('active');
    document.body.classList.remove('sidebar-open');
}

// Render the Premium Engraving UI
function renderEngravingUI(product) {
    const content = document.getElementById('sidebarContent');
    const custom = productCustomizations[product.id];

    // Fetch authorized components and fonts for this product
    fetch(`/store/api/product/${product.id}/customization-data/`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                content.innerHTML = `<div class="alert alert-danger">Erreur: Impossible de charger les composants</div>`;
                return;
            }

            // Save the engraving price to the product object for calculations
            product.engraving_price = data.engraving_price;

            const components = data.components || [];
            const fonts = data.fonts || [];
            const componentMap = {};
            components.forEach((comp) => {
                componentMap[String(comp.id)] = comp;
            });
            custom._components_map = componentMap;

            if (!custom.choices.studio_component && components.length > 0) {
                custom.choices.studio_component = String(components[0].id);
                custom.choices.studio_component_label = components[0].name || '';
            }

            const fontOptions = fonts
                .map((font) => ({
                    label: font.name || font.font_family,
                    value: font.font_family || font.name
                }))
                .filter((font) => font.label && font.value);

            custom._font_options = fontOptions;
            if (fontOptions.length > 0) {
                const allowedValues = fontOptions.map((f) => f.value);
                if (!allowedValues.includes(custom.choices.recto.font)) {
                    custom.choices.recto.font = allowedValues[0];
                }
                if (!allowedValues.includes(custom.choices.verso.font)) {
                    custom.choices.verso.font = allowedValues[0];
                }
            }
            const engravingMode = data.engraving_mode || product.engraving_mode || 'text';
            custom.choices.engraving_mode = engravingMode;
            if (engravingMode !== 'text' && custom.choices.recto && custom.choices.recto.active === false) {
                custom.choices.recto.active = true;
            }

            // Generate components grid HTML
            let componentsHTML = '';
            if (components.length > 0) {
                componentsHTML = `
                    <div class="components-section" style="margin-bottom: 1.5rem;">
                        <h5 style="font-weight: 600; margin-bottom: 0.75rem; color: #333;">Formes Disponibles</h5>
                        <div class="components-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1rem;">
                            ${components.map((comp) => `
                                <div class="component-item ${String(custom.choices.studio_component) === String(comp.id) ? 'active' : ''}"
                                     onclick="setSidebarComponent('${product.id}', '${comp.id}')"
                                     data-label="${comp.shape || comp.name}"
                                     style="position: relative; cursor: pointer; border: 2px solid ${String(custom.choices.studio_component) === String(comp.id) ? '#0d6efd' : '#e9ecef'}; border-radius: 8px; padding: 0.5rem; text-align: center; transition: all 0.2s; box-shadow: ${String(custom.choices.studio_component) === String(comp.id) ? '0 0 8px rgba(13,110,253,0.25)' : 'none'};" 
                                     onmouseover="this.style.borderColor='#0d6efd'; this.style.boxShadow='0 0 8px rgba(13,110,253,0.3)'"
                                     onmouseout="this.style.borderColor='${String(custom.choices.studio_component) === String(comp.id) ? '#0d6efd' : '#e9ecef'}'; this.style.boxShadow='${String(custom.choices.studio_component) === String(comp.id) ? '0 0 8px rgba(13,110,253,0.25)' : 'none'}'">
                                    <img src="${comp.image_url}" alt="${comp.name}" style="max-height: 80px; max-width: 80px; object-fit: contain; margin: auto; display: block;">
                                    <small style="display: block; margin-top: 0.25rem; font-size: 0.75rem; color: #666;">${comp.name}</small>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            let fontsHTML = '';

            // Render the complete sidebar
            const selectedComponent = componentMap[String(custom.choices.studio_component)] || components[0] || null;
            const previewImage = selectedComponent && selectedComponent.image_url ? selectedComponent.image_url : '';
            const previewText = custom.choices.recto && custom.choices.recto.active ? (custom.choices.recto.text || '') : '';

            content.innerHTML = `
        <div class="product-header-sidebar" style="position:relative; text-align:center; padding-bottom:1.5rem;">
            <div class="engraving-preview-box" style="position: relative; width: 100%; max-width: 320px; aspect-ratio: 1; margin: 0 auto 1.5rem; border-radius: 20px; background: #fff; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
                <!-- THE SVG PREVIEWER -->
                <svg viewBox="0 0 400 400" style="width: 100%; height: 100%; display: block;">
                    <defs>
                        <!-- Dynamic Clip Path based on shape -->
                        <clipPath id="engravingMaskPath">
                            ${getShapeSVGPath(custom.choices.studio_component_label || '', 400, 400)}
                        </clipPath>
                    </defs>
                    
                    <!-- Clipped User Photo (Behind) -->
                    <g transform="translate(0, 25)">
                        <image id="engravingPhotoPreview-recto-svg" 
                               href="${custom.choices.recto.image_preview || ''}" 
                               x="100" y="100" width="200" height="200" 
                               clip-path="url(#engravingMaskPath)"
                               style="opacity: ${custom.choices.recto.image_preview ? '1' : '0'}; transition: opacity 0.3s; filter: contrast(1.1) grayscale(1);" />
                    </g>
                    
                    <!-- Text Overlay (Below product image for texture) -->
                    <text x="50%" y="60%" text-anchor="middle" id="previewTextSVG"
                          style="font-family: ${custom.choices.recto.font || 'Arial'}; font-size: 20px; font-weight: 500; fill: #111; opacity: ${previewText ? '1' : '0'}; pointer-events: none;">
                          ${previewText}
                    </text>

                    <!-- Background Product Image (On top with multiply for texture) -->
                    <image id="sidebarPreviewImg" href="${previewImage || ''}" x="0" y="0" width="400" height="400" 
                           style="mix-blend-mode: multiply; pointer-events: none;" preserveAspectRatio="xMidYMid meet" />
                </svg>
            </div>
            <h2 class="sidebar-product-title" style="margin-bottom: 0.5rem; font-weight: 700;">${product.name}</h2>
            <p class="sidebar-product-price" id="sidebarTopPrice" style="color: #b11226; font-size: 1.25rem; font-weight: 600;">${calculateTotalPrice(product).toLocaleString()} FC</p>



            
            ${componentsHTML}
            ${fontsHTML}
        </div>

        <div class="engraving-container">
            <!-- RECTO SECTION -->
            <div class="engraving-section ${custom.choices.recto.active ? 'active' : ''}" id="section-recto">
                <div class="engraving-header" onclick="toggleEngravingSection('${product.id}', 'recto')">
                    <div class="engraving-checkbox">
                        ${custom.choices.recto.active ? '<i class="bi bi-check"></i>' : ''}
                    </div>
                    <span class="engraving-title">RECTO (FACE AVANT)</span>
                </div>
                <div class="engraving-content">
                    <div class="engraving-form">
                        <div class="form-group">
                            <div class="form-label-row">
                                <span class="form-label">Calcul Gravure</span>
                                <span class="badge-offer">OFFERTE</span>
                            </div>
                        </div>

                        ${engravingMode !== 'image' ? `
                        <div class="form-group">
                            <label class="form-label" style="margin-bottom:0.5rem; display:block;">Typographie</label>
                            <select class="premium-select" onchange="updateEngravingField('${product.id}', 'recto', 'font', this.value)" ${fontOptions.length > 0 ? '' : 'disabled'}>
                                ${fontOptions.length > 0 ? fontOptions.map((font) => `
                                    <option value="${font.value}" style="font-family: ${font.value};" ${custom.choices.recto.font === font.value ? 'selected' : ''}>${font.label}</option>
                                `).join('') : `<option value="">Aucune police disponible</option>`}
                            </select>
                            <div class="font-preview-box" style="font-family: ${custom.choices.recto.font}">
                                Preview
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" style="margin-bottom:0.5rem; display:block;">Message (Ligne 1)</label>
                            <div class="input-wrapper">
                                <input type="text" class="premium-input" 
                                       placeholder="Votre texte..." 
                                       maxlength="25"
                                       value="${custom.choices.recto.text}"
                                       oninput="updateEngravingField('${product.id}', 'recto', 'text', this.value)">
                                <span class="char-counter">${custom.choices.recto.text.length} / 25</span>
                            </div>
                        </div>
                        ` : ''}

                        ${engravingMode !== 'text' ? `
                        <div class="form-group engraving-image-group" data-side="recto">
                            <label class="form-label" style="margin-bottom:0.5rem; display:block;">Image / Photo</label>
                            <input type="file" class="form-control engraving-image-input" data-side="recto" accept="image/*">
                            <div class="engraving-editor">
                                <canvas id="engravingCanvas-recto" width="260" height="260"></canvas>
                                <div class="engraving-editor-controls">
                                    <input type="range" class="form-range engraving-zoom" data-side="recto" min="0.2" max="3" step="0.01" value="${custom.choices.recto.image_scale || 1}">
                                    <button type="button" class="btn btn-light btn-sm engraving-reset" data-side="recto">Reinitialiser</button>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>

            <!-- VERSO SECTION (Optional) -->
            <div class="engraving-section ${custom.choices.verso.active ? 'active' : ''}" id="section-verso">
                <div class="engraving-header" onclick="toggleEngravingSection('${product.id}', 'verso')">
                    <div class="engraving-checkbox">
                        ${custom.choices.verso.active ? '<i class="bi bi-check"></i>' : ''}
                    </div>
                    <span class="engraving-title">VERSO (FACE ARRIÈRE)</span>
                </div>
                <div class="engraving-content">
                    <div class="engraving-form">
                         <div class="form-group">
                            <div class="form-label-row">
                                <span class="form-label">Calcul Gravure</span>
                                <span class="badge-offer">OFFERTE</span>
                            </div>
                        </div>
                        ${engravingMode !== 'image' ? `
                         <div class="form-group">
                            <label class="form-label" style="margin-bottom:0.5rem; display:block;">Typographie</label>
                            <select class="premium-select" onchange="updateEngravingField('${product.id}', 'verso', 'font', this.value)" ${fontOptions.length > 0 ? '' : 'disabled'}>
                                ${fontOptions.length > 0 ? fontOptions.map((font) => `
                                    <option value="${font.value}" style="font-family: ${font.value};" ${custom.choices.verso.font === font.value ? 'selected' : ''}>${font.label}</option>
                                `).join('') : `<option value="">Aucune police disponible</option>`}
                            </select>
                             <div class="font-preview-box" style="font-family: ${custom.choices.verso.font}">
                                Preview
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label" style="margin-bottom:0.5rem; display:block;">Message</label>
                            <div class="input-wrapper">
                                <input type="text" class="premium-input" 
                                       placeholder="Votre texte..." 
                                       maxlength="25"
                                       value="${custom.choices.verso.text}"
                                       oninput="updateEngravingField('${product.id}', 'verso', 'text', this.value)">
                                <span class="char-counter">${custom.choices.verso.text.length} / 25</span>
                            </div>
                        </div>
                        ` : ''}

                        ${engravingMode !== 'text' ? `
                        <div class="form-group engraving-image-group" data-side="verso">
                            <label class="form-label" style="margin-bottom:0.5rem; display:block;">Image / Photo</label>
                            <input type="file" class="form-control engraving-image-input" data-side="verso" accept="image/*">
                            <div class="engraving-editor">
                                <canvas id="engravingCanvas-verso" width="260" height="260"></canvas>
                                <div class="engraving-editor-controls">
                                    <input type="range" class="form-range engraving-zoom" data-side="verso" min="0.2" max="3" step="0.01" value="${custom.choices.verso.image_scale || 1}">
                                    <button type="button" class="btn btn-light btn-sm engraving-reset" data-side="verso">Reinitialiser</button>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;

            if (engravingMode !== 'text') {
                initEngravingImageEditors(
                    product.id,
                    selectedComponent ? selectedComponent.image_url : '',
                    selectedComponent ? selectedComponent.shape_identifier : ''
                );
            }

            renderSidebarFooter(product);
        })
        .catch(error => {
            console.error('Erreur lors du chargement des composants:', error);
            content.innerHTML = `<div class="alert alert-danger">Erreur: Impossible de charger les composants</div>`;
        });
}

function setSidebarComponent(productId, componentId) {
    const custom = productCustomizations[productId];
    if (!custom) return;
    custom.choices.studio_component = String(componentId);
    if (custom._components_map && custom._components_map[String(componentId)]) {
        custom.choices.studio_component_label = custom._components_map[String(componentId)].name || '';
    }
    renderEngravingUI(products.find(p => p.id === productId));
}

function initEngravingImageEditors(productId, componentImageUrl, shapeIdentifier) {
    ['recto', 'verso'].forEach(side => {
        const input = document.querySelector(`.engraving-image-input[data-side="${side}"]`);
        const zoom = document.querySelector(`.engraving-zoom[data-side="${side}"]`);
        const resetBtn = document.querySelector(`.engraving-reset[data-side="${side}"]`);
        const canvas = document.getElementById(`engravingCanvas-${side}`);
        if (!input || !zoom || !canvas) return;

        const custom = productCustomizations[productId];
        if (!custom || !custom.choices || !custom.choices[side]) return;

        zoom.value = custom.choices[side].image_scale || 1;

        input.addEventListener('change', () => {
            const file = input.files && input.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (e) => {
                custom.choices[side].image_data = e.target.result;
                custom.choices[side].image_scale = 1;
                custom.choices[side].image_x = 0;
                custom.choices[side].image_y = 0;
                renderEngravingCanvas(productId, side, componentImageUrl, shapeIdentifier);
            };
            reader.readAsDataURL(file);
        });

        zoom.addEventListener('input', () => {
            custom.choices[side].image_scale = parseFloat(zoom.value) || 1;
            renderEngravingCanvas(productId, side, componentImageUrl, shapeIdentifier);
        });

        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                custom.choices[side].image_scale = 1;
                custom.choices[side].image_x = 0;
                custom.choices[side].image_y = 0;
                zoom.value = 1;
                renderEngravingCanvas(productId, side, componentImageUrl, shapeIdentifier);
            });
        }

        let isDragging = false;
        let lastX = 0;
        let lastY = 0;

        canvas.addEventListener('mousedown', (e) => {
            if (!custom.choices[side].image_data) return;
            isDragging = true;
            lastX = e.clientX;
            lastY = e.clientY;
        });
        window.addEventListener('mouseup', () => { isDragging = false; });
        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = e.clientX - lastX;
            const dy = e.clientY - lastY;
            lastX = e.clientX;
            lastY = e.clientY;
            custom.choices[side].image_x += dx;
            custom.choices[side].image_y += dy;
            renderEngravingCanvas(productId, side, componentImageUrl, shapeIdentifier);
        });

        renderEngravingCanvas(productId, side, componentImageUrl, shapeIdentifier);
    });
}


function renderEngravingCanvas(productId, side, componentImageUrl, shapeIdentifier) {
    const custom = productCustomizations[productId];
    if (!custom || !custom.choices || !custom.choices[side]) return;
    const canvas = document.getElementById(`engravingCanvas-${side}`);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    // Clear to transparent
    ctx.clearRect(0, 0, w, h);

    const dataUrl = custom.choices[side].image_data;
    if (!dataUrl) {
        custom.choices[side].image_preview = '';
        const previewImg = document.getElementById(`engravingPhotoPreview-${side}`);
        if (previewImg) previewImg.style.opacity = '0';
        drawOverlayGuide(ctx, shapeIdentifier, w, h);
        return;
    }

    const scale = custom.choices[side].image_scale || 1;
    const offsetX = custom.choices[side].image_x || 0;
    const offsetY = custom.choices[side].image_y || 0;

    const userImg = new Image();
    userImg.onload = () => {
        // We use a temporary canvas for better masking results
        const maskCanvas = document.createElement('canvas');
        maskCanvas.width = w;
        maskCanvas.height = h;
        const mctx = maskCanvas.getContext('2d');

        // Draw the shape on mask canvas
        applyShapePath(mctx, shapeIdentifier, w, h, 1);
        mctx.fillStyle = 'black';
        mctx.fill();

        // Final Composition
        ctx.save();

        // 1. Position and draw user image
        const baseScale = Math.min(w / userImg.width, h / userImg.height);
        const drawW = userImg.width * baseScale * scale;
        const drawH = userImg.height * baseScale * scale;
        const x = (w - drawW) / 2 + offsetX;
        const y = (h - drawH) / 2 + offsetY;

        ctx.filter = 'contrast(1.3) grayscale(1) brightness(0.95)';
        ctx.drawImage(userImg, x, y, drawW, drawH);
        ctx.filter = 'none';

        // 2. Apply the Mask using destination-in
        ctx.globalCompositeOperation = 'destination-in';
        ctx.drawImage(maskCanvas, 0, 0);

        // 3. Reset operation to draw overlay
        ctx.globalCompositeOperation = 'source-over';

        // 4. Subtle inner shadow for realism
        ctx.strokeStyle = 'rgba(0,0,0,0.15)';
        ctx.lineWidth = 2;
        applyShapePath(ctx, shapeIdentifier, w, h, 1);
        ctx.stroke();

        ctx.restore();

        const finalizePreview = () => {
            const dataUrl = canvas.toDataURL('image/png');
            custom.choices[side].image_preview = dataUrl;

            // Update SVG preview if side is recto
            if (side === 'recto') {
                const svgPhoto = document.getElementById('engravingPhotoPreview-recto-svg');
                if (svgPhoto) {
                    svgPhoto.setAttribute('href', dataUrl);
                    svgPhoto.style.opacity = '1';
                }
            }
        };


        drawOverlayGuide(ctx, shapeIdentifier, w, h);
        finalizePreview();
    };
    userImg.src = dataUrl;
}


function applyShapePath(ctx, shapeIdentifier, w, h, scale_factor = 1) {
    const shape = (shapeIdentifier || '').toLowerCase();
    const midX = w / 2;
    const midY = h / 2;

    ctx.beginPath();

    // Support for various shapes based on keywords
    if (shape.includes('heart') || shape.includes('coeur')) {
        const size = Math.min(w, h) * 0.4 * scale_factor;
        ctx.moveTo(midX, midY + size * 0.6);
        ctx.bezierCurveTo(midX + size, midY + size * 0.1, midX + size * 0.9, midY - size * 0.9, midX, midY - size * 0.35);
        ctx.bezierCurveTo(midX - size * 0.9, midY - size * 0.9, midX - size, midY + size * 0.1, midX, midY + size * 0.6);
    } else if (shape.includes('cross') || shape.includes('croix')) {
        const s = Math.min(w, h) * 0.6 * scale_factor;
        const bar = s * 0.25;
        ctx.rect(midX - bar / 2, midY - s / 2, bar, s);
        ctx.rect(midX - s / 2, midY - bar * 0.8, s, bar);
    } else if (shape.includes('africa') || shape.includes('afrique') || shape.includes('continent')) {
        // Simple artistic approximation of Africa continent
        const s = Math.min(w, h) * 0.35 * scale_factor;
        ctx.moveTo(midX - s * 0.8, midY - s);
        ctx.bezierCurveTo(midX + s, midY - s * 1.5, midX + s * 1.2, midY + s * 0.5, midX + s * 0.5, midY + s);
        ctx.bezierCurveTo(midX, midY + s * 1.5, midX - s * 0.5, midY + s, midX - s, midY + s * 0.5);
        ctx.bezierCurveTo(midX - s * 1.2, midY, midX - s * 0.8, midY - s, midX - s * 0.8, midY - s);
    } else if (shape.includes('dog') || shape.includes('tag') || shape.includes('plaque')) {
        const rw = w * 0.6 * scale_factor;
        const rh = h * 0.8 * scale_factor;
        roundRectPath(ctx, (w - rw) / 2, (h - rh) / 2, rw, rh, 15);
    } else if (shape.includes('bar') || shape.includes('ligne')) {
        const rw = w * 0.85 * scale_factor;
        const rh = h * 0.25 * scale_factor;
        roundRectPath(ctx, (w - rw) / 2, (h - rh) / 2, rw, rh, rh / 2);
    } else {
        // FAILSAFE: Circle for any other medallion
        const r = Math.min(w, h) * 0.42 * scale_factor;
        ctx.arc(midX, midY, r, 0, Math.PI * 2);
    }
    ctx.closePath();
}


function drawOverlayGuide(ctx, shapeIdentifier, w, h) {
    ctx.save();
    ctx.globalAlpha = 0.4;
    ctx.strokeStyle = '#b11226';
    ctx.setLineDash([5, 5]); // Dashed line for guide
    ctx.lineWidth = 2;
    applyShapePath(ctx, shapeIdentifier, w, h, 1);
    ctx.stroke();
    ctx.restore();
}


function drawEngravingMask(ctx, shapeIdentifier, w, h) {
    applyShapePath(ctx, shapeIdentifier, w, h, 1);
    ctx.save();
    ctx.fillStyle = '#000';
    ctx.fill();
    ctx.restore();
}


function roundRectPath(ctx, x, y, w, h, r) {
    const radius = Math.min(r, w / 2, h / 2);
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + w - radius, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
    ctx.lineTo(x + w, y + h - radius);
    ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
    ctx.lineTo(x + radius, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
}

function toggleEngravingSection(productId, side) {
    const custom = productCustomizations[productId];
    // Toggle active state
    custom.choices[side].active = !custom.choices[side].active;

    // Re-render to update UI classes (simple way)
    renderEngravingUI(products.find(p => p.id === productId));
}

function updateEngravingField(productId, side, field, value) {
    const custom = productCustomizations[productId];
    custom.choices[side][field] = value;

    // Update SVG Text Overlay
    if (side === 'recto') {
        const textSVG = document.getElementById('previewTextSVG');
        if (textSVG) {
            textSVG.textContent = custom.choices[side].text;
            textSVG.style.fontFamily = custom.choices[side].font;
            textSVG.style.opacity = custom.choices[side].text ? 1 : 0;
        }
    }

    // Update local char counters...

    if (field === 'text') {
        // Find specific input parent to update counter
        // For simplicity, just re-render or find element:
        // Trying to avoid focus loss on input, so DO NOT re-render the whole UI on text input
        const activeSection = document.getElementById(`section-${side}`);
        const counter = activeSection.querySelector('.char-counter');
        if (counter) counter.innerText = `${value.length} / 15`;
    }

    if (field === 'font') {
        // Force re-render to update font preview box
        renderEngravingUI(products.find(p => p.id === productId));
    }
}

function renderSidebarFooter(product) {
    const footerPrice = document.getElementById('sidebarTotal');
    const footerBtn = document.getElementById('sidebarAddBtn');
    if (!footerPrice || !footerBtn) return;

    const custom = productCustomizations[product.id];
    let priceHTML = '';
    const unitPrice = calculateTotalPrice(product);
    const qty = custom ? custom.quantity : 1;
    const total = unitPrice * qty;

    if (custom && (custom.choices?.recto?.active || custom.choices?.verso?.active)) {
        const basePrice = product.selling_price || product.price || 0;
        const engravingPrice = parseFloat(product.engraving_price) || 0;
        priceHTML = `
            <div style="font-size: 0.8rem; color: #666; margin-bottom: 2px;">
                ${basePrice.toLocaleString()} + Gravure ${engravingPrice.toLocaleString()} FC
            </div>
            <div style="font-weight: 700; font-size: 1.25rem;">${total.toLocaleString()} FC</div>
        `;
    } else {
        priceHTML = `<div style="font-weight: 700; font-size: 1.25rem;">${total.toLocaleString()} FC</div>`;
    }

    footerPrice.innerHTML = priceHTML;

    // Also update top price if it exists
    const topPrice = document.getElementById('sidebarTopPrice');
    if (topPrice) topPrice.innerText = total.toLocaleString() + ' FC';

    // Update button action
    footerBtn.onclick = () => addToCart(product.id);
}


/* --- PREMIUM UI HELPERS --- */

function toggleWishlist(productId, btnElement) {
    // Toggle class
    btnElement.classList.toggle('active'); // active usually means filled red in CSS if defined

    // Animate
    const icon = btnElement.querySelector('i');
    if (icon) {
        if (btnElement.classList.contains('active')) {
            icon.classList.remove('bi-heart');
            icon.classList.add('bi-heart-fill');
            icon.style.color = '#E21717';
        } else {
            icon.classList.add('bi-heart');
            icon.classList.remove('bi-heart-fill');
            icon.style.color = '';
        }
    }
}

// Enhance addToCart to include Flying Animation
const originalAddToCart = addToCart;
addToCart = async function (productId) {
    // Run animation
    try {
        // Find product image
        let img = null;
        // Try sidebar image first
        const sidebarImg = document.getElementById('sidebarPreviewImg');
        if (sidebarImg && document.querySelector('.product-sidebar.active')) {
            img = sidebarImg;
        } else {
            // Find in grid
            const card = document.querySelector(`.product-card[data-id="${productId}"]`);
            if (card) img = card.querySelector('img');
        }

        if (img) {
            runFlyAnimation(img);
        }
    } catch (e) { console.error(e); }

    // Call original
    await originalAddToCart(productId);
};

function runFlyAnimation(sourceImg) {
    const cartIcon = document.querySelector('.cart-toggle-btn') || document.querySelector('.cart-icon-desktop') || document.getElementById('cartBadge');
    if (!cartIcon) return;

    const flyImg = sourceImg.cloneNode();
    flyImg.classList.add('fly-item');

    const rect = sourceImg.getBoundingClientRect();
    const targetRect = cartIcon.getBoundingClientRect();

    flyImg.style.left = rect.left + 'px';
    flyImg.style.top = rect.top + 'px';
    flyImg.style.width = rect.width + 'px';
    flyImg.style.height = rect.height + 'px';
    flyImg.style.position = 'fixed';
    flyImg.style.zIndex = '10000';
    flyImg.style.borderRadius = '50%';
    flyImg.style.opacity = '1';
    flyImg.style.transition = 'all 0.8s cubic-bezier(0.2, 1, 0.3, 1)';

    document.body.appendChild(flyImg);

    // Force reflow
    flyImg.getBoundingClientRect();

    setTimeout(() => {
        flyImg.style.left = (targetRect.left + 10) + 'px';
        flyImg.style.top = (targetRect.top + 10) + 'px';
        flyImg.style.width = '30px';
        flyImg.style.height = '30px';
        flyImg.style.opacity = '0';
    }, 50);

    setTimeout(() => {
        flyImg.remove();
        // Shake cart
        cartIcon.classList.add('shake-anim'); // Ensure CSS exists or inline it
        setTimeout(() => cartIcon.classList.remove('shake-anim'), 500);
    }, 850);
}

function getShapeSVGPath(shapeLabel, w, h) {
    const shape = (shapeLabel || '').toLowerCase();
    const midX = w / 2;
    const midY = h / 2;

    if (shape.includes('heart') || shape.includes('coeur')) {
        const s = 140;
        return `<path d="M ${midX} ${midY + s * 0.6} C ${midX + s} ${midY + s * 0.1} ${midX + s * 0.9} ${midY - s * 0.9} ${midX} ${midY - s * 0.35} C ${midX - s * 0.9} ${midY - s * 0.9} ${midX - s} ${midY + s * 0.1} ${midX} ${midY + s * 0.6} Z" />`;
    } else if (shape.includes('cross') || shape.includes('croix')) {
        return `<path d="M ${midX - 25} ${midY - 110} h 50 v 220 h -50 Z M ${midX - 110} ${midY - 25} v 50 h 220 v -50 Z" />`;
    } else if (shape.includes('africa') || shape.includes('afrique')) {
        return `<path d="M ${midX - 70} ${midY - 90} Q ${midX + 90} ${midY - 130} ${midX + 110} ${midY + 40} Q ${midX + 40} ${midY + 130} ${midX - 20} ${midY + 110} Q ${midX - 90} ${midY + 40} ${midX - 70} ${midY - 90}" />`;
    } else if (shape.includes('militaire') || shape.includes('med') || shape.includes('plaque')) {
        // Dog Tag / Militaire shape
        return `<rect x="${midX - 80}" y="${midY - 110}" width="160" height="220" rx="40" ry="40" />`;
    }
    // Default: Circle
    return `<circle cx="${midX}" cy="${midY}" r="130" />`;
}


/**
 * HEADLESS MOCKUP COMPOSITOR
 * Generates a full product mockup from customization state without requiring the sidebar to be open.
 * This ensures perfect mockups are captured for the order console regardless of UI state.
 */
async function generateHeadlessMockup(product, customizationState) {
    return new Promise(async (resolve, reject) => {
        try {
            const width = 400;
            const height = 400;
            const canvas = document.createElement('canvas');
            canvas.width = width * 2; // High DPI
            canvas.height = height * 2;
            const ctx = canvas.getContext('2d');
            ctx.scale(2, 2);

            // 1. Extract customization data
            const choices = customizationState.choices || {};
            const componentId = choices.studio_component;
            const rectoData = choices.recto || {};

            // Find the selected component to get its image and shape
            let componentImage = null;
            let shapeLabel = 'circle';

            if (componentId && typeof components !== 'undefined') {
                const comp = components.find(c => String(c.id) === String(componentId));
                if (comp) {
                    componentImage = comp.image_url;
                    shapeLabel = comp.shape || comp.name || 'circle';
                }
            }

            // Get photo and text from customization
            const photoUrl = rectoData.image_preview || rectoData.image_data || rectoData.url || null;
            const textStr = rectoData.text || '';
            const textFont = rectoData.font || 'Arial';

            console.log("Headless Compositor:", { componentImage, shapeLabel, photoUrl, textStr });

            // 2. Load images
            const loadImage = (url) => new Promise((res) => {
                if (!url || url === "") return res(null);
                const img = new Image();
                img.crossOrigin = "anonymous";
                img.onload = () => res(img);
                img.onerror = () => {
                    console.warn("Headless: Failed to load image", url);
                    res(null);
                };
                img.src = url;
            });

            const [photoImg, bgImg] = await Promise.all([
                loadImage(photoUrl),
                loadImage(componentImage)
            ]);

            // 3. Clear Canvas (white background)
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, width, height);

            // 4. Layer 1: Draw Custom Photo with Mask & Filters
            if (photoImg) {
                ctx.save();
                applyCanvasShapeMask(ctx, shapeLabel, width, height);
                ctx.clip();

                // Apply filters matching the SVG preview
                ctx.filter = 'contrast(1.1) grayscale(1)';

                // Match SVG transform and positioning
                ctx.translate(0, 25);
                ctx.drawImage(photoImg, 100, 100, 200, 200);
                ctx.restore();
            }

            // 5. Layer 2: Draw Product Texture (Multiply Mode) - THE CRITICAL FIX
            if (bgImg) {
                ctx.save();
                ctx.globalCompositeOperation = 'multiply';
                ctx.drawImage(bgImg, 0, 0, width, height);
                ctx.restore();
            }

            // 6. Layer 3: Draw Text Overlay
            if (textStr) {
                ctx.save();
                ctx.fillStyle = "#111";
                ctx.font = `500 20px "${textFont}"`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(textStr, width / 2, height * 0.6);
                ctx.restore();
            }

            console.log("✅ Headless mockup composite complete");
            resolve(canvas.toDataURL('image/png'));
        } catch (e) {
            console.error("❌ Headless compositor fatal error:", e);
            reject(e);
        }
    });
}


/**
 * ROBUST SVG CAPTURE: Converts all images to Base64 before rendering.
 * This ensures the background image (medallion/chain) is ALWAYS captured, avoiding CORS issues.
 */
async function captureSVGToDataURL(svg) {
    return new Promise(async (resolve, reject) => {
        try {
            const width = 400;
            const height = 400;

            // 1. Clone the SVG to avoid modifying the live UI
            const clone = svg.cloneNode(true);

            // 2. Convert ALL images to Base64 to avoid CORS issues
            const images = clone.querySelectorAll('image');
            const imageConversionPromises = Array.from(images).map(async (img) => {
                const href = img.getAttribute('href') || img.getAttribute('xlink:href');
                if (!href || href.startsWith('data:')) return; // Already Base64 or empty

                try {
                    // Fetch and convert to Base64
                    const response = await fetch(href);
                    const blob = await response.blob();
                    const base64 = await new Promise((res) => {
                        const reader = new FileReader();
                        reader.onloadend = () => res(reader.result);
                        reader.readAsDataURL(blob);
                    });

                    // Update the image element
                    img.setAttribute('href', base64);
                    img.removeAttribute('xlink:href');
                    console.log("✅ Converted image to Base64:", href.substring(0, 50));
                } catch (err) {
                    console.warn("⚠️ Failed to convert image to Base64:", href, err);
                }
            });

            // Wait for all images to be converted
            await Promise.all(imageConversionPromises);

            // 3. Serialize the SVG
            const serializer = new XMLSerializer();
            let svgString = serializer.serializeToString(clone);

            // Ensure proper namespaces
            if (!svgString.includes('xmlns="http://www.w3.org/2000/svg"')) {
                svgString = svgString.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
            }
            if (!svgString.includes('xmlns:xlink')) {
                svgString = svgString.replace('<svg', '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
            }

            // 4. Create a high-resolution canvas
            const canvas = document.createElement('canvas');
            canvas.width = width * 2; // High DPI
            canvas.height = height * 2;
            const ctx = canvas.getContext('2d');
            ctx.scale(2, 2);

            // 5. Render SVG to canvas via Image
            const img = new Image();
            const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);

            img.onload = () => {
                // White background
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, width, height);

                // Draw the complete SVG
                ctx.drawImage(img, 0, 0, width, height);

                // Clean up and resolve
                URL.revokeObjectURL(url);
                resolve(canvas.toDataURL('image/png'));
            };

            img.onerror = (err) => {
                URL.revokeObjectURL(url);
                console.error("SVG rendering failed:", err);
                reject(new Error("Failed to render SVG to canvas"));
            };

            img.src = url;

        } catch (e) {
            console.error("SVG capture error:", e);
            reject(e);
        }
    });
}

/**
 * HELPER: Applies a clipping path to the context matching the store's SVG shapes.
 */
function applyCanvasShapeMask(ctx, shapeLabel, w, h) {
    const shape = (shapeLabel || '').toLowerCase();
    const midX = w / 2;
    const midY = h / 2;
    ctx.beginPath();

    if (shape.includes('heart') || shape.includes('coeur')) {
        const s = 140;
        ctx.moveTo(midX, midY + s * 0.6);
        ctx.bezierCurveTo(midX + s, midY + s * 0.1, midX + s * 0.9, midY - s * 0.9, midX, midY - s * 0.35);
        ctx.bezierCurveTo(midX - s * 0.9, midY - s * 0.9, midX - s, midY + s * 0.1, midX, midY + s * 0.6);
    } else if (shape.includes('cross') || shape.includes('croix')) {
        // Double rectangle cross
        ctx.rect(midX - 25, midY - 110, 50, 220);
        ctx.rect(midX - 110, midY - 25, 220, 50);
    } else if (shape.includes('africa') || shape.includes('afrique')) {
        ctx.moveTo(midX - 70, midY - 90);
        ctx.quadraticCurveTo(midX + 90, midY - 130, midX + 110, midY + 40);
        ctx.quadraticCurveTo(midX + 40, midY + 130, midX - 20, midY + 110);
        ctx.quadraticCurveTo(midX - 90, midY + 40, midX - 70, midY - 90);
    } else if (shape.includes('militaire') || shape.includes('med') || shape.includes('plaque')) {
        // Dog Tag Shape: Rounded Rectangle
        const w_tag = 160;
        const h_tag = 220;
        const radius = 40;
        const x = midX - w_tag / 2;
        const y = midY - h_tag / 2;
        ctx.roundRect(x, y, w_tag, h_tag, radius);
    } else {
        // Default: Product Circle
        ctx.arc(midX, midY, 130, 0, Math.PI * 2);
    }
    ctx.closePath();
}
