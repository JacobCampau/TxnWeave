"""Document and investigation endpoints (api.md, persistence.md acceptance criteria)."""

CARD = "6006491234567890123"


def transaction(number="00482913", on="2026-03-14", store="042", register=None, payments=None, **extra):
    return {
        "type": "transaction",
        "transaction_number": number,
        "date": on,
        "time": "18:05",
        "store_number": store,
        "register_number": register,
        "payments": payments if payments is not None else [{"type": "cash", "gift_card_number": None, "amount_cents": 2500}],
        "notes": None,
        **extra,
    }


def gift_card(number=CARD, history=()):
    return {
        "type": "gift_card",
        "gift_card_number": number,
        "activation": {"transaction_number": "11112222", "date": "2026-05-01", "time": "09:41", "store_number": "042"},
        "history": list(history),
    }


def docs_url(investigation_id):
    return f"/api/investigations/{investigation_id}/documents"


# ---- Investigations ----


def test_create_list_rename_and_delete_an_investigation(client):
    created = client.post("/api/investigations", json={"name": "  Case 1  "})
    assert created.status_code == 201
    inv = created.json()
    assert inv["name"] == "Case 1" and inv["document_count"] == 0 and inv["has_unsaved_changes"] is False

    renamed = client.patch(f"/api/investigations/{inv['id']}", json={"name": "   "}).json()
    assert renamed["name"] is None  # blank becomes null (BD32)
    assert client.patch(f"/api/investigations/{inv['id']}", json={"name": "x" * 201}).status_code == 422

    assert [i["id"] for i in client.get("/api/investigations").json()] == [inv["id"]]
    assert client.delete(f"/api/investigations/{inv['id']}").status_code == 204
    assert client.get(f"/api/investigations/{inv['id']}").status_code == 404


def test_list_is_newest_first(client):
    first = client.post("/api/investigations", json={}).json()["id"]
    second = client.post("/api/investigations", json={}).json()["id"]
    client.post(docs_url(first), json=transaction())  # touches `first`
    assert [i["id"] for i in client.get("/api/investigations").json()] == [first, second]


def test_counts_and_unsaved_changes(client, investigation_id):
    client.post(docs_url(investigation_id), json=gift_card())
    inv = client.get(f"/api/investigations/{investigation_id}").json()
    assert inv["document_count"] == 1
    assert inv["incomplete_count"] == 1  # the activation transaction is missing
    assert inv["has_unsaved_changes"] is True  # never exported (B16)


# ---- Create, read, update, delete ----


def test_create_and_get_a_transaction(client, investigation_id):
    response = client.post(docs_url(investigation_id), json=transaction(register="003"))
    assert response.status_code == 201
    doc = response.json()
    assert doc["status"] == "complete"
    assert doc["title"] == "Transaction 00482913 · 03-14-2026 · Store 042 · Reg 003"
    assert doc["payments"] == [{"type": "cash", "gift_card_number": None, "amount_cents": 2500}]
    assert client.get(f"{docs_url(investigation_id)}/{doc['id']}").json()["title"] == doc["title"]


def test_blank_optional_fields_become_null(client, investigation_id):
    doc = client.post(docs_url(investigation_id), json=transaction(register="  ", notes="")).json()
    assert doc["register_number"] is None and doc["notes"] is None


def test_put_replaces_the_document_and_type_cannot_change(client, investigation_id):
    doc = client.post(docs_url(investigation_id), json=transaction()).json()
    url = f"{docs_url(investigation_id)}/{doc['id']}"
    updated = client.put(url, json=transaction(store="051", payments=[
        {"type": "credit_card", "gift_card_number": None, "amount_cents": 100},
        {"type": "other", "gift_card_number": None, "amount_cents": -50},
    ])).json()
    assert updated["store_number"] == "051" and [p["amount_cents"] for p in updated["payments"]] == [100, -50]

    changed_type = client.put(url, json=gift_card())
    assert changed_type.status_code == 422
    assert changed_type.json()["detail"]["code"] == "type_change_not_allowed"


def test_delete_a_document(client, investigation_id):
    doc = client.post(docs_url(investigation_id), json=transaction()).json()
    assert client.delete(f"{docs_url(investigation_id)}/{doc['id']}").status_code == 204
    assert client.get(docs_url(investigation_id)).json() == []


def test_unknown_investigation_or_document_is_404(client, investigation_id):
    assert client.get(docs_url(999)).status_code == 404
    assert client.get(f"{docs_url(investigation_id)}/999").status_code == 404
    assert client.delete(f"{docs_url(investigation_id)}/abc").status_code == 404


# ---- Uniqueness (persistence.md acceptance criteria) ----


def test_composite_transaction_uniqueness(client, investigation_id):
    url = docs_url(investigation_id)
    first = client.post(url, json=transaction(register="003")).json()

    again = client.post(url, json=transaction(register="003"))
    assert again.status_code == 409
    assert again.json()["detail"] == {
        "code": "duplicate_key",
        "message": "A transaction with this number, date, store and register already exists.",
        "existing_id": first["id"],
    }

    # Changing only the register (or leaving it blank), the store, or the date is accepted.
    assert client.post(url, json=transaction(register="007")).status_code == 201
    assert client.post(url, json=transaction(register=None)).status_code == 201
    assert client.post(url, json=transaction(store="051", register="003")).status_code == 201
    assert client.post(url, json=transaction(on="2026-03-15", register="003")).status_code == 201
    # Two blank registers with the same key clash.
    assert client.post(url, json=transaction(register=None)).status_code == 409


def test_same_key_in_another_investigation_is_fine(client, investigation_id):
    other = client.post("/api/investigations", json={}).json()["id"]
    assert client.post(docs_url(investigation_id), json=transaction()).status_code == 201
    assert client.post(docs_url(other), json=transaction()).status_code == 201


def test_gift_card_numbers_are_unique_and_the_message_hides_the_number(client, investigation_id):
    url = docs_url(investigation_id)
    assert client.post(url, json=gift_card()).status_code == 201
    again = client.post(url, json=gift_card())
    assert again.status_code == 409 and CARD not in again.text


def test_updating_a_document_onto_its_own_key_is_not_a_duplicate(client, investigation_id):
    doc = client.post(docs_url(investigation_id), json=transaction()).json()
    assert client.put(f"{docs_url(investigation_id)}/{doc['id']}", json=transaction(notes="x")).status_code == 200


# ---- Validation ----


def test_invalid_bodies_are_422_without_echoing_input(client, investigation_id):
    url = docs_url(investigation_id)
    bad_card = transaction(payments=[{"type": "gift_card", "gift_card_number": "12ab" + CARD, "amount_cents": 100}])
    response = client.post(url, json=bad_card)
    assert response.status_code == 422
    assert CARD not in response.text and all("input" not in e for e in response.json()["detail"])

    assert client.post(url, json=transaction(time="24:00")).status_code == 422
    assert client.post(url, json=transaction(on="2026-02-30")).status_code == 422
    assert client.post(url, json=transaction(payments=[])).status_code == 422
    float_amount = transaction(payments=[{"type": "cash", "gift_card_number": None, "amount_cents": 25.5}])
    assert client.post(url, json=float_amount).status_code == 422
    cash_with_card = transaction(payments=[{"type": "cash", "gift_card_number": "123", "amount_cents": 1}])
    assert client.post(url, json=cash_with_card).status_code == 422
    assert client.post(url, json={**transaction(), "surprise": 1}).status_code == 422
    negative_activation = gift_card()
    negative_activation["activation"]["amount_cents"] = -1
    assert client.post(url, json=negative_activation).status_code == 422


# ---- Placeholders through the API ----


def test_list_includes_placeholders_with_referenced_by(client, investigation_id):
    url = docs_url(investigation_id)
    card = client.post(url, json=gift_card(history=[
        {"transaction_number": "00482913", "date": "2026-03-14", "time": "18:05", "store_number": "042", "amount_cents": -4000},
    ])).json()

    listed = client.get(url).json()
    placeholders = [d for d in listed if d["status"] == "incomplete"]
    assert sorted(p["title"] for p in placeholders) == [
        "Transaction 00482913 · 03-14-2026 · Store 042",
        "Transaction 11112222 · 05-01-2026 · Store 042",
    ]
    history_ph = next(p for p in placeholders if p["transaction_number"] == "00482913")
    assert history_ph["payments"] == [{"type": "gift_card", "gift_card_number": CARD, "amount_cents": 4000}]
    assert history_ph["referenced_by"] == [{"id": card["id"], "type": "gift_card", "title": "Gift Card …0123", "match": "exact"}]
    assert history_ph["created_at"] is None

    # Filters.
    assert [d["status"] for d in client.get(url, params={"status": "complete"}).json()] == ["complete"]
    assert {d["type"] for d in client.get(url, params={"type": "gift_card"}).json()} == {"gift_card"}

    # Placeholders can be read but not changed or deleted.
    ph_url = f"{url}/{history_ph['id']}"
    assert client.get(ph_url).json()["id"] == history_ph["id"]
    assert client.put(ph_url, json=transaction()).json()["detail"]["code"] == "placeholder_not_editable"
    assert client.delete(ph_url).status_code == 409

    # Saving the real document promotes it: the placeholder disappears.
    real = client.post(url, json=transaction(payments=[{"type": "gift_card", "gift_card_number": CARD, "amount_cents": 4000}])).json()
    ids = [d["id"] for d in client.get(url).json()]
    assert history_ph["id"] not in ids and real["id"] in ids
    assert {r["id"] for r in client.get(f"{url}/{real['id']}").json()["referenced_by"]} == {card["id"]}


def test_list_order_is_type_then_key(client, investigation_id):
    url = docs_url(investigation_id)
    client.post(url, json=gift_card())
    client.post(url, json=transaction(number="2"))
    client.post(url, json=transaction(number="1"))
    titles = [d["title"] for d in client.get(url).json()]
    assert titles == [
        "Transaction 1 · 03-14-2026 · Store 042",
        "Transaction 11112222 · 05-01-2026 · Store 042",  # placeholder, sorted in by key
        "Transaction 2 · 03-14-2026 · Store 042",
        "Gift Card …0123",
    ]
