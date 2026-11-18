# Backend: Data Model

- **Status:** Agreed (from `backend-graphing-design.md` v3). Updated 2026-11-17 (user decisions): the `important` field (BD27) and the investigation settings schema (BD29).
- **Scope:** The authoritative field types and validation rules for every document type (Transaction, Gift Card, Online Order, Misc), the repeatable Payment and Gift Card history rows, natural keys and the Transaction key tuple, document titles, and how the Pydantic `*In` / `*Out` schemas are split. Also records how this design resolved inconsistencies in the planning notes. The Investigation entity is in [api.md](api.md).
- **Master plan:** [../master-plan.md](../master-plan.md) (cross-cutting B6, B7, B8, B15, BD25 live there)
- **Related:** [persistence.md](persistence.md) (tables for these fields), [relationship-resolution.md](relationship-resolution.md) (how keys are matched), [api.md](api.md) (endpoints using these schemas), [../ui/documents-page.md](../ui/documents-page.md) (the form view of these fields)

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| B14 | **Natural keys, unique within an investigation:** **Transaction = (transaction_number, date, store_number, register_number)**. Online Order = `order_number`. Gift Card = `gift_card_number`. Misc has no key. A duplicate on create or update returns `409` with `existing_id` | User decision: a transaction number repeats across stores, registers and days. Order and card numbers are unique across the retailer by their nature, so they keep single-number keys | The number alone (rejected by the user) |
| BD1 | **In a saved Transaction's identity, a blank register number counts as the empty value `""`, which matches exactly.** `(00482913, 2026-03-14, "042", "")` and `(00482913, 2026-03-14, "042", "003")` are different transactions. Store number can never be blank (BD26) | The user asked for exact matching of missing values. It keeps uniqueness well defined while register stays optional | Make register required; treat a blank register as a wildcard in uniqueness (then two documents could each "cover" the other) |
| BD5 | Gift card numbers allow 1 to 24 digits | Accepted default (OQ-2) | A fixed length |
| BD16 | An amount is required on every payment row. Misc node names don't need to be unique | Accepted assumptions A1 and A6 | — |
| BD17 | Online orders can't appear in gift card history. History entries reference transactions only | Accepted default (OQ-14) | — |
| BD24 | The backend Transaction `title` includes the other identity parts: `Transaction 00482913 · 03-14-2026 · Store 042 · Reg 003`. A blank register is left out. On a placeholder, unknown parts are left out | Two transactions can now share a number, so `Transaction <number>` alone would give duplicate list titles. User confirmed (v3). The matching page-and-ui-layout change is follow-up F1 | Keep the number-only title |
| BD26 | **Store number is required on Transaction documents.** Register number stays optional. References (activation, history, Misc) may still leave store blank, meaning "unknown" (BD2). A Transaction placeholder created from a reference with no store keeps store unknown (`null`) until the real document is saved | User decision (v3). Removes the case where a reference that gives a store could never match a saved transaction with a blank store | Optional store with blank counting as `""` (v2) |
| BD29 | **Investigation settings schema** (UI choices in D27). Colors are stored and sent as **palette token names**, never hex. `InvestigationSettingsIn` is a **full replacement**: all four type styles and the edge color are required. **Validation:** two document types with the same `(color, shape)` return 422 with code `indistinct_styles` and the list of clashing types. The defaults are D9's styles, with `important_edge_color: "ink"` | Token names keep hex out of everything except `palette.ts` and `global.css` (color-system). Full replacement makes the distinctness check simple | Hex values; partial PATCH of single types |

## General rules
"digits(1..N)" means a string matching `^[0-9]{1,N}$`. Strings are trimmed of surrounding whitespace before validation. An empty string on an optional field is stored and returned as `null`.

## Shared value types
| Name | Python (Pydantic) | TypeScript | Rule | Example |
|---|---|---|---|---|
| `TxnNumber` | `Annotated[str, StringConstraints(pattern=r"^[0-9]{1,8}$")]` | `string` | digits(1..8) | `"00482913"` |
| `OrderNumber` | same | `string` | digits(1..8) | `"77120045"` |
| `GiftCardNumber` | pattern `^[0-9]{1,24}$` | `string` | digits(1..24) | `"6006491234567890123"` |
| `StoreNumber` | pattern `^[0-9]{1,3}$` | `string` | digits(1..3) | `"042"` |
| `RegisterNumber` | pattern `^[0-9]{1,3}$` | `string` | digits(1..3) | `"003"` |
| `IsoDate` | `datetime.date` | `string` (`YYYY-MM-DD`) | must be a real calendar date | `"2026-03-14"` |
| `Time24` | pattern `^([01][0-9]\|2[0-3]):[0-5][0-9]$` | `string` | `00:00` to `23:59` | `"18:05"` |
| `AmountCents` | `Annotated[int, Field(ge=-9_999_999, le=9_999_999, strict=True)]` | `number` (integer) | -$99,999.99 to $99,999.99. `0` is allowed. Floats and strings are rejected. Used for payment and history amounts. The sign follows BD25 | `-2550` (a $25.50 return, in transaction view) |
| `ActivationAmountCents` | `Annotated[int, Field(ge=0, le=9_999_999, strict=True)]` | `number` (integer) | $0.00 to $99,999.99, card view (BD25) | `50000` |
| `StateCode` | pattern `^[A-Z]{2}$`, uppercased before validation | `string` | | `"WI"` |
| `ShortText` | `str`, 1 to 200 characters | `string` | | `"Suspicious return"` |
| `Notes` | `str \| None`, at most 10,000 characters | `string \| null` | | |
| `PaymentType` | `Literal["credit_card","gift_card","cash","other"]` | union | | |
| `DocumentType` | `Literal["transaction","gift_card","online_order","misc"]` | union | | |
| `DocumentStatus` | `Literal["complete","incomplete"]` | union | `incomplete` only for placeholders | |
| `DocumentId` | `str` | `string` | A saved document is its integer ID as a string. A placeholder is `"ph-<type>-<12 hex>"` ([relationship-resolution](relationship-resolution.md) 3.6) | `"12"` |

## Payment (repeatable row)
| Field | Type | Required | Rule |
|---|---|---|---|
| `type` | `PaymentType` | yes | |
| `gift_card_number` | `GiftCardNumber \| None` | only when `type == "gift_card"` | Must be `null` for every other type, or the API returns 422 |
| `amount_cents` | `AmountCents` | yes | **Transaction view** (BD25): positive = paid with this tender, negative = returned to this tender. A $25.00 return loaded onto a gift card is `{"type":"gift_card", ..., "amount_cents": -2500}` |

Rows keep the order the user entered them in (`position`).

## Transaction
| Field | Type | Required | Part of the key? | Example |
|---|---|---|---|---|
| `transaction_number` | `TxnNumber` | yes | yes | `"00482913"` |
| `date` | `IsoDate` | yes | yes | `"2026-03-14"` |
| `time` | `Time24` | yes | no | `"18:05"` |
| `store_number` | `StoreNumber` | **yes** (BD26) | yes | `"042"` |
| `register_number` | `RegisterNumber \| None` | no | yes (blank counts as `""`, BD1) | `"003"` |
| `payments` | `list[Payment]`, at least 1 | yes | no | |
| `notes` | `Notes` | no | no | |

**Transaction key tuple** (used for uniqueness and for matching): `(transaction_number, date.isoformat(), store_number, register_number or "")`.

## Gift Card
| Field | Type | Required |
|---|---|---|
| `gift_card_number` | `GiftCardNumber` | yes, key |
| `activation.transaction_number` | `TxnNumber` | yes |
| `activation.date` | `IsoDate` | yes |
| `activation.time` | `Time24` | yes |
| `activation.store_number` | `StoreNumber \| None` | no |
| `activation.amount_cents` | `ActivationAmountCents \| None` | no (0 or more, card view) |
| `history` | `list[GiftCardHistoryEntry]`, 0 or more | no |
| `notes` | `Notes` | no |

**GiftCardHistoryEntry:** `transaction_number: TxnNumber` (required), `date: IsoDate` (required), `time: Time24` (required), `store_number: StoreNumber | None`, `amount_cents: AmountCents | None`. `amount_cents` is in **card view** (BD25): positive = value put onto the card in that transaction (for example a return credited to the card), negative = value spent from the card. Entries keep their order (`position`).

## Online Order
| Field | Type | Required |
|---|---|---|
| `order_number` | `OrderNumber` | yes, key |
| `placed_date` | `IsoDate` | yes |
| `placed_time` | `Time24` | yes |
| `customer_city` | `ShortText \| None` | no |
| `customer_state` | `StateCode \| None` | no |
| `pickup_store_number` | `StoreNumber \| None` | no |
| `payments` | `list[Payment]`, at least 1 | yes |
| `notes` | `Notes` | no |

## Misc
| Field | Type | Required |
|---|---|---|
| `name` | `ShortText` | yes (not unique) |
| `date` | `IsoDate` | yes |
| `time` | `Time24` | yes |
| `transaction_number` | `TxnNumber \| None` | no (a number-only reference, see R5) |
| `order_number` | `OrderNumber \| None` | no (a reference) |
| `payments` | `list[Payment]`, 0 or more | no |
| `notes` | `Notes` | no |

## Pydantic schema split (`schemas/`)
- Every `*In` model has `important: bool = False` (BD27). PUT replaces the whole document, so the client always sends the current value. Every `*Out` model has `important: bool`, which is always `false` for placeholders.
- `*In` models are **strict**: every required field is required. Used for POST and PUT bodies. `DocumentIn = Annotated[TransactionIn | GiftCardIn | OnlineOrderIn | MiscIn, Field(discriminator="type")]`.
- `*Out` models have the same fields, all optional, plus `id`, `investigation_id`, `type`, `status`, `title`, `referenced_by: list[DocumentRef]`, `created_at`, `updated_at` (`null` for placeholders).
- `DocumentRef = {id: DocumentId, type: DocumentType, title: str, match: "exact" | "ambiguous"}`. `match` tells the delete warning and the PropertyPanel whether the referencing document points at this one alone or at it and others.
- `title`:
  - Transaction: per BD24.
  - Gift Card: `Gift Card …<last 4>`.
  - Online Order: `Online Order <number>`.
  - Misc: `<name>`.

## Investigation settings (BD29)
| Name | Python (Pydantic) | TypeScript | Example |
|---|---|---|---|
| `NodeColorToken` | `Literal["ink","slate","mist","rose","crimson"]` | union | `"crimson"` |
| `EdgeColorToken` | `Literal["ink","slate","crimson"]` | union | `"ink"` |
| `NodeShape` | `Literal["ellipse","rectangle","round-rectangle","triangle","diamond","hexagon","octagon","star"]` | union | `"hexagon"` |
| `TypeStyle` | `{color: NodeColorToken, shape: NodeShape}` | interface | `{"color":"slate","shape":"ellipse"}` |
| `InvestigationSettingsIn` | `{node_styles: {transaction, gift_card, online_order, misc: TypeStyle}, important_edge_color: EdgeColorToken}`, every key required | interface | |
| `InvestigationSettingsOut` | `InvestigationSettingsIn` fields plus `is_default: bool` (true when the effective values equal the defaults) | interface | |

**Defaults:** transaction `slate`/`ellipse`, gift_card `crimson`/`round-rectangle`, online_order `ink`/`hexagon`, misc `rose`/`diamond`, important_edge_color `ink`.

## Validation behavior
- 2.9 Negative and zero amounts are accepted on payment and history rows. Payment totals may be negative. A negative activation amount returns 422 (BD25). The backend stores each amount exactly as entered, in its own document's point of view, and never flips a sign on write. Flipping happens only when the backend relates two documents ([relationship-resolution](relationship-resolution.md) 3.7, 3.14).
- 2.10 A Transaction without a store number returns 422 (BD26).

(Behaviors 2.1 to 2.8 are in [api.md](api.md).)

## Plan inconsistencies and how this design resolves them
| Source line in `initial-plans.md` | Problem | Resolution |
|---|---|---|
| L36 `activation date*: DD-YYYY`, L45 `date*: DD-YYYY` | Contradicts `MM-DD-YYYY` on L23, L52 and L63 | A typo for `MM-DD-YYYY` (D18). Stored as ISO (B8) |
| L22, L32, L35, L44, L52, L65, L66: number fields typed `INT` | Overflow, and lost leading zeros | Digits-only strings (B6) |
| L32 24 X's for a gift card number | Real cards are often 16 or 19 digits | 1 to 24 digits (BD5) |
| L24, L37, L46, L53 `time*: 2400` | `24:00` is not a valid time | `HH:MM`, `00:00` to `23:59` |
| L28, L39, L48: `$XXX.XX REAL` vs `$XXXX.XX REAL` | Two different caps, and float money | Integer cents with a $99,999.99 magnitude cap. Payments and history are signed, activation is 0 or more, and the sign convention is BD25 (B7) |
| L54 / L55 state `TEXT`, city `XX TEXT` | The `XX` belongs to state | State is 2 uppercase letters, city is free text |
| L57, L67 "added to a single transaction" | Copied text | Payments belong to any document type that has them |
| L57 `payment type*` vs L67 Misc `payments:` | Is a payment required? | At least 1 for Transaction and Online Order, 0 or more for Misc |
| L72 "and vice versa" | A Transaction has no field that records which card it activated | Completeness depends on node existence (B5, BD18). Two-way confirmation is recorded in `refs` |
| L80 "a new sheet for each node type" | CSV has no sheets | A sectioned single CSV (BD9) |
| L22 "Transaction number" treated as the identifier (implied by L72) | The number repeats across stores, registers and days (user answer) | Composite key (B14), partial-reference matching ([relationship-resolution](relationship-resolution.md) section 3) |

## Acceptance criteria
- [ ] A Transaction with a 24-digit gift card payment and a leading-zero transaction number stores and returns both strings unchanged.
- [ ] Payment and history `amount_cents` accept `-9999999`, `0` and `9999999`. They reject `-10000000`, `10000000`, `25.5` and `"2550"` with 422.
- [ ] `activation.amount_cents` accepts `0` and `9999999` and rejects `-1` with 422.
- [ ] A Transaction with a missing or empty `store_number` returns 422. A Transaction with no `register_number` is accepted.
- [ ] A `cash` payment with a `gift_card_number` returns 422. A `gift_card` payment without one returns 422.
- [ ] Transaction and Online Order with 0 payments return 422. Misc with 0 payments is accepted.
- [ ] `2026-02-30` and `24:00` return 422.
- [ ] Saving and then reading back any document returns every amount with the sign it was saved with.

- [ ] A document saved without `important` reads back `important: false`. A placeholder always has `important: false`.
- [ ] `InvestigationSettingsIn` rejects a hex value, an unknown shape, `"rose"` as the important-edge color, and two types with the same color and shape (422 `indistinct_styles`).

## Course requirements
Traces: FR-03 to FR-06, FR-12, FR-13, FR-14, UC08 (full map in [../project/traceability.md](../project/traceability.md)). Still open:
- F12: FR-06 "description" maps to Notes.
- F14: interview Q3 asks for personal-information fields.
