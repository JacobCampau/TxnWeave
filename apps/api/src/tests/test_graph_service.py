"""GET /graph and graph_service, checked against graph-output.md (behavior 4.x and the
acceptance criteria) and the edge rules in relationship-resolution.md (3.2, 3.9, 3.10)."""

CARD = "6006491234567890123"


def transaction(number="00482913", on="2026-03-14", store="042", card=None, important=False):
    payment = {"type": "gift_card", "gift_card_number": card, "amount_cents": 2500} if card else {
        "type": "cash", "amount_cents": 2500
    }
    return {
        "type": "transaction", "transaction_number": number, "date": on, "time": "18:05",
        "store_number": store, "payments": [payment], "important": important,
    }


def gift_card(number=CARD, activated_by="11112222", history=(), important=False):
    return {
        "type": "gift_card", "gift_card_number": number,
        "activation": {"transaction_number": activated_by, "date": "2026-03-14", "time": "09:41", "store_number": "042"},
        "history": list(history), "important": important,
    }


def misc(txn_number=None):
    return {"type": "misc", "name": "Suspect", "date": "2026-03-14", "time": "12:00", "transaction_number": txn_number}


def add(client, iid, doc) -> str:
    response = client.post(f"/api/investigations/{iid}/documents", json=doc)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def graph(client, iid) -> dict:
    response = client.get(f"/api/investigations/{iid}/graph")
    assert response.status_code == 200, response.text
    return response.json()


def edges_by_id(body) -> dict:
    return {edge["data"]["id"]: edge for edge in body["elements"]["edges"]}


def test_empty_investigation_returns_empty_lists(client, investigation_id):
    body = graph(client, investigation_id)
    assert body["elements"] == {"nodes": [], "edges": []}
    assert body["counts"] == {"nodes": 0, "edges": 0, "incomplete_nodes": 0}


def test_unknown_investigation_is_404(client):
    assert client.get("/api/investigations/999/graph").status_code == 404


def test_payment_with_an_unknown_card_makes_a_placeholder_and_a_dashed_edge(client, investigation_id):
    txn = add(client, investigation_id, transaction(card=CARD))
    response = client.get(f"/api/investigations/{investigation_id}/graph")
    assert CARD not in response.text  # B13: only the masked key leaves the backend

    body = response.json()
    txn_node, card_node = body["elements"]["nodes"]  # ordered by type (3.12)
    assert txn_node["data"]["id"] == txn and txn_node["classes"] == "transaction"
    assert card_node["data"]["display_key"] == "…0123"
    assert card_node["data"]["status"] == "incomplete" and card_node["classes"] == "gift-card incomplete"

    (edge,) = body["elements"]["edges"]
    # R2b: drawn Gift Card → Transaction, the other way round from the reference.
    assert edge["data"]["source"] == card_node["data"]["id"] and edge["data"]["target"] == txn
    assert edge["data"]["kind"] == "used_in" and edge["data"]["status"] == "incomplete"
    assert edge["classes"] == "used-in incomplete"
    assert body["counts"] == {"nodes": 2, "edges": 1, "incomplete_nodes": 1}


def test_activation_and_payment_edges_between_saved_documents(client, investigation_id):
    activating = add(client, investigation_id, transaction(number="11112222"))
    card = add(client, investigation_id, gift_card())
    spending = add(client, investigation_id, transaction(number="22223333", card=CARD))

    edges = edges_by_id(graph(client, investigation_id))
    activated = edges[f"e-activated-{activating}-{card}"]  # R1: Transaction → Gift Card
    assert activated["data"]["status"] == "complete" and activated["data"]["match"] == "exact"
    assert activated["classes"] == "activated"
    used = edges[f"e-used_in-{card}-{spending}"]
    assert used["data"]["refs"] == ["payment"] and used["data"]["ref_count"] == 1


def test_history_and_payment_for_the_same_pair_merge_into_one_edge(client, investigation_id):
    txn = add(client, investigation_id, transaction(card=CARD))
    history = [{"transaction_number": "00482913", "date": "2026-03-14", "time": "18:05", "store_number": "042"}]
    card = add(client, investigation_id, gift_card(history=history))

    used = [e for e in graph(client, investigation_id)["elements"]["edges"] if e["data"]["kind"] == "used_in"]
    assert len(used) == 1  # 3.9
    assert used[0]["data"]["id"] == f"e-used_in-{card}-{txn}"
    assert used[0]["data"]["refs"] == ["gift_card_history", "payment"] and used[0]["data"]["ref_count"] == 2


def test_ambiguous_reference_gives_dashed_ambiguous_edges(client, investigation_id):
    add(client, investigation_id, transaction(store="042"))
    add(client, investigation_id, transaction(store="043"))
    add(client, investigation_id, misc(txn_number="00482913"))  # R5 knows the number only

    edges = graph(client, investigation_id)["elements"]["edges"]
    assert len(edges) == 2
    for edge in edges:
        assert edge["data"]["match"] == "ambiguous" and edge["data"]["status"] == "incomplete"
        assert edge["classes"] == "related incomplete ambiguous"


def test_same_data_gives_identical_elements(client, investigation_id):
    add(client, investigation_id, gift_card())
    add(client, investigation_id, transaction(card=CARD))
    add(client, investigation_id, misc(txn_number="99990000"))
    assert graph(client, investigation_id)["elements"] == graph(client, investigation_id)["elements"]


def test_edge_is_important_only_when_both_ends_are(client, investigation_id):
    iid = investigation_id
    a = add(client, iid, transaction(card=CARD, important=True))
    b = add(client, iid, gift_card(important=True))
    c = add(client, iid, misc(txn_number="00482913"))  # not important

    body = graph(client, iid)
    nodes = {node["data"]["id"]: node for node in body["elements"]["nodes"]}
    assert nodes[a]["classes"] == "transaction important" and nodes[c]["data"]["important"] is False
    edges = edges_by_id(body)
    assert edges[f"e-used_in-{b}-{a}"]["data"]["important"] is True
    assert "important" in edges[f"e-used_in-{b}-{a}"]["classes"]
    assert edges[f"e-related-{c}-{a}"]["data"]["important"] is False

    # Un-marking A turns the A–B edge off on the next call (BD27).
    assert client.put(f"/api/investigations/{iid}/documents/{a}", json=transaction(card=CARD)).status_code == 200
    assert edges_by_id(graph(client, iid))[f"e-used_in-{b}-{a}"]["data"]["important"] is False


def test_edge_to_a_placeholder_is_never_important(client, investigation_id):
    add(client, investigation_id, transaction(card=CARD, important=True))
    (edge,) = graph(client, investigation_id)["elements"]["edges"]
    assert edge["data"]["important"] is False
