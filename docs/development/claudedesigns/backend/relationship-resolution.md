# Backend: Relationship Resolution

- **Status:** Agreed (from `backend-graphing-design.md` v3, behavior section 3). Course traceability note updated 2026-11-17; no rule changed.
- **Scope:** The pure function in `services/relationship_service.py` that takes every saved document of one investigation and produces placeholders (incomplete nodes), links, and `referenced_by`. Covers reference rules R1–R6, partial-reference matching for transactions, exact / ambiguous / zero-match outcomes, placeholder creation, IDs and prefill, promotion, edge merging and status, determinism, and the single place amounts are sign-flipped.
- **Master plan:** [../master-plan.md](../master-plan.md) (BD25 sign convention, B13 card masking)
- **Related:** [data-model.md](data-model.md) (key tuple, BD1, BD26), [graph-output.md](graph-output.md) (turns the resolution into Cytoscape elements), [api.md](api.md) (`referenced_by`, placeholder 409 rules), [persistence.md](persistence.md)

## Non-goals
- Links based on store number, register, date or amount alone (for example "same store"). Only the reference fields in R1 to R6 create edges.
- Flagging details that disagree between two documents, for example a history entry dated 01-02-2026 pointing at a transaction dated 01-03-2026 (BD19). Note that with composite matching, a disagreeing date or store simply doesn't match (3.3).

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| B4 | **Incomplete nodes are derived, not stored.** On every read, references that match no saved document become placeholders in the response. Nothing is written to the database for placeholders | Placeholders can never fall out of sync. Orphaned placeholders vanish by themselves, deleted referenced documents show as incomplete again (D15), and promotion is simply saving a matching document | Stored placeholder rows |
| B5 | A node is **incomplete** only when it is a placeholder. An edge is **incomplete** when either end is a placeholder **or** the edge came from an ambiguous match (BD15) | Simple and testable. Reuses the existing dashed edge style, so the UI doesn't change | One-sided references also count as incomplete (rejected, BD18) |
| B11 | Relationship resolution is a **pure function** in `services/` that works on the whole investigation in memory | Easy to read and test without a database. Investigations are small | SQL joins |
| BD2 | **In a reference, a blank or absent component is a wildcard ("not known"), not `""`.** For example, a Gift Card activation with no store number matches a transaction at any store | References often hold less detail than the transaction itself (no register number ever). If a blank meant `""`, most references could never match a transaction that has a register number | Treat blanks in references as `""` (most activations and history entries would never connect) |
| BD3 | A reference matches a candidate transaction when every component the reference **knows** is equal to the candidate's value. One match links normally. Zero matches creates or joins a placeholder. Two or more matches links to **every** candidate with `match: "ambiguous"` | It never errors, never hides a possible connection, and stays visibly uncertain (dashed edge) until the agent adds detail | Link to none and create a placeholder (makes a fake node next to real ones); pick one candidate (silently wrong) |
| BD6 | Edge kinds and directions follow table 3.2 (`activated`, `used_in`, `related`) | Accepted default (OQ-4) | — |
| BD14 | A placeholder's **single-value fields** (such as `time`) are prefilled only when every reference attached to it agrees. Its **repeatable rows** (payments, history entries) get one derived row per qualifying reference, with amounts sign-flipped per BD25 (3.7) | Accepted assumption A5, extended in v3 so the sign convention also applies to prefilled rows | First reference wins; never prefill amounts (v2) |
| BD15 | An ambiguous edge has `status: "incomplete"` and `match: "ambiguous"`, so it is drawn dashed with the existing incomplete-edge style. There is no separate ambiguous style (user decision, v3) | No UI change is needed. The `ambiguous` class stays in the data in case a style is wanted later | A distinct ambiguous style; a new status value |
| BD18 | Completeness depends only on node existence and match quality. One-sided references are recorded in the edge's `refs` but don't change its status | Accepted default (OQ-5) | An `unconfirmed` status |
| BD19 | No checking for conflicting details in v1 | Accepted default (OQ-6) | — |

## 3. Behavior
Input: all saved documents of one investigation. Output: placeholders, links, and `referenced_by`.

3.1 **Index the saved documents:** `card_by_number` and `order_by_number` (dictionaries keyed by number); `txns_by_number` (a dictionary from `transaction_number` to the list of saved Transactions with that number).

3.2 **Reference rules.** Each rule produces a reference `(source document, target type, known components, kind, ref)`.

| Rule | Reference field(s) | Target | Known components of the reference | Edge direction | `kind` | `ref` |
|---|---|---|---|---|---|---|
| R1 | Gift Card `activation.transaction_number`, `activation.date`, `activation.store_number` | Transaction | number, date, and store if not blank | Transaction → Gift Card | `activated` | `gift_card_activation` |
| R2a | Gift Card `history[i].transaction_number`, `.date`, `.store_number` | Transaction | number, date, and store if not blank | Gift Card → Transaction | `used_in` | `gift_card_history` |
| R2b | Transaction `payments[i].gift_card_number` | Gift Card | number | Gift Card → Transaction | `used_in` | `payment` |
| R3 | Online Order `payments[i].gift_card_number` | Gift Card | number | Gift Card → Online Order | `used_in` | `payment` |
| R4 | Misc `payments[i].gift_card_number` | Gift Card | number | Gift Card → Misc | `used_in` | `payment` |
| R5 | Misc `transaction_number` | Transaction | number only | Misc → Transaction | `related` | `misc_reference` |
| R6 | Misc `order_number` | Online Order | number | Misc → Online Order | `related` | `misc_reference` |

No reference ever knows a register number. Gift Card and Online Order references are single-number lookups: a match or a placeholder, never ambiguous.

3.3 **Matching a Transaction reference** against a candidate (a saved Transaction, or a placeholder, see 3.5). A candidate matches when, **for every component the reference knows**, the candidate has that component and the values are exactly equal. Components the reference doesn't know are ignored (BD2).

Saved candidates always have a store number (BD26), and a blank register is `""` (BD1). References never know a register, so the register never affects matching. It only affects uniqueness. A reference with no store matches a transaction at any store.

Examples. Saved transactions: A = `(00482913, 2026-03-14, "042", "003")`, B = `(00482913, 2026-03-14, "042", "007")`, C = `(00482913, 2026-03-14, "051", "")`, D = `(00482913, 2026-04-02, "042", "")`.

| Reference | Known | Matches | Result |
|---|---|---|---|
| Activation `00482913`, 2026-04-02, store 042 | n, d, s | D | exact link to D |
| History `00482913`, 2026-03-14, store 051 | n, d, s | C | exact link to C |
| History `00482913`, 2026-03-14, store 042 | n, d, s | A, B | ambiguous links to A and B |
| History `00482913`, 2026-03-14, no store | n, d | A, B, C | ambiguous links to A, B and C |
| History `00482913`, 2026-05-01, store 042 | n, d, s | none | placeholder `(00482913, 2026-05-01, "042", ?)` |
| History `00482913`, 2026-05-01, no store | n, d | none | placeholder `(00482913, 2026-05-01, ?, ?)` (store unknown, BD26), or it joins the placeholder in the row above if both references exist (3.5) |
| Misc `00482913` | n | A, B, C, D | ambiguous links to all four |
| Misc `11112222` | n | none | placeholder `(11112222, ?, ?, ?)` |

3.4 **Outcome per reference:** exactly one saved match gives a link with `match: "exact"`. Two or more saved matches give one link to **each** match, with `match: "ambiguous"` (BD3). Zero saved matches: the reference resolves against placeholders (3.5).

3.5 **Placeholders for unmatched Transaction references.** This step runs after every reference has been tried against the saved documents, and is deterministic:
1. Collect the zero-match references. Sort them by number of known components, most first, then by known values, then by source document ID.
2. For each reference, find the placeholders already created that match it (3.3, where a placeholder's unknown components never match a component the reference knows).
   - One match: attach to it (`exact`).
   - Two or more: attach to each (`ambiguous`).
   - None: create a new placeholder whose key holds exactly the reference's known components. Its other components are unknown (`null`).
3. Because the most specific references go first, a number-only Misc reference joins an existing `(number, date, store)` placeholder instead of creating a second "Transaction 00482913".

   Example: activation `(11112222, 2026-05-01, 042)` and Misc `11112222`, both with zero saved matches, give **one** placeholder `(11112222, 2026-05-01, "042", ?)` with both attached as `exact`.

Gift Card and Online Order placeholders are keyed by the number alone and deduplicated by it.

3.6 **Placeholder ID:** `"ph-" + type + "-" + sha256(text).hexdigest()[:12]`, where `text` is:
- for a Transaction: `f"{investigation_id}:transaction:{number}|{date or '?'}|{store or '?'}|{register or '?'}"`. `?` marks an unknown component. A placeholder's store is `?` when none of its references gave a store (BD26), and its register is always `?`. A placeholder never has a blank `""` component, because references never carry blanks.
- for the other types: `f"{investigation_id}:{type}:{number}"`.

The ID stays the same as long as the placeholder's key doesn't change, and it contains no card number (B13).

3.7 **Placeholder prefill (BD14):** the placeholder's known key components are always filled in. Unknown components (store when no reference gave one, register always) are `null`, so the form shows store as a missing required field. Other fields:

| Placeholder type | From | Single-value fields (only if all attached references agree) | Derived rows (one per qualifying reference, in a stable order: source document ID, then row position) |
|---|---|---|---|
| Transaction | R1 activation | `time` ← `activation.time` | none (the activation transaction is where the card was bought, not a tender) |
| Transaction | R2a history entry | `time` | one payment row `{type: "gift_card", gift_card_number: <the card>, amount_cents: −(history.amount_cents)}`. If the history amount is blank, `amount_cents` is `null` |
| Transaction | R5 Misc | none | none |
| Gift Card | R2b Transaction payment | none | one history row `{transaction_number, date, time, store_number}` copied from the paying Transaction, with `amount_cents: −(payment.amount_cents)` |
| Gift Card | R3 / R4 order or Misc payments | none | none (history rows can only reference transactions, BD17) |
| Online Order | R6 Misc | none | none |

The `−(...)` is the sign flip from BD25. Activation details are never prefilled on a Gift Card placeholder, because no reference tells the backend how the card was activated.

**Worked example (BD25).** Transaction `00482913` (03-14-2026, store 042) has a payment row `gift_card 6006491234567890123, amount_cents: -2500`: a $25.00 return loaded onto the card. No Gift Card document exists yet.
- The Gift Card placeholder `…0123` gets the history row `{transaction_number: "00482913", date: "2026-03-14", time: "18:05", store_number: "042", amount_cents: 2500}`, which is **+$25.00 on the card**.
- The opposite direction: a saved Gift Card has a history row for transaction `11112222` (05-01-2026, store 042) with `amount_cents: -4000` (it spent $40.00), and no such Transaction exists. The Transaction placeholder gets the payment row `{type: "gift_card", gift_card_number: "6006491234567890123", amount_cents: 4000}`, which is **+$40.00 paid by that tender**.

3.8 **Promotion:** POSTing a real document makes the references that match it resolve to it on the next read (3.4 runs before 3.5), and the placeholder disappears once nothing is attached to it.
- The user must fill in the store if the placeholder didn't know it (BD26). Any store matches the references that had no store.
- If the user keeps the prefilled key parts and adds a register number, the references still match, because they don't know the register.
- If the user changes a prefilled date or store, the references no longer match and the placeholder stays. That is correct: the documents disagree, and the agent can see it.
- The promoted document's node takes over the placeholder's saved position (BD37). That happens in `document_service`, not here: `resolve` stays pure and knows nothing about positions ([node-positions.md](node-positions.md) 8.6).

3.9 **Edge merging:** links with the same `(source, target, kind)` merge into one edge. `refs`: the distinct `ref` values, sorted. `ref_count`: the number of underlying references. `match`: `"exact"` if **any** underlying reference matched this target uniquely, otherwise `"ambiguous"`.

Example: card X's history is ambiguous between transactions A and B, and A's own payment row uses card X (R2b, always exact). Then the X→A edge is `exact` with `refs: ["gift_card_history","payment"]`, and the X→B edge stays `ambiguous`.

3.10 **Edge status:** `incomplete` if either end is a placeholder or `match == "ambiguous"` (B5, BD15). Otherwise `complete`.

3.11 **`referenced_by`:** on each document, the distinct referencing documents, with `match` set as in 3.9.

3.12 **Determinism:** nodes are ordered by type (transaction, gift_card, online_order, misc), then by key tuple or name, then by ID. Edges are ordered by ID. The same data always gives identical output.

3.13 Resolution never raises an exception because of data content.

3.14 **Relating amounts (BD25).** All amount relationships go through one helper, `services/money.py: card_view(payment_amount_cents) -> int`, which returns `-payment_amount_cents`. Prefill (3.7) uses it, and so must any future feature that shows an amount on an edge, sums amounts across a card and its transactions, or compares a history amount with a payment amount (for example a check that history `+2500` agrees with payment `-2500`). Code must never compare a card-view amount with a transaction-view amount directly. v1 shows no amounts on edges and runs no amount checks (BD19). If either is added later, edge amounts are shown in **card view** for `activated` and `used_in` edges.

## Acceptance criteria
- [ ] Every row of the matching table in 3.3 produces exactly the stated result.
- [ ] Ambiguous references produce one edge per candidate, with `match: "ambiguous"`, `status: "incomplete"` and classes including `incomplete ambiguous`. No error status.
- [ ] An ambiguous X→A history edge that is also confirmed by A's own payment with card X becomes `match: "exact"` and `complete`.
- [ ] An activation `(11112222, 2026-05-01, 042)` and a Misc `11112222`, with no saved match, produce exactly one placeholder, prefilled with number, date, store and the activation time. Both are listed in `referenced_by`.
- [ ] POSTing `(11112222, 2026-05-01, 042, 003)` removes that placeholder, and both edges point at the new document as `complete`. POSTing `(11112222, 2026-05-02, 042, "")` instead leaves the placeholder in place (the dates disagree).
- [ ] A history reference with no store and no saved match produces a Transaction placeholder with `store_number: null`, and its title has no store part. POSTing the real Transaction with any store (and the same number and date) promotes it.
- [ ] **Sign convention (BD25):** a Transaction with the gift card payment `-2500` and no Gift Card document produces a Gift Card placeholder whose history has one row for that transaction with `amount_cents: 2500`. A gift card payment of `+4000` gives a history row of `-4000`. A saved Gift Card with a history row of `-4000` for a missing transaction produces a Transaction placeholder with the payment row `{type: "gift_card", gift_card_number: <card>, amount_cents: 4000}`. A history row with a blank amount gives a payment row with `amount_cents: null`. `card_view(-2500) == 2500`, `card_view(4000) == -4000`, `card_view(0) == 0`. No other module negates an amount (checked by code review).
- [ ] Deleting a matched Transaction brings back the placeholder or the ambiguous links. Deleting the only referencer removes the placeholder.
- [ ] Placeholder IDs stay the same between calls and contain no card numbers.

## Course requirements
See [../project/requirements.md](../project/requirements.md).
Traces: FR-04, FR-08, FR-10 (full map in [../project/traceability.md](../project/traceability.md)). Importance (BD27) needs nothing from resolution; it is applied in graph output (4.3, 4.4). Still open:
- F13: transaction-to-transaction links, possibly a future R7.
- F10: a performance target, because B11 says investigations are small.

## Resolved follow-ups
- **F2. Reverse-direction prefill — confirmed by the user (2026-11-17).** Along with the flip from a transaction's gift card payment into a placeholder card's history, 3.7 also does the reverse: a gift card history entry prefills a gift card payment row on a placeholder Transaction, with the sign flipped. The 3.7 table row and the matching acceptance criterion above stay as written.
