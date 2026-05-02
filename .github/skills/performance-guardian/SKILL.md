---
name: performance-guardian
description: Ensures the project maintains a 90+ PageSpeed score on mobile by enforcing strict asset optimization and code efficiency standards.
---

# Performance Guardian Skill

## Core Philosophy
In this project, performance is not an afterthought; it is a core feature. We aim for maximum efficiency and user experience.

## Image Asset Standards
- **Automated Optimization**: Always run `node scripts/optimize-images.js` (or `npm run build`) after adding new images.
- **Dimensions**: 
	- Results/Screenshots: Max width 400px.
	- Content Images: Max width 1200px.
- **Formats**: Prefer WebP if possible, otherwise highly compressed JPEGs.
- **Lazy Loading**: Use `loading="lazy"` for all non-critical images.
- **Decoding**: Use `decoding="async"` for all images outside the LCP area.

## Code Execution & LCP
- **Defer Everything**: If a script or component is not needed for the initial frame, defer it.
- **Initialization Delay**: Scripts like analytics, HUD radars, and complex canvas animations should wait for at least 800ms-2000ms after the page loads.
- **LCP Integrity**: Critical above-the-fold elements and background animations are LCP priorities. Keep them simple, fast, and avoid layout shifts.

## CLS (Cumulative Layout Shift)
- **Zero Tolerance**: Every container must have an explicit height (skeleton) or a fixed size before content loads.
- **WebFonts**: Use `font-display: swap` and preconnect to Google Fonts.

## Build Governance
- The `prebuild` hook in `package.json` must always be present and functional.
- Any regression in PageSpeed mobile score (below 90) is considered a critical bug.
