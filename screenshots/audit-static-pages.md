# Design Audit: Static Pages
Date: 2026-02-22

## Summary

The live site is **structurally close** to the Pencil designs but has significant divergences in layout composition, typography hierarchy, and content presentation. The core visual language (colors, fonts, card styling) is largely consistent. The biggest gaps are:

1. **Home page** uses a flat list of game cards instead of a 3-column grid, has different page header structure, and shows real (many) games vs the idealized 3-card mockup.
2. **Help page** is well-matched structurally; the TOC navigation uses pipe-separated inline links instead of pill-style buttons.
3. **New Game page** is the closest match overall; the form fieldsets and button row align well with the design.

The academic theme CSS is comprehensive and well-written. Most differences stem from HTML structure choices (how content sections are organized) rather than missing CSS rules.

---

## Home Page (/)

### Screenshot Comparison
- Pencil: node MD0P7
- Live: screenshots/home-live.png

### Differences Found

1. **[Layout] Page header structure**
   - Pencil: Dedicated card with top-rounded corners containing "PROSIM III -- Production Simulation" (h1 at 36px Crimson Pro 700) + subtitle "Production Management Simulation Game" (16px Source Sans 3) + gold divider bar. Card connects visually to the Welcome Section below.
   - Live: No card wrapper. Just an `<h1>PROSIM</h1>` followed by a `<p>` with bold "Production Management Simulation" text. The h1 has gold underline from the h1 CSS rule. No card background.
   - Fix: The live page uses `<h1>` directly in `<main>`, but the design uses a `<main> > <header>` wrapper. Wrap the h1 and subtitle in `<header>` tags inside main. CSS rule `.theme-academic main > header` already provides the card styling with top-rounded corners.

2. **[Content] Title text differs**
   - Pencil: "PROSIM III -- Production Simulation"
   - Live: "PROSIM"
   - Fix: Update the h1 text in `index.html` to "PROSIM III -- Production Simulation" or similar to match the design's intent of a more descriptive title.

3. **[Layout] Welcome section is missing**
   - Pencil: Has a distinct "Welcome to PROSIM III" card (h2 at 26px Crimson Pro, gold accent bar, two paragraphs explaining the simulation).
   - Live: No welcome section. Goes directly from the page header to the "Your Games" section.
   - Fix: Add a `<section>` with a "Welcome to PROSIM III" h2, a brief description paragraph, and the "select an existing game" call-to-action.

4. **[Layout] Game cards use stacked list instead of 3-column grid**
   - Pencil: Three game cards displayed in a horizontal 3-column grid layout within the "Your Simulation Games" section.
   - Live: Games render as a stacked vertical list of cards spanning full width.
   - Note: The CSS `.game-list` class does define `grid-template-columns: repeat(auto-fill, minmax(300px, 1fr))` which should produce a multi-column layout. The issue may be that the actual data has 9 games (vs 3 in the design) and the full-width card styling is working. **Check**: Is the `.game-list` class actually being applied? Looking at the HTML: `<div class="game-list">` -- yes it is. The cards should grid. The live screenshot shows they ARE in a single-column layout -- at 960px max-width with `minmax(300px, 1fr)`, we should get 2-3 columns. This might be a Simple.css override issue or the cards might be too wide.
   - Fix: Inspect whether Simple.css is overriding the grid. The game cards appear to span the full container width. Check if `.game-list` needs `display: grid !important;` or if another rule is overriding it.

5. **[Components] Game card gold top bar**
   - Pencil: Each game card has a 4px gradient gold bar at the very top (inside the card, achieved via a rectangle element).
   - Live: The game cards rely on the CSS `::before` pseudo-element for the gold top bar. This should work -- verify it's rendering. From the live screenshot, the cards DO appear to have a subtle top accent. This looks correct.
   - Status: **Likely OK** -- confirm visually at higher resolution.

6. **[Typography] Game card title styling**
   - Pencil: Card titles are 20px Crimson Pro 600, navy color.
   - Live: Card h3 titles appear to match this styling based on the CSS (`.game-card h3` = 1.25rem = 20px, Crimson Pro, 600, navy).
   - Status: **Match**.

7. **[Layout] "Your Simulation Games" section header**
   - Pencil: h2 "Your Simulation Games" with gold accent bar + "New Game" button (navy background, white text, plus icon) aligned to the right in a flex row, separated by a bottom border.
   - Live: h2 "Your Games" with "New Game" link-button to the right. The `section > header` CSS rule provides flex layout with space-between.
   - Differences: Title says "Your Games" not "Your Simulation Games". The New Game button in the design has a `+` icon before the text; the live version is just text.
   - Fix: Consider adding a `+` character or icon to the New Game button. Update section title if desired.

8. **[Content] "About PROSIM" section**
   - Pencil: No "About PROSIM" section at the bottom.
   - Live: Has an "About PROSIM" section below the games list with descriptive text and a "Learn how to play" link.
   - Note: This is additional content not in the design. It provides useful context. Could be kept as-is or removed to match the design.

9. **[Typography] Footer text**
   - Pencil: "PROSIM III -- Production Simulation" in 14px Crimson Pro 600 navy, below that "Reconstructed from 1996 original..." in 13px Source Sans 3 text-light.
   - Live: "PROSIM - Production Management Simulation" in strong + regular text, "Originally created by Greenlaw, Hottenstein & Chu (1968) | Reconstructed 2025" in small.
   - Fix: The text content differs. The design says "PROSIM III" and references the 1996 original; the live says just "PROSIM" and references 1968. Update to match the design for consistency.

10. **[Spacing] Navbar brand text**
    - Pencil: "PROSIM III" with letter-spacing 0.8px, 22px Crimson Pro 700.
    - Live: `<strong>PROSIM</strong>` styled via `.brand` selector (1.375rem = 22px, Crimson Pro 700, letter-spacing 0.04em = ~0.88px).
    - Difference: Text says "PROSIM" not "PROSIM III".
    - Fix: Update navbar brand text to "PROSIM III" in `navbar.html`.

11. **[Components] Navbar link "Decisions" present in design, not in live for non-game context**
    - Pencil: Navbar shows Home, Help, Decisions, and theme selector.
    - Live: Navbar shows Games, New Game, Help, and theme selector.
    - Note: This is a contextual difference -- the design's navbar shows "Decisions" which is game-specific. The live site correctly shows "Games" and "New Game" for the home page context. The design should probably show the non-game nav too.
    - Status: **Acceptable difference** -- live site navigation makes more sense for the home page.

12. **[Components] Navbar active state**
    - Pencil: "Home" nav link has a brighter/more opaque background (#ffffff4D = 30% white) compared to others (#ffffff1A = 10% white), indicating the active page.
    - Live: All nav links have the same `background: rgba(255, 255, 255, 0.1)` with no active state differentiation.
    - Fix: Add an `.active` or `aria-current="page"` class to the current page's nav link and style it with `background: rgba(255, 255, 255, 0.3)`.

---

## Help Page (/help)

### Screenshot Comparison
- Pencil: node jMop6
- Live: screenshots/help-live.png

### Differences Found

1. **[Layout] Page header card**
   - Pencil: Card with top-rounded corners containing "How to Play PROSIM" (h1 at 28px, 700 weight) + subtitle "Complete guide to managing your production company" (15px, Source Sans 3, text-secondary). Connected to the TOC nav below.
   - Live: `<h1>How to Play PROSIM</h1>` rendered directly in main, with the standard h1 gold underline styling. No card wrapper, no subtitle text.
   - Fix: Wrap h1 in a `<header>` tag inside main to trigger the `.theme-academic main > header` card styling. Add the subtitle paragraph.

2. **[Components] TOC navigation - pill buttons vs inline links**
   - Pencil: TOC rendered as a row of pill-shaped buttons with navy-pale (#e8eef5) background, 6px/14px padding, 6px corner radius, centered in a card with 10px gap.
   - Live: TOC rendered as inline text links separated by pipe characters (`|`), inside a `<nav>` block with "Contents:" label. Styled with a card background via `.theme-academic main > nav`.
   - Fix: Replace the pipe-separated link format with a flex row of styled pill links. Add CSS for TOC pills:
     ```css
     .theme-academic main > nav {
         display: flex;
         flex-wrap: wrap;
         gap: 0.625rem;
         justify-content: center;
         align-items: center;
     }
     .theme-academic main > nav a {
         background: var(--acad-navy-pale);
         padding: 0.375rem 0.875rem;
         border-radius: 6px;
         text-decoration: none;
         font-size: 0.8125rem;
     }
     ```
     Also update the HTML to remove the pipe separators and "Contents:" label, or restyle them.

3. **[Typography] Section h2 headings**
   - Pencil: Section h2s like "Game Objective", "Production System" etc. are styled within their respective cards.
   - Live: Section h2s render with the standard h2 style (gold accent underline via ::after pseudo-element, border-bottom). The `section > h2` rule removes the top margin which matches.
   - Status: **Mostly match**. The gold accent bar in the design is a 48px wide x 2px gold rectangle below the h2, while the CSS uses a 3rem (48px) ::after element. This is consistent.

4. **[Layout] Production Flow diagram**
   - Pencil: The production flow is shown as a visual diagram with department boxes (Parts Dept, Assembly Dept) connected by arrows, with colored borders (green for Parts, navy for Assembly).
   - Live: Production flow is rendered as a `<pre>` block with plain text: `Raw Materials -> Parts Department -> Parts (X', Y', Z') -> Assembly Department`
   - Fix: This is a significant visual difference. The design has a proper flow diagram with styled boxes. Implementing this would require custom HTML/CSS for the flow visualization. This is a **medium-high effort** change.

5. **[Layout] Department info layout**
   - Pencil: "Departments" section shows Parts Department and Assembly Department info in a two-column layout side by side.
   - Live: Departments are displayed sequentially in a single column with `<p>` and `<ul>` elements.
   - Fix: Wrap the two department blocks in a flex/grid row for a two-column layout on desktop.

6. **[Components] "Back to Games" link at bottom**
   - Pencil: Has a back arrow link at the very bottom before the footer.
   - Live: Has `<a href="/">&larr; Back to Games</a>` inside a section at the bottom.
   - Status: **Match** (content matches, just wrapped in a section card).

7. **[Spacing] Section card gap**
   - Pencil: 20px gap between section cards.
   - Live: Sections have `margin: 1.25rem 0` (20px) which matches.
   - Status: **Match**.

8. **[Typography] Cost Structure ordered lists**
   - Pencil: Ordered lists have custom gold-colored numbering.
   - Live: CSS provides custom `counter()` numbering with gold color via `.theme-academic section ol > li::before`.
   - Status: **Match**.

9. **[Components] Strategy Tips layout**
   - Pencil: Shows "Strategy Tips" with subsections for Early/Mid/Late/General game tips.
   - Live: Same structure with h3 subsections and bullet lists.
   - Status: **Match**.

10. **[Content] Workforce section detail**
    - Pencil: Shows more specific efficiency ranges and training details in a structured format.
    - Live: Simple bullet list with "Untrained operators: 60-90% efficiency", "Trained operators: 95-100% efficiency".
    - Status: **Acceptable** -- content is similar, just less structured.

---

## New Game Page (/new)

### Screenshot Comparison
- Pencil: node GA2ME
- Live: screenshots/new-game-live.png

### Differences Found

1. **[Layout] Page header card**
   - Pencil: Card with top-rounded corners containing "Start New Game" (28px, Crimson Pro 700) + subtitle paragraph (15px, text-secondary, line-height 1.6). Connected to the Company Setup card below.
   - Live: `<h1>Start New Game</h1>` with gold underline, followed by a `<p>` paragraph. No card wrapper.
   - Fix: Same as other pages -- wrap in `<header>` to trigger card styling. The CSS `main > header + section` would need adjustment since the next element is a `<form>` with `<fieldset>`, not a `<section>`.

2. **[Components] Fieldset legend styling**
   - Pencil: "Company Setup" and "Advanced Options" rendered as card section headers (22px Crimson Pro 600, with 48px gold accent bar below).
   - Live: `<fieldset>` with `<legend>` rendered using the fieldset CSS (1.125rem = 18px Crimson Pro 600, navy color, on background).
   - Difference: Design uses 22px font-size with gold accent bar; live uses 18px with standard legend positioning (overlapping the border).
   - Fix: Either increase the legend font-size to 22px and add a gold bar decorative element, or accept the difference as a fieldset-vs-card distinction. The current fieldset styling is clean and functional.
   - CSS suggestion: `.theme-academic fieldset legend { font-size: 1.375rem; }` to match 22px.

3. **[Components] Form input layout**
   - Pencil: Company Name input is a full-width field (height 42px, 8px radius, 1px border). Game Length is a select with the value and chevron, plus a helper text note beside it (not below).
   - Live: Company Name and Game Length inputs are full-width fields. The helper text "All game lengths are multiples of 4..." appears below the select in a `<small>` tag.
   - Difference: In the design, the Game Length helper appears inline next to the select. In the live site, it's below.
   - Status: **Minor** -- the live layout is more standard and readable.

4. **[Spacing] Form field gap in fieldset**
   - Pencil: 16px gap between form fields within the card.
   - Live: Fields inside fieldset are spaced by the browser's default margins on labels, inputs, and smalls. The fieldset padding is `1.25rem 1.5rem`.
   - Fix: Add explicit margins between label/input groups or use flex-gap within fieldsets.

5. **[Components] Button row alignment**
   - Pencil: "Start Game" button (navy, white text, 12px/24px padding, 8px radius) and "Cancel" button (outlined, navy text, border) side by side with 12px gap.
   - Live: "Start Game" submit button and "Cancel" secondary link-button side by side. The CSS `.theme-academic form > div:last-child` provides flex layout with 0.75rem (12px) gap.
   - Status: **Match** in layout. Button sizing may differ slightly.

6. **[Components] Cancel button style**
   - Pencil: Cancel button has white background, 1px border in $border color, navy text.
   - Live: Cancel uses `a[role="button"].secondary` which gets `background: var(--acad-surface); border: 1.5px solid var(--acad-border); color: var(--acad-navy)`.
   - Status: **Close match**. Border is 1.5px instead of 1px.

7. **[Layout] Game Overview section**
   - Pencil: "Game Overview" card (22px Crimson Pro h2, gold accent bar, bullet list, closing paragraph, "Read the full game manual" link).
   - Live: `<section>` with `<h2>Game Overview</h2>`, bullet list, paragraphs, and "Read the full game manual" link. Styled as a card via the section CSS rule.
   - Status: **Good match**. Content and structure align well.

8. **[Typography] Section h2 within Game Overview**
   - Pencil: "Game Overview" at 22px Crimson Pro 600 with gold bar.
   - Live: Standard h2 styling at 1.625rem (26px) with gold ::after accent.
   - Difference: Design uses 22px, live uses 26px. The design's gold bar is explicit (48px rectangle), while the CSS uses `::after` pseudo-element.
   - Fix: This is within the card context. The design's h2 inside a fieldset/card may intentionally be smaller than a standalone h2. Consider if 26px is too large for in-card headings.

9. **[Content] Bullet list styling**
   - Pencil: Uses explicit bullet dots (text "bullet") with 8px gap to text, inside a left-padded container.
   - Live: Standard `<ul>` with CSS marker styling (gold-colored bullets via `::marker`).
   - Status: **Close match** -- both achieve gold bullets with similar spacing.

---

## Priority Summary

### Critical (breaks the design intent)

1. ~~**Home page missing Welcome section**~~ FIXED -- Added "Welcome to PROSIM III" section between header card and games list.
2. ~~**Home page game cards not in grid layout**~~ FIXED -- Added `!important` on display:grid, `max-width:none` on articles, reduced minmax to 280px. Renders as 2-column grid.
3. ~~**Page headers not using card wrapper**~~ FIXED -- All three pages now use `<header>` inside `<main>` triggering the connected card styling.

### Medium (noticeable but not broken)

4. ~~**Help page TOC uses pipe-separated links instead of pill buttons**~~ FIXED -- Converted to flex row of pill-styled buttons with navy-pale bg, 6px radius.
5. ~~**Help page Production Flow is plain text instead of visual diagram**~~ FIXED -- Built flow diagram with styled boxes (color-coded Parts/Assembly departments) connected by gold arrows.
6. ~~**Navbar missing active state indicator**~~ FIXED -- Added `aria-current="page"` via template logic and CSS for 30% white background.
7. ~~**Brand text says "PROSIM" instead of "PROSIM III"**~~ FIXED -- Updated navbar, page headers, and footer.
8. ~~**Footer text content differs**~~ FIXED -- Now reads "PROSIM III -- Production Simulation" / "Reconstructed from the 1996 original by Chu, Hottenstein & Greenlaw".
9. ~~**Fieldset legend font-size**~~ FIXED -- Increased from 1.125rem (18px) to 1.375rem (22px).

### Low (polish/fine-tuning)

10. ~~**Game section title text**~~ FIXED -- Changed to "Your Simulation Games".
11. ~~**New Game button missing "+" icon**~~ FIXED -- Button now reads "+ New Game".
12. ~~**Help page department info could use two-column layout**~~ FIXED -- Added `.dept-grid` with 2-column CSS grid, color-coded cards.
13. **Cancel button border width** -- 1.5px in CSS vs 1px in design. Barely noticeable. NOT FIXED (intentional -- 1.5px reads better on screen).
14. ~~**"About PROSIM" section on home page**~~ FIXED -- Removed to match design. Welcome section now provides introductory context.
