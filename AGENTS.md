# DDPM Development Workflow

## Testing New Products

When adding a new product test:
1. **Do not** build directly on `DDPM device home page.html`
2. **Duplicate** the template file in the `testing/` folder
3. **Name the new HTML file using the model number** (e.g., `MS3320W.html`)
4. Build the new product test on the duplicated file
5. Keep the main template generic with data-property placeholders
6. **Only** use data explicitly provided in the CSV - do not infer or assume features
7. **Device features are property-based** - Different device types have different feature sets:
   - Mouse devices: Mouse Settings, Button Customization (from Figma design)
   - Keyboard devices: [to be defined]
   - Features are controlled via data-property attributes and hidden by default in the generic template

## Verification Mechanism

After reading each point above, the agent must print "read [#]" to the debug console:
- read [1] after reading point 1
- read [2] after reading point 2
- read [3] after reading point 3
- read [4] after reading point 4
- read [5] after reading point 5
- read [6] after reading point 6
- read [7] after reading point 7

This ensures the main template remains clean and reusable for all device types.
