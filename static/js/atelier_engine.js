/**
 * Atelier Mkaribu - Studio Engine v2
 * High-end product customization logic
 */

class AtelierStudio {
    constructor(config) {
        this.config = config;
        this.state = {
            step: 1,
            view: 'front', // 'front' or 'back'
            choices: {
                model: 'base',
                studio_component: null,
                studio_engraving: { text: '', font: '', side: 'front' }
            }
        };

        this.initKonva();
        this.bindEvents();
    }

    initKonva() {
        const container = document.getElementById('konva-container');
        this.stage = new Konva.Stage({
            container: 'konva-container',
            width: container.offsetWidth,
            height: container.offsetHeight
        });

        this.layer = new Konva.Layer();
        this.stage.add(this.layer);

        this.mainGroup = new Konva.Group({
            x: this.stage.width() / 2,
            y: this.stage.height() / 2
        });
        this.layer.add(this.mainGroup);

        this.loadBaseImage();
    }

    loadBaseImage() {
        Konva.Image.fromURL(this.config.image, (img) => {
            const scale = Math.min(this.stage.width() * 0.8, this.stage.height() * 0.8) / 500;
            img.width(500 * scale);
            img.height(500 * scale);
            img.offsetX((500 * scale) / 2);
            img.offsetY((500 * scale) / 2);
            this.baseImage = img;
            // Use multiply to let underlying engravings show through highlight/shadows
            img.globalCompositeOperation('multiply');
            this.mainGroup.add(img);
            this.layer.draw();
        });
    }

    updateEngraving(text, font) {
        if (!this.engravingNode) {
            this.engravingNode = new Konva.Text({
                text: '',
                fontSize: 22,
                fontFamily: font || 'Dancing Script',
                fill: 'rgba(0,0,0,0.6)',
                align: 'center',
                wrap: 'word',
                padding: 10,
                draggable: true
            });

            // "Engraving" effect: slightly dark with a subtle highlight
            this.engravingNode.shadowColor('rgba(255,255,255,0.4)');
            this.engravingNode.shadowBlur(1);
            this.engravingNode.shadowOffset({ x: 1, y: 1 });
            this.engravingNode.shadowOpacity(0.5);

            this.mainGroup.add(this.engravingNode);
            // Ensure engraving stays BELOW the base image for realistic look
            this.engravingNode.moveToBottom();
        }

        this.engravingNode.text(text);
        if (font) this.engravingNode.fontFamily(font);

        // Center it roughly for now
        this.engravingNode.offsetX(this.engravingNode.width() / 2);
        this.engravingNode.offsetY(this.engravingNode.height() / 2);

        this.layer.draw();
    }

    zoomTo(scale, centerX, centerY) {
        gsap.to(this.mainGroup, {
            scaleX: scale,
            scaleY: scale,
            x: centerX || this.stage.width() / 2,
            y: centerY || this.stage.height() / 2,
            duration: 1,
            ease: "expo.out",
            onUpdate: () => this.layer.draw()
        });
    }

    bindEvents() {
        window.addEventListener('resize', () => {
            const container = document.getElementById('konva-container');
            this.stage.width(container.offsetWidth);
            this.stage.height(container.offsetHeight);
            this.mainGroup.x(this.stage.width() / 2);
            this.mainGroup.y(this.stage.height() / 2);
            this.layer.draw();
        });
    }
}
