---
name: performance-audit
description: How to perform a performance audit on your project.
argument-hint: "Describe the audit scope"
agent: "agent"
---

# Performance Audit Workflow

Use this workflow to verify that current changes haven't regressed the PageSpeed score.

## 1. Local Optimization Check
Before deploying, ensure all assets are optimized.
// turbo
1. Run `npm run optimize` (or `node scripts/optimize-images.js`).
2. Verify that there are no new large images in `src/images` (>300KB).

## 2. Production Build Check
Verify build size and lazy loading.
1. Run `npm run build`.
2. Inspect the `dist/assets` folder. Look for any JS chunks larger than 200KB.

## 3. Automated PageSpeed Audit
// turbo
1. Deploy to staging/production.
2. Visit [PageSpeed Insights](https://pagespeed.web.dev/).
3. Enter the site URL and select the **Mobile** tab.
4. Target Score: **90+**.

## 4. Key Metrics to Watch
- **LCP (Largest Contentful Paint)**: Target < 2.5s.
- **CLS (Cumulative Layout Shift)**: Target 0.
- **TBT (Total Blocking Time)**: Target < 200ms.

## 5. Remediation
If the score is < 90:
- Identify large images not being caught by the script.
- Check if new third-party scripts were added without `defer` or initialization delay.
- Use the `browser_subagent` to capture a trace of the loading process.
