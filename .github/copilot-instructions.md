# User Objective

Rebuild hypertrader.com.br with the same core content but a completely different and innovative experience.

## Requirements

1. Ignore and remove the blog section.
2. Auto-detect browser language and load Portuguese or English accordingly.
3. Use visual references inspired by sci-fi spacecraft interiors, command centers, teleport effects, uniforms, androids, and alien species.
4. Keep implementation simple: minimal backend for agent creation, everything else in HTML/JS/CSS, and leverage mature libraries for advanced visual effects and 3D.
5. Host on Google Cloud with minimal cost using on-demand infrastructure, CDN, backend, and database only when needed.
6. Backend language standard: Python.

## Creative Direction

Build a highly interactive, futuristic immersion where users feel they are boarding a spacecraft and interacting with advanced technologies.

## Suggested Concept: The Quantum Bridge

1. Use an immersive SPA instead of traditional vertical scrolling.
2. Add a loading transition inspired by transport/hyperspace effects to mask heavy asset loading.
3. Build a 3D cockpit-style HUD with floating holographic menus (Three.js or React Three Fiber).
4. Use a four-part pneumatic door transition between sections.
5. Add AI-generated backgrounds and android-style guide avatars.

## Low-Cost Google Cloud Stack

1. Frontend: Firebase Hosting or Cloud Storage + Cloud CDN.
2. Vector store: Pinecone serverless or Vertex AI Vector Search. For strict budget, use local JSON vectors or Firestore.
3. Language detection: `navigator.language` with PT/EN content loading.

## Visual and Motion Tooling

1. Vanta.js for animated galaxy or molecular cloud backgrounds.
2. Spline for interactive 3D assets and door animations.
3. GSAP for hologram transitions and staged UI reveals.

## User Journey Suggestion

1. Entry screen: "Requesting boarding permission..."
2. Main bridge: market radar, robot strategy panels, and central command console.

## Development Architecture Guidance

1. Local development:
- Vite for fast frontend iteration.
- Firebase Emulators for local Cloud Functions testing.
2. Staging:
- Temporary Firebase Hosting URL for validating 3D animations and load performance.
3. Production:
- Cloud Storage + CDN for low-latency media delivery.

## Technical Core Guidance

1. Internationalization middleware that reads `navigator.language` and injects PT/EN copy.
2. Lazy-load 3D models only after user interaction to keep initial load fast.
