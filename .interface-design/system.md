# Interface Design System — LinkedIn Ads Action Center

## Direction
Professional, data-dense, temporally-aware operations console. Information density with breathing room.

## Feel
Cold-professional. Like a well-built analytics tool at a media agency. Not warm, not playful. Precise.

## Foundation
- **Font:** Inter (Google Fonts CDN), feature settings: cv02, cv03, cv04, cv11
- **Spacing base:** 4px
- **Depth:** Borders-only (no shadows)
- **Radius:** sm=4px, md=6px, lg=8px
- **Color hue:** 250 (blue-gray) in oklch space

## Token Architecture
All tokens in `frontend/src/index.css`.

### Surfaces (3-level elevation via lightness)
- `--canvas` — base background
- `--surface` — cards, panels
- `--elevated` — table headers, dropdowns

### Borders (2-level hierarchy)
- `--edge` — standard separation
- `--edge-soft` — subtle separation

### Text (3-level hierarchy)
- `--ink` — primary
- `--ink-secondary` — supporting
- `--ink-faint` — labels, metadata, disabled

### Accent
- `--accent` — desaturated LinkedIn blue (oklch hue 240)
- `--accent-muted` — accent at 8-12% opacity

### Semantic
- `--signal-positive` — green, health/success
- `--signal-warning` — amber, alerts/staleness
- `--signal-error` — red, errors/failures

## Component Patterns

### Page Header
Sticky, translucent backdrop-blur, 48px height, border-b.

### Cards
Rounded-lg, border, bg-card. Padding: px-4 py-3 to py-4.

### Section Labels
10px, font-semibold, uppercase, tracking-[0.08em], muted-foreground.

### Status Pills
Rounded-full, 10px font-medium. Signal colors at 10% opacity backgrounds.

### Tabs
Underline style (border-b-2), not button pills. For data-dense views.

### Tables
Elevated header row. Dense 1.5py rows. Tabular-nums. Edge-soft borders.

### Stat Blocks
Numbers-first: 2xl font-semibold tabular-nums. 10px uppercase label above.

## Chart Palette
`CHART_COLORS` in ChartCard.tsx: blue, teal, amber, rose, violet, green (all desaturated oklch).

## Signature
Temporal awareness — connection status in sidebar, token expiry visualization, data freshness indicators, workflow status pills.
