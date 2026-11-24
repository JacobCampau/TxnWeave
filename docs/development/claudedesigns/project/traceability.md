# Project: Design-to-Requirement Traceability

- **Status:** Agreed (P2, user decision 2026-11-17). This map is maintained by whoever adds or changes a design element: every new decision, behavior or component gets a row here in the same change.
- **Master plan:** [../master-plan.md](../master-plan.md) (P2)
- **Related:** [requirements.md](requirements.md) (FR → design, the reverse direction)

## Rules
- Every decision (`B`, `BD`, `D`, `P`), reference rule (`R`), behavior (`1.x`–`7.x`, `UI-n`) and component in `backend/` and `ui/` appears below with at least one FR or UC ID.
- No FR is invented. Elements with no FR behind them are in [Untraced elements](#untraced-elements), with the interview finding or plan line that motivated them.
- **Weak** means the FR covers the element only by interpretation. Those are listed separately.

## Master plan
| Element | FR / UC |
|---|---|
| P1 waves | FR-01 to FR-27 |
| G1 | FR-02, FR-08 |
| G2 | FR-08 (weak) |
| G3 | FR-18 |
| G4 | FR-11, FR-19 |
| B6, B8 | FR-03 to FR-06, FR-11, FR-12 |
| B7, BD25 | FR-03 to FR-06 |
| BD27 | FR-14, FR-15, UC06, UC07 |

## backend/data-model.md
| Element | FR / UC |
|---|---|
| B14, BD1, BD26 | FR-03 to FR-05, FR-12 |
| BD5, BD17 | FR-04 |
| BD16 | FR-03, FR-05, FR-06 |
| BD24 (titles) | UC02, FR-07 |
| BD29, settings types | FR-13, UC08 |
| Shared value types, document tables, schema split, 2.9, 2.10 | FR-03 to FR-06, FR-12 |

## backend/persistence.md
| Element | FR / UC |
|---|---|
| B1, B2, BD22 | FR-18, FR-01 |
| B10, tables, ORM | FR-03 to FR-06 |
| BD4, uniqueness | FR-12 |
| BD7 | FR-01 |
| BD30, `important` column | FR-13, FR-14 |
| Indexes | FR-08 |

## backend/api.md
| Element | FR / UC |
|---|---|
| B3, behaviors 1.1 to 1.6, BD32 | FR-01 |
| B9 | FR-03 to FR-06 |
| B16 | FR-11 |
| BD28, 2.11 | FR-14, UC06 |
| BD31, behaviors 7.1 to 7.3 | FR-13, UC08 |
| 2.1, 2.2 | FR-12 |
| 2.3 to 2.5 | FR-07 |
| 2.6 | FR-18 |
| 2.7 | FR-06 |
| 2.8 | FR-08 |

## backend/relationship-resolution.md
| Element | FR / UC |
|---|---|
| R1 to R6, B11, BD6, 3.1 to 3.4, 3.9 to 3.13 | FR-08 (sources: FR-04 to FR-06) |
| B4, B5, BD2, BD3, BD14, BD15, BD18, 3.5 to 3.8 (incomplete nodes) | FR-08 (weak) |
| BD19 | FR-08 (scope limit) |
| 3.14 (money flip) | FR-03, FR-04 |

## backend/graph-output.md
| Element | FR / UC |
|---|---|
| B12, 4.1, 4.2 | FR-02, FR-08 |
| Node and edge data fields | FR-02, FR-09 |
| Classes | FR-02, FR-21 |
| 4.3, 4.4 | FR-14, FR-15, UC06, UC07 |

## backend/csv-save-load.md
| Element | FR / UC |
|---|---|
| B17, BD12 | FR-11, FR-19 |
| BD9, BD10, BD11, 5.1 to 5.5 | FR-11, UC04 |
| BD13 | FR-11, UC05 |
| BD33, 5.9 | FR-13, FR-14, UC08 |
| BD34 (markerless file rejected, 422) | FR-11, FR-19, UC05 |
| 5.6 to 5.8, `ImportReport` | FR-11, FR-19, FR-22 |

## backend/build-plan.md
Each step carries its FRs in the step table. Step 10 has none (see Untraced).

## ui/color-system.md
| Element | FR / UC |
|---|---|
| D19, palette tokens, color usage table | FR-02, FR-13 |
| D20, D22, D23 | FR-02 |
| D24 | FR-03 to FR-06 |
| User-chosen colors section | FR-13, UC08 |
| Important badge, node and edge rows | FR-14, UC06 |

## ui/app-shell.md
| Element | FR / UC |
|---|---|
| D1 | FR-02, FR-09, UC02 |
| D2 | FR-08 |
| D3, UI-1 | FR-01, FR-11, UC05 |
| D4, D30, UI-25 | FR-01 |
| D5, UI-2 | FR-11 |
| D6, `TopBar` | FR-01, FR-11, FR-17 |
| UI-3 | FR-18 |
| UI-17, `LoadReportDialog` | FR-19 |
| `App.tsx`, `StartDialog` | FR-01, UC05 |
| `ConfirmDialog`, `Toast` | FR-01, FR-07 |
| D34, UI-30 (start flow, Resume row) | FR-01, FR-18, UC05 |
| D35, UI-31 (CSV load checks) | FR-11, FR-19, UC05 |

## ui/investigation-page.md
| Element | FR / UC |
|---|---|
| D7 | FR-02, FR-08, FR-09, FR-10 |
| D8 | FR-10, FR-20 |
| D9, graph styles | FR-02, FR-13, FR-21 |
| D11 | FR-02 |
| D31, UI-26 | FR-14, FR-15, UC06, UC07 |
| UI-4, UI-5, UI-8, `InvestigationPage`, `GraphCanvas`, `graphMapper.ts` | FR-02, FR-10 |
| UI-6, `PropertyPanel` | FR-09, FR-14, UC03 |
| UI-7, `GraphToolbar`, `ExportDialog`, Legend | FR-10, FR-17, FR-21, UC09 |
| UI-29, `cytoscapeConfig.ts` | FR-13, UC08 |
| D36, UI-32 (export orientation preview) | FR-17, UC09 |
| D37, UI-33, `GraphLegend` | FR-21 |

## ui/documents-page.md
| Element | FR / UC |
|---|---|
| D12, UI-9, `DocumentsPage` | UC02, FR-07 |
| D13, UI-11 | UC02, FR-16 |
| D14, UI-14 | FR-07, FR-12 |
| D15, UI-15 | FR-07 |
| D16, UI-10, UI-16 | FR-03 to FR-06 |
| D17, D18, D25, UI-13, input components | FR-12 |
| UI-12 | FR-07, FR-08 (weak) |
| D32, UI-27 | FR-14, UC06 |
| D33, UI-28, `DocumentList`, `documentSearch.ts` | FR-16, UC02 |
| `NodeEditor` | FR-03 to FR-07, FR-12 |
| UI-34 (Save disabled with no changes) | FR-07, FR-12 |
| UI-35 (delete details) | FR-07, UC02 |

## ui/settings-page.md
| Element | FR / UC |
|---|---|
| D26, `SettingsPage` | FR-13, UC08, FR-01 |
| D27, D28, UI-21 to UI-23, `AppearanceTable`, `StylePreview` | FR-13, UC08 |
| D29, UI-24 | FR-01 |

## ui/build-plan.md
Each step carries its FRs in the step table.

## Untraced elements
These have **no FR or UC behind them**. They stay in the design. Whether to keep each one without an FR, or to add a requirement to the course documents, is for the user to decide.

| Element(s) | What it is | Motivated by |
|---|---|---|
| B13, D10, BD8, BD21, api 6.1 to 6.3, backend step 10 | Card-number masking, no echo or logging of card numbers, localhost/VPN only | Interview Q8 (leaks), NQ-3. The nearest FRs (FR-23, FR-24) are authentication, which is Future |
| B15 | snake_case JSON | Technical convention |
| BD23 | Last write wins | Single-user scope (master plan principle 6) |
| D21, UI-20 | Desktop only, 1280px minimum | Persona works at a desktop |
| UI-18, `ApiErrorBanner` | Banner when the API is unreachable | Interview Q9 ("loses connectivity") |
| UI-19, WCAG contrast tables (color-system) | Keyboard access, focus ring, contrast ratios | Interview Q11 (accessibility), NQ-2 |
| G5, P2 | Process rules | Author's review workflow |

## Weakly traced elements
- **Incomplete nodes and edges** (G2, B4, B5, BD2, BD3, BD14, BD15, BD18, 3.5 to 3.8, UI-12, and the incomplete styles in D9 and D22) trace to FR-08 only by interpretation: relationships are generated from forms, including references to documents that don't exist yet. The explicit source is `initial-plans.md` ("incomplete or missing information should not throw an error"), not an FR.
- **5.5 formula escaping** traces to FR-11 (a readable file), but its purpose is security (spreadsheet formula injection).
