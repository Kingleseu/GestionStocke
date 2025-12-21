// Data - Injected from Django
const products = window.djangoProducts || [];
let adminSettings = window.storeSettings || {
    deliveryPrice: 5.99,
    freeShippingThreshold: 100,
    taxRate: 0.2,
    bannerText: '🎁 Free shipping on orders over €100',
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

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    const preloader = document.getElementById('premiumPreloader');

    // Smooth Preloader Removal
    window.addEventListener('load', () => {
        setTimeout(() => {
            if (preloader) preloader.classList.add('fade-out');
            if (typeof initPremiumAnimations === 'function') initPremiumAnimations();
        }, 800);
    });

    initSiteContent();
    renderFeaturedProducts();
    renderCatalogueProducts();
    renderProductsTable();
    renderTopProducts();
    updateCartUI();

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

function toggleProductCard(productId) {
    if (expandedCardId === productId) {
        closeExpandedCard();
        return;
    }

    // Close any existing
    if (expandedCardId) {
        closeExpandedCard();
    }

    const originalCard = document.querySelector(`.product-card[data-id="${productId}"]`);
    if (!originalCard) return;

    expandedCardId = productId;

    // Create logic for customization state if missing
    if (!productCustomizations[productId]) {
        const product = products.find(p => p.id === productId);
        productCustomizations[productId] = {
            engraving: '',
            material: product.material,
            size: '',
            quantity: 1,
            uploadedImage: null,
            message: ''
        };
    }

    // 1. Get Rect
    const rect = originalCard.getBoundingClientRect();
    const scrollTop = window.scrollY;

    // 2. Create Clone/Overlay
    // We render the card content AGAIN but wrapped in the overlay class
    // We add the form immediately
    const product = products.find(p => p.id === productId);
    const innerHTML = createProductCardContent(product, true); // true = expanded/with form

    const overlay = document.createElement('div');
    overlay.className = 'product-card-overlay';
    overlay.id = 'activeOverlayCard';
    overlay.innerHTML = innerHTML;

    // 3. Position initially exactly over original
    overlay.style.position = 'absolute';
    overlay.style.top = (rect.top + scrollTop) + 'px';
    overlay.style.left = rect.left + 'px';
    overlay.style.width = rect.width + 'px';
    overlay.style.height = rect.height + 'px'; // Start with same height
    overlay.dataset.id = productId;

    document.body.appendChild(overlay);

    // 4. Force reflow
    overlay.getBoundingClientRect();

    // 5. Expand
    // Calculate expected expanded height or let it auto? Auto is tricky with transitions.
    // Better: let it be 'auto' height but animate min-height or max-height?
    // Transitioning width/scaling is easier.

    overlay.classList.add('active');

    // Make it pop out - slightly wider and auto height
    overlay.style.width = (rect.width * 1.05) + 'px';
    overlay.style.height = 'auto';
    overlay.style.zIndex = '9999';
    // Center it slightly if scaling width
    overlay.style.left = (rect.left - (rect.width * 0.025)) + 'px';

    // Ensure it doesn't go off screen
    // (Optional bounding box checks here)

    // Listen for click outside
    setTimeout(() => {
        document.addEventListener('click', handleOverlayClickOutside);
    }, 50);
}

function handleOverlayClickOutside(e) {
    const overlay = document.getElementById('activeOverlayCard');
    if (overlay && !overlay.contains(e.target)) {
        closeExpandedCard();
    }
}

function closeExpandedCard() {
    if (!expandedCardId) return;

    const overlay = document.getElementById('activeOverlayCard');
    if (overlay) {
        // Animate back? Or just remove for speed/native feel as per 'quick interactions'
        overlay.remove();
    }

    expandedCardId = null;
    document.removeEventListener('click', handleOverlayClickOutside);
}

// Separate content generation from the wrapper
function createProductCard(product) {
    // Standard grid card (never expanded inline)
    return `
        <div class="product-card" data-id="${product.id}">
            ${createProductCardContent(product, false)}
        </div>
    `;
}

function createProductCardContent(product, isExpanded) {
    const badgeClass = product.badge ? `badge-${product.badge.toLowerCase()}` : '';
    const customization = productCustomizations[product.id] || {
        engraving: '',
        material: product.material,
        size: '',
        quantity: 1,
        uploadedImage: null,
        message: ''
    };

    return `
        <div class="product-image" onclick="${!isExpanded ? `event.stopPropagation(); toggleProductCard('${product.id}')` : ''}">
            <img src="${product.image}" alt="${product.name}">
            ${product.badge ? `<div class="product-badge ${badgeClass}">${product.badge}</div>` : ''}
            <button class="favorite-btn" onclick="event.stopPropagation(); toggleFavorite('${product.id}')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
            </button>
            ${product.stock < 10 ? `<div class="stock-badge">Plus que ${product.stock} en stock</div>` : ''}
        </div>
        <div class="product-info">
            <h3>${product.name}</h3>
            <p class="product-meta">${product.material} • ${product.category}</p>
            <div class="product-footer">
                <p class="product-price">€${product.price ? product.price.toLocaleString() : '0'}</p>
                ${product.customizable ? '<span class="customizable-badge">Personnalisable</span>' : ''}
            </div>
            ${!isExpanded ? `
                <button class="product-btn" onclick="event.stopPropagation(); toggleProductCard('${product.id}')">
                    ${product.customizable ? 'Personnaliser' : 'Ajouter au panier'}
                </button>
            ` : ''}
        </div>
        ${isExpanded ? `
            <div class="customization-form" onclick="event.stopPropagation()">
                <div class="form-header">
                    <h4>Personnalisation</h4>
                    <button class="close-form-btn" onclick="closeExpandedCard()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                ${product.customizable ? `
                    <div class="form-field">
                        <label>Gravure personnalisée</label>
                        <input type="text" value="${customization.engraving}" 
                               placeholder="Ex: Initiales, date..." maxlength="30" 
                               oninput="updateCustomization('${product.id}', 'engraving', this.value)">
                    </div>
                    
                    <!-- NEW: Message -->
                    <div class="form-field">
                         <label>Message (Optionnel)</label>
                         <textarea rows="2" placeholder="Un petit mot doux..." 
                                   oninput="updateCustomization('${product.id}', 'message', this.value)">${customization.message || ''}</textarea>
                    </div>

                    <!-- NEW: File Upload (Mock) -->
                     <div class="form-field">
                        <label>Photo à graver (Optionnel)</label>
                        <div class="upload-area" onclick="document.getElementById('file-${product.id}').click()">
                            ${customization.uploadedImage ?
                    `<div class="upload-preview">
                                    <img src="${customization.uploadedImage}" alt="Preview">
                                    <span class="remove-upload" onclick="event.stopPropagation(); updateCustomization('${product.id}', 'uploadedImage', null)">×</span>
                                 </div>` :
                    `<span>Cliquez pour ajouter une photo</span>`
                }
                        </div>
                        <input type="file" id="file-${product.id}" hidden accept="image/*" 
                               onchange="handleImageUpload('${product.id}', this)">
                    </div>

                     <div class="form-field">
                        <label>Matière</label>
                        <div class="material-selector">
                            ${['Or', 'Argent', 'Or rose'].map(mat => `
                                <button class="material-btn ${customization.material === mat ? 'active' : ''}" 
                                        onclick="updateCustomization('${product.id}', 'material', '${mat}')">
                                    ${mat}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                    <div class="form-field">
                        <label>Taille</label>
                        <select onchange="updateCustomization('${product.id}', 'size', this.value)">
                            <option value="">Sélectionner une taille</option>
                            <option value="S" ${customization.size === 'S' ? 'selected' : ''}>S (50mm)</option>
                            <option value="M" ${customization.size === 'M' ? 'selected' : ''}>M (55mm)</option>
                            <option value="L" ${customization.size === 'L' ? 'selected' : ''}>L (60mm)</option>
                            <option value="XL" ${customization.size === 'XL' ? 'selected' : ''}>XL (65mm)</option>
                        </select>
                    </div>
                ` : ''}
                <div class="form-field">
                    <label>Quantité</label>
                    <div class="quantity-controls">
                        <button class="qty-btn" onclick="updateQuantity('${product.id}', -1)">−</button>
                        <input type="number" class="qty-input" value="${customization.quantity}" 
                               min="1" max="${product.stock}" readonly>
                        <button class="qty-btn" onclick="updateQuantity('${product.id}', 1)">+</button>
                    </div>
                </div>
                <button class="add-to-cart-btn ${isCustomizationComplete(product) ? '' : 'disabled'}" 
                        onclick="addToCart('${product.id}')" 
                        ${isCustomizationComplete(product) ? '' : 'disabled'}>
                    Ajouter au panier • €${(product.price * customization.quantity).toLocaleString()}
                </button>
            </div>
        ` : ''}
    `;
}

function toggleFavorite(productId) {
    const btn = event.target.closest('.favorite-btn');
    btn.classList.toggle('liked');
}

function updateCustomization(productId, field, value) {
    if (!productCustomizations[productId]) {
        const product = products.find(p => p.id === productId);
        productCustomizations[productId] = {
            engraving: '',
            material: product.material,
            size: '',
            quantity: 1,
            uploadedImage: null
        };
    }
    productCustomizations[productId][field] = value;
    renderCatalogueProducts();
    renderFeaturedProducts();
}

function updateQuantity(productId, delta) {
    const custom = productCustomizations[productId];
    const product = products.find(p => p.id === productId);
    if (!custom) return;

    // Check real stock
    const newQty = Math.max(1, Math.min(product.stock, custom.quantity + delta));
    custom.quantity = newQty;

    // Rerender ONLY the overlay if active, otherwise the entire grid? 
    // Optimization: find the active overlay and only update its contents
    if (expandedCardId === productId) {
        updateOverlayContent(productId);
    } else {
        renderCatalogueProducts();
        renderFeaturedProducts();
    }
}

function handleImageUpload(productId, input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            updateCustomization(productId, 'uploadedImage', e.target.result);
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Helper to update just the overlay content to avoid full re-render/flicker
function updateOverlayContent(productId) {
    const overlay = document.getElementById('activeOverlayCard');
    if (!overlay) return;

    const product = products.find(p => p.id === productId);
    // Reuse the content generator
    const innerHTML = createProductCardContent(product, true);
    overlay.innerHTML = innerHTML;
}

// Override updateCustomization to use efficient update
function updateCustomization(productId, field, value) {
    if (!productCustomizations[productId]) {
        const product = products.find(p => p.id === productId);
        productCustomizations[productId] = {
            engraving: '',
            material: product.material,
            size: '',
            quantity: 1,
            uploadedImage: null,
            message: ''
        };
    }
    productCustomizations[productId][field] = value;

    if (expandedCardId === productId) {
        updateOverlayContent(productId);
    } else {
        renderCatalogueProducts();
        renderFeaturedProducts();
    }
}

// Cart Functions
function addToCart(productId) {
    const product = products.find(p => p.id === productId);
    const custom = productCustomizations[productId];

    const cartItem = {
        id: Date.now().toString(),
        productId: productId,
        name: product.name,
        price: product.price,
        image: product.image,
        quantity: custom.quantity,
        customization: product.customizable ? {
            engraving: custom.engraving,
            material: custom.material,
            size: custom.size,
            uploadedImage: custom.uploadedImage,
            message: custom.message
        } : null
    };

    cart.push(cartItem);
    updateCartUI();
    closeExpandedCard();
    saveCart();

    // Reset customization
    productCustomizations[productId] = {
        engraving: '',
        material: product.material,
        size: '',
        quantity: 1,
        uploadedImage: null
    };

    toggleCart();
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
                    ${item.customization ? `
                        <div class="cart-item-customization">
                            ${item.customization.uploadedImage ? `<div style="margin-bottom:4px;"><img src="${item.customization.uploadedImage}" style="width:30px;height:30px;object-fit:cover;border-radius:4px;border:1px solid #ddd;"></div>` : ''}
                            ${item.customization.engraving ? `<p>Gravure: "${item.customization.engraving}"</p>` : ''}
                            ${item.customization.message ? `<p>Message: "${item.customization.message}"</p>` : ''}
                            ${item.customization.material ? `<p>Matière: ${item.customization.material}</p>` : ''}
                            ${item.customization.size ? `<p>Taille: ${item.customization.size}</p>` : ''}
                        </div>
                    ` : ''}
                    <div class="cart-item-footer">
                        <div class="cart-item-controls">
                            <button class="cart-qty-btn" onclick="updateCartQuantity('${item.id}', -1)">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="5" y1="12" x2="19" y2="12"></line>
                                </svg>
                            </button>
                            <span class="cart-item-qty">${item.quantity}</span>
                            <button class="cart-qty-btn" onclick="updateCartQuantity('${item.id}', 1)">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="12" y1="5" x2="12" y2="19"></line>
                                    <line x1="5" y1="12" x2="19" y2="12"></line>
                                </svg>
                            </button>
                        </div>
                        <p class="cart-item-price">€${(item.price * item.quantity).toLocaleString()}</p>
                    </div>
                </div>
            </div>
        `).join('');

        cartFooter.style.display = 'block';
        updateCartSummary();
    }
}

function updateCartSummary() {
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const deliveryFee = subtotal >= adminSettings.freeShippingThreshold ? 0 : adminSettings.deliveryPrice;
    const tax = subtotal * adminSettings.taxRate;
    const total = subtotal + deliveryFee + tax;

    document.getElementById('cartSubtotal').textContent = `€${subtotal.toFixed(2)}`;
    const deliveryEl = document.getElementById('cartDelivery');
    if (deliveryEl) {
        deliveryEl.innerHTML = deliveryFee === 0
            ? '<span class="free-delivery">Gratuit</span>'
            : `€${deliveryFee.toFixed(2)}`;
    }
    document.getElementById('cartTax').textContent = `€${tax.toFixed(2)}`;
    document.getElementById('cartTotal').textContent = `€${total.toFixed(2)}`;
}

function toggleCart() {
    const drawer = document.getElementById('cartDrawer');
    if (drawer) drawer.classList.toggle('active');
}

// Checkout Logic - Added for Django Integration
async function proceedToCheckout() {
    if (cart.length === 0) return;

    const checkoutBtn = document.querySelector('.checkout-btn');
    const originalText = checkoutBtn.innerHTML;
    checkoutBtn.innerHTML = 'Traitement...';
    checkoutBtn.disabled = true;

    // Force sync before verify
    await saveCart();

    // Check sync status or trust persistence
    // In our simplified flow, we assume saveCart worked or we try again.
    // Wait a bit to ensure session write if async
    // Actually saveCart uses fetch await, so it's done.

    showView('checkout');
    checkoutBtn.innerHTML = originalText;
    checkoutBtn.disabled = false;
}

function renderCheckoutSummary() {
    const list = document.getElementById('checkoutOrderItems');
    if (!list) return;

    list.innerHTML = cart.map(item => `
        <div class="order-item">
            <div class="order-item-image">
                <img src="${item.image}" alt="${item.name}">
                <span class="item-qty-badge">${item.quantity}</span>
            </div>
            <div class="order-item-details">
                <h4>${item.name}</h4>
                <p>${item.customization ? (item.customization.material || 'Standard') : 'Standard'}</p>
            </div>
            <div class="order-item-price">
                €${(item.price * item.quantity).toLocaleString()}
            </div>
        </div>
    `).join('');

    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const deliveryFee = subtotal >= adminSettings.freeShippingThreshold ? 0 : adminSettings.deliveryPrice;
    const tax = subtotal * adminSettings.taxRate;
    const total = subtotal + deliveryFee + tax;

    const subEl = document.getElementById('checkoutSubtotal');
    if (subEl) subEl.textContent = `€${subtotal.toFixed(2)}`;

    const delEl = document.getElementById('checkoutDelivery');
    if (delEl) delEl.innerHTML = deliveryFee === 0 ? '<span class="free-delivery">Gratuit</span>' : `€${deliveryFee.toFixed(2)}`;

    const taxEl = document.getElementById('checkoutTax');
    if (taxEl) taxEl.textContent = `€${tax.toFixed(2)}`;

    const totEl = document.getElementById('checkoutTotal');
    if (totEl) totEl.textContent = `€${total.toFixed(2)}`;
}

// Filter Functions
function filterProducts() {
    return products.filter(product => {
        if (filters.category !== 'Tous' && product.category !== filters.category) return false;
        if (filters.material !== 'Tous' && product.material !== filters.material) return false;

        if (filters.priceRange !== 'Tous') {
            if (filters.priceRange === '0-500' && product.price >= 500) return false;
            if (filters.priceRange === '500-1000' && (product.price < 500 || product.price >= 1000)) return false;
            if (filters.priceRange === '1000-2000' && (product.price < 1000 || product.price >= 2000)) return false;
            if (filters.priceRange === '2000+' && product.price < 2000) return false;
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
                <td>€${product.price ? product.price.toLocaleString() : '0'}</td>
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
                    <p class="top-product-revenue">€${revenue.toLocaleString()}</p>
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
