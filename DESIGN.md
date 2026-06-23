# En-AgentSociety — Design System Handoff

> Visual reference for Claude Code. Derived from the `En-AgentSociety.dc.html` design mock.  
> The live mock is the ground truth — refer to it for any ambiguity.

---

## 1. Fonts

Load from Google Fonts:

```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
```

| Role | Family | Weights used |
|---|---|---|
| Headings / brand | `Space Grotesk` | 500, 600, 700 |
| UI body / labels | `DM Sans` | 300, 400, 500, 600 |
| Data / IDs / times / code | `JetBrains Mono` | 400, 500 |

---

## 2. Color Tokens

### Backgrounds

| Token name | Value | Usage |
|---|---|---|
| `--bg-page` | `#070d1a` | App root, `<body>` |
| `--bg-surface` | `#0c1728` | Cards, table containers, filter bars |
| `--bg-surface-raised` | `#0d1829` | Feature cards on home page |
| `--bg-surface-hover` | `#0f1d30` | Card hover state |
| `--bg-nav` | `rgba(7,13,26,0.96)` | Sticky nav bar (+ `backdrop-filter: blur(20px)`) |

### Page texture

The page background has a subtle dot-grid overlay:

```css
background-image:
  linear-gradient(rgba(255,255,255,0.011) 1px, transparent 1px),
  linear-gradient(90deg, rgba(255,255,255,0.011) 1px, transparent 1px);
background-size: 44px 44px;
```

### Borders

| Token name | Value | Usage |
|---|---|---|
| `--border-subtle` | `rgba(255,255,255,0.07)` | Default card/panel border |
| `--border-xsubtle` | `rgba(255,255,255,0.04)` | Table row dividers |
| `--border-nav` | `rgba(255,255,255,0.07)` | Nav bottom border |
| `--border-input` | `rgba(255,255,255,0.08)` | Input/select borders |

### Text

| Token name | Value | Usage |
|---|---|---|
| `--text-primary` | `#e2eaf5` | Main body text, headings |
| `--text-secondary` | `rgba(226,234,245,0.58)` | Subtitles, descriptions |
| `--text-tertiary` | `rgba(226,234,245,0.48)` | Card body copy, muted labels |
| `--text-muted` | `rgba(226,234,245,0.38)` | Page subtitles, dimmed values |
| `--text-xmuted` | `rgba(226,234,245,0.30)` | Timestamps, IDs |
| `--text-data` | `rgba(226,234,245,0.62)` | Token counts in table |
| `--text-nav-inactive` | `rgba(226,234,245,0.48)` | Nav items at rest |
| `--text-label` | `rgba(226,234,245,0.32)` | Table column headers (uppercase) |

### Accent — Teal (primary)

| Token name | Value | Usage |
|---|---|---|
| `--accent` | `#0fb8a4` | Primary buttons, active nav, logo, borders |
| `--accent-hover` | `#11c9b6` | Primary button hover |
| `--accent-bg` | `rgba(15,184,164,0.08–0.13)` | Pill/badge/icon backgrounds |
| `--accent-border` | `rgba(15,184,164,0.20–0.22)` | Pill borders |
| `--on-accent` | `#060c18` | Text on teal buttons |

### Semantic status colors

| Status | Text | Background | Border |
|---|---|---|---|
| Running | `#60a5fa` | `rgba(96,165,250,0.13)` | `rgba(96,165,250,0.18)` |
| Completed | `#34d399` | `rgba(52,211,153,0.13)` | `rgba(52,211,153,0.18)` |
| Not Started | `#9ca3af` | `rgba(107,114,128,0.18)` | `rgba(107,114,128,0.17)` |
| Stopped / Error | `#f87171` | `rgba(248,113,113,0.13)` | `rgba(248,113,113,0.32)` |

### Feature card accent colors (home page)

Each contribution card has a `2px` top border:

| Card | Color |
|---|---|
| Observability | `#0fb8a4` (teal) |
| Validation | `#60a5fa` (blue) |
| Regional Scale | `#34d399` (green) |
| Open Source | `#a78bfa` (violet) |

---

## 3. Spacing & Sizing

| Token | Value | Usage |
|---|---|---|
| Nav height | `52px` | Sticky top nav |
| Page padding (dense) | `28px 28px` | Experiments page |
| Page padding (wide) | `48px` | Home features section |
| Card padding | `30px` | Feature cards |
| Filter bar padding | `14px 18px` | Filter row |
| Table row height | `52px` | Data rows |
| Table header height | `38px` | Column header row |
| Grid gap (cards) | `18px` | 2-col card grid |
| Nav item gap | `1px` | Between nav buttons |

---

## 4. Border Radius

| Token | Value | Usage |
|---|---|---|
| `--radius-xs` | `4px` | Status badges, small buttons |
| `--radius-sm` | `5–6px` | Table action buttons, inputs |
| `--radius-md` | `7–8px` | Primary buttons, CTAs |
| `--radius-lg` | `10px` | Filter bar, table container |
| `--radius-xl` | `12px` | Feature cards |
| `--radius-pill` | `20px` | Status chips, capability pills |
| `--radius-icon` | `8px` | Icon boxes on feature cards |

---

## 5. Typography Scale

| Role | Font | Size | Weight | Tracking | Notes |
|---|---|---|---|---|---|
| Hero title (H1) | Space Grotesk | 58px | 700 | -0.038em | `line-height: 1.04` |
| Section title (H2) | Space Grotesk | 35px | 600 | -0.025em | `line-height: 1.18` |
| Page title | Space Grotesk | 22px | 600 | -0.022em | Experiments header |
| Card title (H3) | Space Grotesk | 16.5px | 600 | — | Feature cards |
| Nav logo | Space Grotesk | 14.5px | 600 | -0.025em | |
| Body / subtitle | DM Sans | 17.5px | 300 | — | Hero subtitle |
| Card body | DM Sans | 13.5px | 400 | — | `line-height: 1.72` |
| Nav item | DM Sans | 12.5px | 400/500 | — | Active: weight 500 |
| Table row name | DM Sans | 13px | 400 | — | |
| Page subtitle | DM Sans | 13px | 400 | — | |
| Table header label | DM Sans | 10px | 700 | 0.08em | uppercase |
| Section overline | Space Grotesk | 11px | 600 | 0.12em | uppercase, teal |
| Pill / badge | DM Sans | 11–11.5px | 500–600 | 0.05–0.07em | uppercase |
| Mono ID | JetBrains Mono | 10.5px | 400 | — | truncated with `…` |
| Mono time | JetBrains Mono | 11px | 400 | — | |
| Mono tokens | JetBrains Mono | 12px | 400 | — | |
| Mono timestamps | JetBrains Mono | 10px | 400 | — | |
| Conference badge | DM Sans | 11px | 600 | 0.07em | uppercase, teal pill |

---

## 6. Components

### 6.1 Navigation bar

```
position: sticky; top: 0; z-index: 50
height: 52px
background: rgba(7,13,26,0.96); backdrop-filter: blur(20px)
border-bottom: 1px solid rgba(255,255,255,0.07)
padding: 0 20px
```

**Logo:** SVG hexagonal network mark in `#0fb8a4` + `Space Grotesk 600 14.5px` wordmark.

**Nav item (inactive):**
```
background: transparent; color: rgba(226,234,245,0.48)
padding: 5px 9px; border-radius: 6px; font-size: 12.5px
hover → background: rgba(255,255,255,0.06); color: #e2eaf5
```

**Nav item (active — e.g. Experiments):**
```
background: rgba(15,184,164,0.1); color: #0fb8a4; font-weight: 500
```

**Separator:** `1px × 16px` div, `rgba(255,255,255,0.1)`, `margin: 0 5px`.

**Nav groups (left → right):**
1. Logo
2. Config: LLM · Maps · Agents · Workflows
3. `|` separator
4. App: Experiments · Grafana · Charts · Loki · Daily Schedule
5. `|` separator
6. Docs: Survey · Documentation
7. Right: GitHub button + locale badge (`EN`)

**GitHub button (right side):**
```
background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.09)
border-radius: 6px; padding: 5px 12px; font-size: 12px
hover → background: rgba(255,255,255,0.09)
```

---

### 6.2 Primary button (teal)

```
background: #0fb8a4; color: #060c18
font-family: DM Sans; font-weight: 600
border-radius: 8px (large) / 7px (medium) / 6px (small) / 5px (table)
padding: 13px 34px (hero) / 9px 18px (page header) / 7px 18px (filter) / 5px 13px (table)
hover → background: #11c9b6
```

### 6.3 Ghost button

```
background: rgba(255,255,255,0.04–0.06); border: 1px solid rgba(255,255,255,0.08–0.11)
color: rgba(226,234,245,0.55–0.75); border-radius: 6–8px
hover → background: rgba(255,255,255,0.08–0.10)
```

### 6.4 Danger button (Stop)

```
background: transparent; border: 1px solid rgba(248,113,113,0.32)
color: #f87171; border-radius: 5px; padding: 5px 10px; font-size: 11px
hover → background: rgba(248,113,113,0.07); border-color: rgba(248,113,113,0.5)
```

### 6.5 Status badge

```
border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 500
display: inline-block; letter-spacing: 0.01em
Colors: see §2 Semantic status colors
```

### 6.6 Pill / chip (filter summary row)

```
border-radius: 20px; padding: 4px 14px; font-size: 12px
Colors: see §2 Semantic status colors (lighter alpha for bg/border)
```

### 6.7 Capability pill (hero)

```
border-radius: 20px; padding: 4px 14px; font-size: 11.5px; font-weight: 500
letter-spacing: 0.05em; text-transform: uppercase
Each pill uses one of the 4 accent colors (teal/blue/green/violet)
```

### 6.8 Feature card (home)

```
background: #0d1829; border: 1px solid rgba(255,255,255,0.07)
border-top: 2px solid <accent-color>; border-radius: 12px; padding: 30px
hover → background: #0f1d30; border-color: rgba(255,255,255,0.12)
```

**Icon box inside card:**
```
width: 40px; height: 40px; border-radius: 8px
background: rgba(<accent-rgb>, 0.1); display: flex; align-items: center; justify-content: center
margin-bottom: 18px
Icon: 19×19px stroke icon, stroke = accent color, strokeWidth: 1.8
```

### 6.9 Filter bar

```
background: #0c1728; border: 1px solid rgba(255,255,255,0.07)
border-radius: 10px; padding: 14px 18px
display: flex; align-items: center; gap: 14px; flex-wrap: wrap
```

**Label inside filter bar:**
```
font-size: 10.5px; font-weight: 600; letter-spacing: 0.07em
text-transform: uppercase; color: rgba(226,234,245,0.3)
```

**Input / Select inside filter bar:**
```
background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08)
border-radius: 6px; padding: 6px 10px; color: #e2eaf5; outline: none
```

### 6.10 Data table

**Container:**
```
background: #0c1728; border: 1px solid rgba(255,255,255,0.07)
border-radius: 10px; overflow: hidden
```

**Header row:**
```
height: 38px; background: rgba(255,255,255,0.02)
border-bottom: 1px solid rgba(255,255,255,0.07)
font-size: 10px; font-weight: 700; letter-spacing: 0.08em
text-transform: uppercase; color: rgba(226,234,245,0.32)
padding: 0 16px
```

**Data row:**
```
height: 52px; border-bottom: 1px solid rgba(255,255,255,0.04)
padding: 0 16px; display: grid (column widths as needed)
hover → background: rgba(255,255,255,0.03)
```

**Column grid template (Experiments table):**
```
162px 1fr 56px 118px 56px 84px 84px 84px 132px 132px 158px
```
Columns: ID · Name · Days · Status · Day · Time · In Tok · Out Tok · Created · Updated · Action

**ID cell:** `JetBrains Mono 10.5px`, truncated UUID prefix + `…`, `color: rgba(226,234,245,0.38)`  
**Name cell:** `DM Sans 13px`, `color: #d8e4f2`, ellipsis overflow  
**Numeric/mono cells:** `JetBrains Mono 11–12px`  
**Timestamps:** `JetBrains Mono 10px`, `color: rgba(226,234,245,0.30)`

---

### 6.11 Hero section

```
position: relative; min-height: calc(100vh - 52px)
display: flex; flex-direction: column; align-items: center; justify-content: center
padding: 80px 32px 140px; overflow: hidden
```

**Radial glow (decorative, pointer-events: none):**
```css
background: radial-gradient(ellipse 1000px 700px at 50% 48%, rgba(15,184,164,0.07) 0%, transparent 62%);
/* + inner layer: 500px×400px, opacity 0.04 */
```

**Entrance animation:**
```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
/* Badge: animation: fadeUp 0.45s ease both */
/* Content block: animation: fadeUp 0.55s 0.08s ease both; initial opacity: 0 */
```

---

## 7. Page Layouts

### Home page

```
<Nav />
<Hero>              ← min-height: calc(100vh - 52px), centered column
  badge
  logomark (76×76 SVG)
  H1
  subtitle
  capability pills
  CTA buttons
  scroll indicator
</Hero>
<Features>          ← max-width: 1120px, margin: auto, padding: 64px 48px 100px
  overline + H2
  2-col card grid (gap: 18px)
</Features>
```

### Experiments page

```
<Nav />
<Page padding: 32px 28px>
  Page header (H1 + subtitle + "Create Experiment" button)
  Filter bar (ID · Name · Status · Reset · Search)
  Status chip row (All · Running · Completed · Not Started)
  Data table (full width, horizontally scrollable at < 1300px)
</Page>
```

---

## 8. Scrollbar styling

```css
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
```

---

## 9. Token formatting (experiments table)

```js
function formatTokens(n) {
  if (n === 0)       return '—';
  if (n >= 1_000_000_000) return (n / 1e9).toFixed(1) + 'B';
  if (n >= 1_000_000)     return (n / 1e6).toFixed(0)  + 'M';
  if (n >= 1_000)         return (n / 1e3).toFixed(0)  + 'K';
  return String(n);
}
```

---

## 10. Logo / brand mark

SVG: concentric hexagon outlines (outer opacity 0.6, inner 0.25) + central filled circle + 4 outer nodes + connecting lines (opacity 0.22) + outer node cross-connections (opacity 0.14). All strokes `#0fb8a4`.

Nav size: `26×26px`. Hero size: `76×76px`.

Wordmark: `"En-AgentSociety"` in Space Grotesk 600, `#e2eaf5`, `letter-spacing: -0.025em`.

---

## 11. Pages / routes (full nav)

| Nav label | Notes |
|---|---|
| LLM | Config |
| Maps | Config |
| Agents | Config |
| Workflows | Config |
| Experiments | App — redesigned (see §7) |
| Grafana | External link |
| Charts | App |
| Loki | External link |
| Daily Schedule | App — preserve existing blocks/timeline |
| Survey | |
| Documentation | |

---

## 12. Design decisions & rationale

- **Dark navy** (`#070d1a`) over pure black: avoids harsh contrast, feels like a scientific terminal rather than a consumer app.
- **Teal accent** (`#0fb8a4`) chosen for geo/data associations; high contrast on dark backgrounds; avoids the blue-heavy look of most dev tools.
- **Space Grotesk** for all headings: wide, geometric, confident — matches academic/research tool aesthetic without being sterile.
- **JetBrains Mono** only for data values (IDs, times, token counts) — never for UI labels — keeps the typographic hierarchy clean.
- **Subtle grid texture** (`background-size: 44px`) on the page background evokes map grids / coordinate spaces without being intrusive.
- **No sidebar**: nav is top-horizontal with divider groups. Keeps full horizontal width available for wide data tables and map views.
- **Status colors** are consistent across badges, chips, and card borders throughout the app — a single source of truth (§2).
