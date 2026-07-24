---
phase: requirements
title: Requirements & Problem Understanding
description: Clarify the problem space, gather requirements, and define success criteria
---

# Requirements & Problem Understanding: AR Web App Product Placement

## Problem Statement
**What problem are we solving?**
Users buying home appliances or products want to see how a product fits and looks inside their real-life room before purchasing. Currently, traditional 2D images fail to provide realistic scale, proportion, and aesthetic fit in the user's specific space.

## Goals & Objectives
**What do we want to achieve?**
- **Primary Goal**: Build a web application accessible via mobile phone browsers (Chrome, Safari, Edge) that uses WebXR/AR (`<model-viewer>` / Three.js) to allow users to place 3D/AR representations of products onto real-world surfaces through their phone camera.
- **Secondary Goal**: Provide an admin/upload interface where product specs (Dimensions: WxHxD, Weight, Name, Category) and multi-angle product photos can be uploaded and processed into 3D AR models.
- **Non-Goals**: Requiring users to install native iOS/Android apps (Must work 100% in browser).

## User Stories & Use Cases
1. **Product Spec & Image Upload (Admin/User)**:
   - As an admin/user, I want to fill in product dimensions (Width, Height, Depth) and upload multi-angle photos (Front, Back, Left, Right, Top) or 3D files (`.glb`/`.gltf`) so the app can register the product for AR viewing.
2. **Product Catalog & Camera AR View (Mobile User)**:
   - As a shopper on mobile, I want to browse products, click "View in AR", grant camera permission, scan the floor/table surface, and place the product in 1:1 real scale.
3. **Interactive AR Manipulation**:
   - As a user, I want to drag, rotate, and reposition the placed 3D product on the floor to check fit and aesthetics.

## Success Criteria
- Works on both iOS (WebXR / QuickLook fallback) and Android (WebXR / Scene Viewer).
- 1:1 true scale placement based on product dimensions.
- Smooth camera feed with high-performance 3D rendering (>45 fps).
- Clean, modern, responsive glassmorphism UI.

## Constraints & Assumptions
- Camera access requires HTTPS or `localhost` context.
- Mobile browser must support WebXR or WebGL + AR QuickLook / Scene Viewer.


