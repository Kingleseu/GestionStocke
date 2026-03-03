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

            // 5. Layer 2: Draw Text Overlay (Below texture for realism)
            if (textStr) {
                ctx.save();
                ctx.fillStyle = "#111";
                ctx.font = `500 20px "${textFont}"`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(textStr, width / 2, height * 0.6);
                ctx.restore();
            }

            // 6. Layer 3: Draw Product Texture (Multiply Mode)
            if (bgImg) {
                ctx.save();
                ctx.globalCompositeOperation = 'multiply';
                ctx.drawImage(bgImg, 0, 0, width, height);
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
