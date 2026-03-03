/* static/js/admin/admin_customization.js */

document.addEventListener('DOMContentLoaded', function () {
    // Function to toggle the Inline visibility
    function toggleCustomizationConfig() {
        const isCustomizableCheckbox = document.querySelector('input[name="is_customizable"]');
        const inlineGroup = document.querySelector('#productcustomizationconfig_set-group'); // Django standard ID for stacked inline

        if (!isCustomizableCheckbox || !inlineGroup) return;

        if (isCustomizableCheckbox.checked) {
            inlineGroup.style.display = 'block';
            // Optional: Scroll to it with smooth behavior if enabling
            // inlineGroup.scrollIntoView({ behavior: 'smooth' });
        } else {
            inlineGroup.style.display = 'none';
        }
    }

    // Initial check
    toggleCustomizationConfig();

    // Listen for changes
    const isCustomizableCheckbox = document.querySelector('input[name="is_customizable"]');
    if (isCustomizableCheckbox) {
        isCustomizableCheckbox.addEventListener('change', toggleCustomizationConfig);
    }
});
