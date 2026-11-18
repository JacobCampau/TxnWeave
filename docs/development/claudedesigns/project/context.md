# Project: Context, Stakeholders, Quality Goals and Risks

- **Status:** Draft (2026-11-17), except the waves section, which restates the agreed P1. Taken from the course PDFs. The quality goals (NQ) are still suggestions. Open follow-ups are in [../design-history.md](../design-history.md).
- **Source plans:** `docs/development/CS420_Project_Discovery and Specification.pdf` (read in full). `docs/development/CS420_Project_Concept.pdf` (**only its outline and link targets could be read**, see F19 in [../design-history.md](../design-history.md)). Also `docs/development/initial-plans.md`.
- **Master plan:** [../master-plan.md](../master-plan.md)
- **Related:**
  - [requirements.md](requirements.md): FR-01 to FR-27 and UC01 to UC10, with waves.
  - [traceability.md](traceability.md): design elements → FR/UC.

## Problem statement
From the Discovery PDF, section 1:
- Gift card fraud cases cover many transactions over many days. The evidence comes from separate systems: video, POS reports, gift card histories, online orders, SKU details and store credit card rewards.
- The hardest part of a case is **explaining it to other agents**, not finding the evidence. No tool gives a single summary, so agents fall back on verbal explanations and quick sketches.
- Graphing a case in draw.io works, but it is too slow to do for most cases: every box and line is drawn by hand from paper documents.
- Commercial investigation tools cost money or do far more than the team needs.
- **What TxnWeave does:** agents fill in forms and get a connected graph back. The graph helps them identify theft incidents and locate suspects, gives the Asset Protection (AP) team something to act on, and lets people outside the case see what happened and where to watch for future incidents.

## Stakeholders
| Stakeholder | Role | What they need |
|---|---|---|
| AP agent (primary user) | Enters documents and reads the graph | Forms instead of drawing; a clear graph |
| AP team members not on the case, including trainees and older employees | Read graphs and PNG exports | A graph they understand without knowing the report systems (interview Q7, Q12) |
| The author | Developer, and an AP agent | Small, reviewable design and code (master plan principle 5) |
| CS 420 course staff | Grade the project | Wave 1 fully implemented, Wave 2 at least started (P1, [requirements.md](requirements.md)) |
| Police and report readers (indirect) | Receive reports built with help from the graph (persona scenario) | Accurate content. They never use the app |

## Persona (Discovery PDF, Table 2)
**Kyle**, a full-time AP agent aged 50 at a large retailer.
- Has never used a computer program for more than 30 minutes at a time.
- Learns and explains visually.
- Is very good at organizing large amounts of paper reports.
- His best program is Excel, along with anything that has labeled forms.
- His team currently shares investigation notes by text message and photo.
- Has no time to learn tools that require drawing shapes and lines.

**Scenario:** Kyle confirms a fraudulent return, then finds a set of suspicious gift cards in the card history. He fills in one form for each transaction, gift card and online order, and the graph appears. His team understands the case straight away, plans its reports to police around the graph, and highlights important documents as they go.

**Design consequences:**
- The forms-first flow is already the core design (G1, D7).
- Labeled forms that enforce their own format (D17).
- No drawing (FR-08).
- Plain wording on Save and Load (RK-3).
- "Highlighting important reports" is importance (BD27, D31, D32).

## Interview findings (Discovery PDF, section 2)
The two interviewees are referred to as A and B. The design docs don't need their names.

| Q | Finding | Where it is handled |
|---|---|---|
| 1 | A: date, time and register for transactions. B: card numbers and activation dates. B: clicking into a card's history is nice to have, not required | Node data ([graph-output](../backend/graph-output.md)) and PropertyPanel (UI-6). History view: UC10 / FR-25, Future |
| 2 | Add, edit and remove as the case grows, by **filling in forms**. Transaction: cards used, card types, and "previous transactions linked to the transaction". Gift card: activation and history. Online order: date placed, payment, card. A catch-all item. Notes on every item | Forms ([documents-page](../ui/documents-page.md)). **Linking a transaction to other transactions is not designed (F13)** |
| 3 | On click: related transactions and cards (A). Personal information, dates, times and payments (B) | PropertyPanel (UI-6). **There are no personal-information fields (F14)** |
| 4 | Neither interviewee understood "saving to a file". They mainly use Microsoft Word | Autosave (B2), RK-3 |
| 5 | Sharing should show clear connections (A) and the "main route" to the conclusion of the case, meaning the important moments and how they connect (B) | PNG export (UI-7). Main route: important nodes and edges (BD27) |
| 6 | Color coding (A). Following one card, or one person's actions (B) | Per-type colors on the Investigation settings page (D27). Document search, including by the last digits of a card (D33). **There is no person entity (F15, open)** |
| 7 | Graphs must be clear to people who don't know the systems (A). Input mistakes could lead to wrong conclusions (B) | Legend (UI-7, FR-21). Validation (FR-12). RK-1 |
| 8 | Fear of leaks. Wants password protection | FR-23 / FR-24, Future. IAM design still to come. NQ-3 |
| 9 | After a crash, go back to the last save, with autosaves in between. Invalid save files say where the problem is and why. Invalid form input is reported before the item is created | B2, `ImportReport` ([csv-save-load](../backend/csv-save-load.md)), UI-13 |
| 10 | No size limit; the canvas should grow | FR-20, NQ-6, F10 |
| 11 | Top three. A: security, storage, accessibility. B: main route, image export, easy editing | NQ-3, B2, NQ-2. BD27, UI-7, D14 |
| 12 | Useful when it organizes complex cases (A), and anyone on the team can understand a case by looking at it (B) | Project success criteria below |

## Project success criteria
- S1. An agent can enter a multi-day gift card case through forms only and get a connected graph (FR-03 to FR-08).
- S2. A team member who wasn't on the case can explain the case's main connections from the graph or its PNG export, using the legend (FR-17, FR-21).

## Quality goals (non-functional requirements)
These are drawn from the interviews and the persona. **They are suggestions waiting for the user's confirmation.**

| ID | Quality | Requirement | Covered by |
|---|---|---|---|
| NQ-1 | Learnability | A first-time user can create a document and see it on the graph without instructions. Every field is labeled, required fields are marked `*`, and every error message says what to fix | D14, D17, UI-4, UI-13 |
| NQ-2 | Accessibility | WCAG AA text contrast, full keyboard access, visible focus, and color never the only signal | D19, UI-19, color-system "Input in error" row |
| NQ-3 | Confidentiality | Localhost or VPN only. Card numbers masked outside the form and panel. No logging of request bodies. Password protection is Future work (FR-23) | B13, D10, 6.1 to 6.3, BD21 |
| NQ-4 | Reliability | No saved document is lost after a browser crash. Content of an invalid import file never causes an error status | B2, 5.8, G2 |
| NQ-5 | Data quality | Every input is validated before it is saved. Uncertain links stay visibly uncertain (dashed) | FR-12, BD3, BD15 |
| NQ-6 | Scale | The canvas has no fixed size. A performance target is **open** (F10, suggested: 500 documents render within 3 seconds) | FR-20, B11 |
| NQ-7 | Shareability | A PNG export can be read on its own (masked numbers, legend colors) | UI-7, D10 |

## Risks
| ID | Risk | Mitigation in the current design |
|---|---|---|
| RK-1 | Input mistakes produce a misleading graph (interview Q7) | Strict validation, incomplete nodes, and dashed ambiguous edges. No conflict checking yet (BD19) |
| RK-2 | Case data leaks. There is no login yet (Q8) | Localhost or VPN only, masking, unencrypted file kept small (BD7). IAM design still to come |
| RK-3 | Users don't understand saving to a file (Q4) | Autosave is automatic (B2). StartDialog offers Resume. Save and Load are plain buttons |
| RK-4 | Scope creep. The PDF's section 5 says AI tools added features nobody asked for | Waves (P1) and traceability (P2, [traceability.md](traceability.md)). Every addition is labeled and confirmed by the user |
| RK-5 | Large cases become slow or unreadable (Q10) | `cose` layout, fit and re-layout. F10 performance target |
| RK-6 | Non-experts misread the graph (Q7) | Legend, edge labels, distinct shapes (D9, D11) |

## Similar systems
- draw.io: manual drawing. This is what TxnWeave replaces (Discovery PDF section 1).
- From the Concept PDF's link targets only (the text around them is unread, F19): i2 Analyst's Notebook, DataWalk, Linkurious. All three are commercial link-analysis tools. That matches the Discovery PDF's point that existing tools "cost money or contain way more tools" than the team needs.

## Schedule and milestones: implementation waves (P1)
The user replaced the PDF's three requirement levels with waves. P1 in the [master plan](../master-plan.md) is the authoritative statement.

| Wave | Target | Build-plan steps |
|---|---|---|
| Wave 1 | FR-01 to FR-12 fully implemented | [backend](../backend/build-plan.md) steps 1 to 10, [UI](../ui/build-plan.md) steps 1 to 9 |
| Wave 2 | FR-13 to FR-21 at least started | backend steps 11 and 12, UI steps 10 to 13 |
| Future | After the assignment is submitted: FR-22 to FR-27, IAM, open follow-ups | Rows tagged "Future" |

Neither PDF gives calendar dates. The Discovery PDF is dated 2026-11-09 (CS 420 Project Part 2). The Concept PDF's outline has no schedule section. Neither PDF gives a testing approach. Testing is defined only by the acceptance criteria in each feature doc.
