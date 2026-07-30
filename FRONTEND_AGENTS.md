# FRONTEND_AGENTS.md — TraceMind Frontend Guide

This document defines the frontend implementation strategy for TraceMind.

The backend is already implemented.

Do NOT redesign backend contracts.

The frontend must consume the existing REST API exactly as defined.

---

# Product Vision

TraceMind is NOT an admin dashboard.

It is an AI Investigation Workspace.

The experience should make users feel like they are investigating an AI failure rather than browsing logs.

The product story is:

Choose Investigation
↓

Watch Investigation

↓

Find Root Cause

↓

Understand Why

↓

Fix

↓

Prevent

Everything in the interface should reinforce this narrative.

---

# UX Goals

The UI should communicate the value of TraceMind within 5 seconds.

A user should instantly understand:

• Which AI session failed

• Where the failure occurred

• Why it occurred

• How to fix it

Avoid exposing backend implementation details.

Avoid showing unnecessary JSON unless explicitly requested.

The graph is the hero of the application.

---

# Design Direction

Visual inspiration:

• Linear

• Raycast

• Vercel

with

Subtle Neo Brutalism

Do NOT build:

Cyberpunk UI

Glassmorphism

Gradient-heavy dashboards

Gaming aesthetics

The interface should feel professional, developer-first and memorable.

---

# Visual Principles

Large whitespace

Strong typography

Clear visual hierarchy

Minimal color palette

Bold buttons

Thick borders

Subtle offset shadows

Warm neutral backgrounds

Rounded cards

Smooth motion

The interface should feel confident instead of playful.

---

# Layout

Desktop-first.

Structure:

Top Navigation

↓

Left Sidebar

↓

Execution Workspace

↓

Investigation Summary

↓

Bottom Drawer

The graph workspace should occupy most of the screen.

---

# Navigation

The application should be a single-page experience.

Avoid page navigation.

Everything happens inside one Investigation Workspace.

---

# Information Architecture

Application

├── Landing

├── Investigation Workspace

│     ├── Session List

│     ├── Execution Graph

│     ├── Investigation Summary

│     └── Timeline Drawer

└── Settings (Future)

---

# Core Components

Layout

Navbar

Sidebar

Bottom Drawer

Workspace

Execution Graph

Timeline

Node Details

Investigation

Diagnosis Card

Confidence Meter

Evidence List

Suggested Fix

Regression Viewer

Shared

Buttons

Cards

Badges

Tooltips

Loading Overlay

Empty State

Error State

Skeleton Loader

---

# Dashboard Workflow

Landing

↓

Launch Workspace

↓

Select Trace

↓

Load Execution Graph

↓

Inspect Nodes

↓

Click Diagnose

↓

Show Investigation Summary

↓

Generate Regression Test

↓

Export

The experience should feel sequential.

---

# Interaction Principles

Never overwhelm the user.

Reveal information progressively.

Hover

↓

Node Details

Click

↓

Investigation

Diagnose

↓

Animated Analysis

Complete

↓

Highlight Root Cause

The interface should guide attention naturally.

---

# Loading Experience

Diagnosis should never appear instantly.

Sequence:

Building Execution Graph...

↓

Detecting Anomalies...

↓

Tracing Causal Chain...

↓

Generating Diagnosis...

↓

Investigation Complete

The graph should animate while processing.

---

# Color System

Background

#F8F7F4

Surface

#FFFFFF

Primary

#FF6B35

Success

#4CAF50

Warning

#F4B400

Danger

#EF4444

Border

#111111

Text

#161616

---

# Typography

Heading

Space Grotesk

Body

Inter

Code

IBM Plex Mono

---

# Motion

Motion should reinforce understanding.

Use animation only when it communicates state.

Examples:

Graph construction

Node highlight

Drawer expansion

Panel transition

Diagnosis reveal

Avoid decorative animations.

---

# Component Rules

Every component must be reusable.

Every component must support loading.

Every component must support empty states.

Every component must support errors.

No component should contain API logic.

Business logic belongs outside presentation components.

---

# API Layer

Use the existing backend.

Do NOT duplicate diagnosis logic.

Do NOT calculate confidence.

Do NOT infer anomalies.

Render exactly what the backend provides.

---

# Design Philosophy

The graph is the product.

The diagnosis is the story.

The regression test is the takeaway.

Everything else should disappear into the background.

---

# Success Criteria

A first-time user should understand the product within five seconds.

The graph immediately communicates causality.

The root cause is unmistakably highlighted.

The investigation summary explains the failure clearly.

The regression test demonstrates how the failure can be prevented.

If any UI element does not directly support this journey, remove it.