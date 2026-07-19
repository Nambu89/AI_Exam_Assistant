# Design tokens

"Study / edu meets Azure" — trustworthy, calm, focused. Tokens live in
`src/index.css` as CSS custom properties, exposed to Tailwind v4 via
`@theme inline`. Class-based dark mode (`html.dark`).

## Palette

| Token | Light | Dark | Use |
|---|---|---|---|
| `--background` | `#f6f8fc` | `#0b1220` | app canvas |
| `--foreground` | `#0f172a` | `#e6edf7` | body text |
| `--card` | `#ffffff` | `#121a2b` | surfaces |
| `--muted` / `--muted-foreground` | `#eef2f8` / `#4b5772` | `#1b2436` / `#a3b3cc` | secondary surfaces/text |
| `--primary` | `#0f6cbd` (Azure blue) | `#4aa3ec` | actions, links, focus ring |
| `--accent` | teal | teal | highlights |
| `--success` / `--warning` / `--danger` | — | — | status |
| `--community-1…8` | categorical | categorical | concept-map communities |

Every fg/bg pair targets **WCAG 2.2 AA** (≥ 4.5:1 body, ≥ 3:1 large text/UI).
Focus is always visible (2px `--ring` outline). `prefers-reduced-motion` is
honoured globally.

## Type & shape

- Font: Inter (system fallback), mono stack for code.
- Radius scale from `--radius` (0.75rem): `sm`/`md`/`lg`/`xl`.
- Spacing: Tailwind default scale; content max-width `6xl`.

## Primitives

`Button` (variants: primary/secondary/outline/ghost/danger; sizes sm/md/lg/icon;
plus `buttonClass()` so `<Link>` can look like a button), `Badge` (tones),
`Card` family, `Select`. Icons: lucide-react.

## Responsiveness

Mobile-first. Two-column layouts (chat + sources, map + panel) collapse to a
single column under `lg`. The concept map scales via SVG `viewBox`.
