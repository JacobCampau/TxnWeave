# UI: Color System

- **Status:** Agreed (from `page-and-ui-layout.md` v2, "Color system"). Updated 2026-11-17 (user decisions): user-chosen node colors (D27), and the colors for important nodes, edges and badges (D31, D32). D19 is unchanged.
- **Scope:** The fixed five-color palette and where it is defined, the black-or-white text rule with WCAG contrast figures, contrast between palette colors for borders and shapes, the color of every app-shell, page and form element, and the limited places transparency is allowed. Graph node and edge styles are in [investigation-page.md](investigation-page.md).
- **Master plan:** [../master-plan.md](../master-plan.md)
- **Related:** [investigation-page.md](investigation-page.md) (graph styles use these tokens), [app-shell.md](app-shell.md), [documents-page.md](documents-page.md), [build-plan.md](build-plan.md) (step 1)

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| D19 | **Every color comes from the 5-color palette. Text is #000000 or #FFFFFF, chosen by WCAG contrast** | User rule | — |
| D20 | The graph canvas is #D2CDCB, not white | White isn't in the palette. #D2CDCB is the closest color to the plan's "white canvas", gives 13.3:1 contrast with black text, and keeps all four node fills distinguishable | #131313 dark canvas (an #131313 node fill would disappear, and exports would be harder to read) |
| D22 | Transparency is allowed in exactly two places: the plan's 75% opacity on incomplete nodes, and the dialog backdrop (ink at 70%). Nothing else may use transparency | Transparency blends colors into shades outside the palette. These two uses are required by the plan or needed for usability | Solid ink backdrop with no transparency at all |
| D23 | Empty-state text is black italic, 20px, on the mist canvas. This replaces the plan's "greyed text" | Grey text would break the black-or-white text rule | Grey text; text on a slate card |
| D24 | When a dropdown is open, some browsers draw its option list in the operating system's colors. This is an accepted exception | CSS can't fully control native dropdown lists | Build a custom dropdown component |

## Palette tokens
Defined once in `apps/web/src/styles/palette.ts` (for Cytoscape) and mirrored as CSS custom properties in `apps/web/src/styles/global.css`. No other file may contain a hex color.

| Token (CSS / TS) | Hex | Text color on it | Contrast | Contrast with the other text color |
|---|---|---|---|---|
| `--color-ink` / `palette.ink` | #131313 | #FFFFFF | 18.6:1 | black 1.1:1 |
| `--color-slate` / `palette.slate` | #394249 | #FFFFFF | 10.2:1 | black 2.0:1 |
| `--color-mist` / `palette.mist` | #D2CDCB | #000000 | 13.3:1 | white 1.6:1 |
| `--color-rose` / `palette.rose` | #D26D6F | #000000 | 6.2:1 | white 3.4:1 (fails for normal text) |
| `--color-crimson` / `palette.crimson` | #C11E20 | #FFFFFF | 6.0:1 | black 3.5:1 (fails for normal text) |
| `--text-on-dark` | #FFFFFF | Used on ink, slate, crimson | — | — |
| `--text-on-light` | #000000 | Used on mist, rose | — | — |

Every chosen text pairing meets WCAG AA for normal text (4.5:1 or better).

## Contrast between palette colors
Borders and shapes need 3:1 against what's next to them.

| Pair | Ratio | 3:1 or better? |
|---|---|---|
| mist / ink | 11.8 | yes |
| mist / slate | 6.5 | yes |
| mist / crimson | 3.8 | yes |
| mist / rose | 2.2 | **no**. Rose shapes always get an ink border |
| ink / rose | 5.5 | yes |
| ink / crimson | 3.1 | yes |
| slate / rose | 3.0 | just meets it |
| slate / crimson | 1.7 | **no**. Never put crimson directly against slate |

## Color usage
| Element | Background | Text | Border / other |
|---|---|---|---|
| Top bar | ink | white | Active tab: 3px crimson underline and bold text. Inactive tabs: regular weight |
| Investigation toolbar | slate | white | 1px ink bottom border |
| Graph canvas | mist | black | — |
| PropertyPanel drawer | slate | white | 1px ink left border |
| Documents list pane | slate | white | — |
| List item (normal) | slate | white | 1px ink divider |
| List item (selected) | ink | white | — |
| List item (incomplete) | same as its normal or selected state | white | 4px rose left border and an "Incomplete" badge |
| "Incomplete" badge | rose | black | — |
| Form pane | mist | black | — |
| Text inputs / dropdowns | mist | black | 1px slate border |
| Input in error | mist | black | 2px crimson border plus a black message starting "Error:" (color is never the only signal) |
| Focus ring on light backgrounds | — | — | 3px ink outline, 2px offset |
| Focus ring on dark backgrounds | — | — | 3px mist outline, 2px offset |
| Primary button (one per view: Save, New document, Export) | crimson | white | — |
| Secondary button on a light background | slate | white | — |
| Secondary button on a dark background | mist | black | — |
| Destructive button (Delete, Discard) | rose | black | 1px ink border. The label always names the action |
| Disabled button | mist | black | 1px dashed slate border, `cursor: not-allowed`, `aria-disabled`. Never uses transparency |
| API error banner | crimson | white | Retry button: ink background, white text |
| Success toast | slate | white | 1px ink border |
| Error toast | crimson | white | 1px ink border |
| Dialogs | mist | black | 1px ink border. Backdrop is ink at 70% opacity (D22) |
| Loading spinner | — | — | Crimson on mist. Mist on slate or ink |
| Selected text highlight (`::selection`) | crimson | white | — |
| Scrollbars (`scrollbar-color`) | track ink | — | thumb slate |
| "Important" badge (list item, D32) | ink | white | 1px mist border, so the badge stays visible on both slate and ink (selected) list items |
| Important node (graph, D31) | the type's fill | label stays black on mist | 6px **double** ink border |
| Important edge (graph, D31) | — | — | 4px line in the investigation's important-edge color: ink (default), slate or crimson (D27) |
| Settings page | mist | black | Color swatches are palette tokens with a 1px ink border |

## User-chosen colors (D27)
On the Investigation settings page, users pick node fills from the 5 tokens and the important-edge color from ink, slate or crimson. This keeps D19:
- **No hex outside `palette.ts`.** Settings carry token names (BD29).
- **Text stays black or white with the same contrast.** Node labels are drawn below the node on the mist canvas, never on the fill.
- **Every fill stays visible.** Every node keeps its 2px ink border (11.8:1 against mist).
- **Every edge color meets 3:1 against mist:** ink 11.8, slate 6.5, crimson 3.8. Rose (2.2) and mist (1.0) are not offered for edges.
- **Color is never the only signal.** Each type still has a shape, the legend, and a label prefix.

## Acceptance criteria
- [ ] Searching `apps/web/src` for hex colors finds them only in `styles/palette.ts` and `styles/global.css`, and only the five palette colors plus #000000 and #FFFFFF.
- [ ] All text is #000000 or #FFFFFF and follows the text pairings in the palette table.
- [ ] Transparency appears only on incomplete nodes (75%) and the dialog backdrop (ink at 70%), per D22.

## Course requirements
Traces: FR-02, FR-13, FR-14, UC06, UC08 (full map in [../project/traceability.md](../project/traceability.md)). The WCAG contrast rules have no FR behind them; they come from interview Q11 and NQ-2 and are listed as untraced.
