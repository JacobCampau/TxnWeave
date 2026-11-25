"""Investigation settings endpoints (api.md section 7, BD29 to BD31)."""

import copy

DEFAULTS = {
    "node_styles": {
        "transaction": {"color": "slate", "shape": "ellipse"},
        "gift_card": {"color": "crimson", "shape": "round-rectangle"},
        "online_order": {"color": "ink", "shape": "hexagon"},
        "misc": {"color": "rose", "shape": "diamond"},
    },
    "important_edge_color": "ink",
}


def settings_url(investigation_id):
    return f"/api/investigations/{investigation_id}/settings"


def custom():
    body = copy.deepcopy(DEFAULTS)
    body["node_styles"]["misc"] = {"color": "mist", "shape": "star"}
    body["important_edge_color"] = "crimson"
    return body


def test_get_returns_the_defaults_when_nothing_was_saved(client, investigation_id):
    response = client.get(settings_url(investigation_id))
    assert response.status_code == 200
    assert response.json() == {**DEFAULTS, "is_default": True}


def test_put_saves_and_get_returns_the_saved_values(client, investigation_id):
    saved = client.put(settings_url(investigation_id), json=custom())
    assert saved.status_code == 200
    assert saved.json() == {**custom(), "is_default": False}
    assert client.get(settings_url(investigation_id)).json() == {**custom(), "is_default": False}


def test_saving_the_default_values_reports_is_default(client, investigation_id):
    assert client.put(settings_url(investigation_id), json=DEFAULTS).json()["is_default"] is True


def test_put_counts_as_a_change(client, investigation_id):
    before = client.get(f"/api/investigations/{investigation_id}").json()["updated_at"]
    client.put(settings_url(investigation_id), json=custom())
    after = client.get(f"/api/investigations/{investigation_id}").json()["updated_at"]
    assert after > before


def test_put_rejects_a_hex_color_a_rose_edge_and_a_missing_type(client, investigation_id):
    hex_color = custom()
    hex_color["node_styles"]["misc"]["color"] = "#C11E20"
    rose_edge = custom()
    rose_edge["important_edge_color"] = "rose"
    missing = custom()
    del missing["node_styles"]["gift_card"]
    for body in (hex_color, rose_edge, missing):
        assert client.put(settings_url(investigation_id), json=body).status_code == 422


def test_put_rejects_two_types_that_look_the_same(client, investigation_id):
    body = custom()
    body["node_styles"]["misc"] = {"color": "slate", "shape": "ellipse"}  # same as transaction
    response = client.put(settings_url(investigation_id), json=body)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "indistinct_styles"
    assert sorted(detail["types"]) == ["misc", "transaction"]
    # Nothing was saved.
    assert client.get(settings_url(investigation_id)).json()["is_default"] is True


def test_delete_resets_to_the_defaults(client, investigation_id):
    client.put(settings_url(investigation_id), json=custom())
    reset = client.delete(settings_url(investigation_id))
    assert reset.status_code == 200
    assert reset.json() == {**DEFAULTS, "is_default": True}
    assert client.get(settings_url(investigation_id)).json()["is_default"] is True


def test_unknown_investigation_returns_404(client):
    assert client.get(settings_url(999)).status_code == 404
    assert client.put(settings_url(999), json=DEFAULTS).status_code == 404
    assert client.delete(settings_url(999)).status_code == 404


def test_deleting_the_investigation_removes_its_settings(client, investigation_id):
    client.put(settings_url(investigation_id), json=custom())
    assert client.delete(f"/api/investigations/{investigation_id}").status_code == 204
    # SQLite may reuse the deleted id, so a leftover row would show up on the new investigation.
    new_id = client.post("/api/investigations", json={}).json()["id"]
    assert client.get(settings_url(new_id)).json()["is_default"] is True
