Based on bryllim/bryl-minimal-design, MIT License, Copyright (c) 2026 Bryl Lim.

# Bryl-Minimal Design Template

**Template name:** bryl-minimal
**Template type:** Design language / frontend aesthetic profile
**Owner skill:** Cloak
**Source:** bryllim/bryl-minimal-design
**License:** MIT

## Purpose
Apply the bryl-minimal design language â€” a monochrome, typography-driven minimal aesthetic with halftone dot textures, pixel-font display headings, tiny uppercase monospace labels, soft large-radius cards, and full light/dark theming. Use this whenever building or restyling any web UI (portfolio, landing page, blog, dashboard, docs site, app screen, component) where the user wants a clean, minimal, monochrome, editorial, or terminal-inspired look. Works with any stack (plain HTML/CSS, Tailwind, React, Vue, etc.) â€” it describes the aesthetic in values, not code.

## Activation keywords
Use when: User asks for minimal, monochrome, editorial, terminal-inspired, or bryl-minimal UI.

## Do-not-use conditions
Do not use when: User asks for colorful, playful, enterprise SaaS, glassmorphism, brutalist, cyberpunk, or brand-specific UI.

## Visual rules
- **No accent color.** Emphasis comes from inversion, typography, and texture (halftone dots).
- **Monochrome palette.** Pure white/true black backgrounds with a nine-step gray ramp for depth.
- **Hairlines.** Use 1px hairlines (Gray 200) generously to separate sections and grid cells.
- **Textures.** Halftone dots instead of color blocks for visual interest.
- **Inverted chips.** The one "loud" element allowed per view is an inverted chip (e.g. black background, white text on light mode).
- **Text selection.** Selection should invert: ink background, background-colored text.

## Typography rules
- **Body/UI:** Geist (sans-serif) for paragraphs, navigation, card titles, buttons.
- **Technical:** Geist Mono for labels, timestamps, tags, footer links, nav items.
- **Display:** Geist Pixel for page titles, section number labels, big stat values.
- **Long-form:** Source Serif 4 for article/blog body text only.
- Micro-labels should be 9-11px mono, UPPERCASE, letter-spaced.
- Hierarchy comes from font choice, casing, and tracking, not huge size extremes.

## Layout rules
- **Whitespace is structure.** Content lives in a narrow measure with generous vertical rhythm.
- Avoid using boxes or background tints to separate sections.
- Sections are separated by hairline rules and numbered labels.

## Component rules
- Soft large-radius cards. When a card needs a fill, use gray 50 or a faint gradient from gray 50 to the background.
- Clean and minimal form inputs, primarily separated by hairlines or minimal borders.

## Motion rules
- Restrained but deliberate motion.
- Theme changes crossfade over half a second on background, text, and border colors.

## Accessibility gates
- Semantic HTML
- Accessible contrast
- Keyboard support
- Responsive layout
- Reduced-motion support
- Preserved stack

## Restyling order
1. Review semantic structure and accessibility baseline.
2. Establish monochrome color tokens and typography scale.
3. Apply layout rhythms (whitespace, narrow measures).
4. Apply components, styling borders to hairlines, and using halftone textures.
5. Verify contrast, motion restrictions, and responsive adaptations.
