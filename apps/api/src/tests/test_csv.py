"""CSV Save and Load, checked against csv-save-load.md (acceptance criteria and 5.10)."""

CARD = "6006491234567890123"
MARKER = "TXNWEAVE_SAVE,format_version,1"


def transaction(number="00482913", store="042", notes=None, important=False, payments=None):
    return {
        "type": "transaction", "transaction_number": number, "date": "2026-03-14", "time": "18:05",
        "store_number": store, "notes": notes, "important": important,
        "payments": payments or [{"type": "gift_card", "gift_card_number": CARD, "amount_cents": -1250}],
    }


def gift_card(history=()):
    return {
        "type": "gift_card", "gift_card_number": CARD,
        "activation": {"transaction_number": "11112222", "date": "2026-03-01", "time": "09:41", "store_number": "042", "amount_cents": 5000},
        "history": list(history),
    }


def add(client, iid, doc):
    response = client.post(f"/api/investigations/{iid}/documents", json=doc)
    assert response.status_code == 201, response.text


def export(client, iid) -> str:
    response = client.get(f"/api/investigations/{iid}/export.csv")
    assert response.status_code == 200
    return response.content.decode("utf-8")


def load(client, text: str, dry_run: bool, filename="case.csv"):
    return client.post(
        f"/api/investigations/import?dry_run={str(dry_run).lower()}",
        files={"file": (filename, text.encode("utf-8"), "text/csv")},
    )


def minimal_file(*sections: str) -> str:
    return "\n".join([MARKER, "investigation_name,Loaded case,exported_at,2026-11-24T15:30:00Z", *sections]) + "\n"


TXN_SECTION = "\nsection,transactions\nref,transaction_number,date,time,store_number,register_number,important,notes\n"
PAY_SECTION = "\nsection,payments\nparent_ref,type,gift_card_number,amount ($)\n"


# ---- Export ----


def test_export_follows_the_layout_and_cell_rules(client, investigation_id):
    add(client, investigation_id, transaction(notes="-not a formula"))
    add(client, investigation_id, gift_card())
    response = client.get(f"/api/investigations/{investigation_id}/export.csv")
    assert response.headers["content-disposition"] == 'attachment; filename="untitled-investigation.csv"'
    text = response.content.decode("utf-8")

    assert text.startswith("﻿" + MARKER)  # BOM, then the marker (5.1, BD12)
    lines = text.lstrip("﻿").splitlines()
    assert lines[1].startswith("investigation_name,,exported_at,")
    assert "T1,00482913,03-14-2026,18:05,042,,false,'-not a formula" in lines  # escaped text
    assert "T1,gift_card,6006491234567890123,-12.50" in lines  # amounts are never escaped
    assert "G1,6006491234567890123,11112222,03-01-2026,09:41,042,50.00,false," in lines
    assert lines[-5:] == [
        "transaction,slate,ellipse", "gift_card,crimson,round-rectangle", "online_order,ink,hexagon",
        "misc,rose,diamond", "important_edge,ink,",
    ]  # settings last (BD33)


def test_export_clears_unsaved_changes(client, investigation_id):
    add(client, investigation_id, transaction())
    assert client.get(f"/api/investigations/{investigation_id}").json()["has_unsaved_changes"] is True
    export(client, investigation_id)
    assert client.get(f"/api/investigations/{investigation_id}").json()["has_unsaved_changes"] is False


def test_export_of_unknown_investigation_is_404(client):
    assert client.get("/api/investigations/999/export.csv").status_code == 404


# ---- Import ----


def test_round_trip_keeps_documents_importance_and_settings(client, investigation_id):
    iid = investigation_id
    client.patch(f"/api/investigations/{iid}", json={"name": "Store 042 ring"})
    add(client, iid, transaction(important=True, notes="=cmd"))
    add(client, iid, gift_card(history=[{"transaction_number": "00482913", "date": "2026-03-14", "time": "18:05", "store_number": "042", "amount_cents": 1250}]))
    styles = client.get(f"/api/investigations/{iid}/settings").json()
    styles["node_styles"]["misc"] = {"color": "slate", "shape": "star"}
    styles["important_edge_color"] = "crimson"
    del styles["is_default"]
    assert client.put(f"/api/investigations/{iid}/settings", json=styles).status_code == 200
    text = export(client, iid)

    dry = load(client, text, dry_run=True)
    assert dry.status_code == 200 and dry.json()["problems"] == []
    assert len(client.get("/api/investigations").json()) == 1  # the dry run wrote nothing

    loaded = load(client, text, dry_run=False)
    assert loaded.status_code == 201
    new = loaded.json()["investigation"]
    assert new["name"] == "Store 042 ring" and new["document_count"] == 2 and new["has_unsaved_changes"] is False

    def strip(doc):
        return {k: v for k, v in doc.items() if k not in {"id", "investigation_id", "created_at", "updated_at", "referenced_by"}}

    before = [strip(d) for d in client.get(f"/api/investigations/{iid}/documents").json()]
    after = [strip(d) for d in client.get(f"/api/investigations/{new['id']}/documents").json()]
    assert after == before  # same fields, signs, notes and important flags
    after_settings = client.get(f"/api/investigations/{new['id']}/settings").json()
    assert after_settings["node_styles"]["misc"] == {"color": "slate", "shape": "star"}
    assert after_settings["important_edge_color"] == "crimson"


def test_file_without_marker_is_rejected_for_both_modes(client):
    for text in ["", "ref,transaction_number\nT1,123\n", "TXNWEAVE_SAVE,format_version,2\n"]:
        for dry_run in (True, False):
            response = load(client, text, dry_run)
            assert response.status_code == 422
            assert response.json()["detail"]["code"] == "not_a_txnweave_file"
    assert client.get("/api/investigations").json() == []


def test_marker_padded_with_blank_cells_is_accepted(client):
    response = load(client, "TXNWEAVE_SAVE,format_version,1,,,\n", dry_run=True)
    assert response.status_code == 200 and response.json()["counts"]["documents_imported"] == 0


def test_non_utf8_and_oversized_files(client):
    bad = client.post("/api/investigations/import?dry_run=true", files={"file": ("x.csv", b"\xff\xfe\x00bad", "text/csv")})
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "unreadable_file"
    big = minimal_file() + ("x" * 5_000_001)
    assert load(client, big, dry_run=True).status_code == 413


def test_blank_store_skips_the_row_and_its_payments(client):
    text = minimal_file(
        TXN_SECTION + "T1,00482913,03-14-2026,18:05,,,false,\nT2,00482914,03-14-2026,18:06,042,,false,",
        PAY_SECTION + "T1,cash,,5.00\nT2,cash,,-25.50",
    )
    report = load(client, text, dry_run=True).json()
    codes = [(p["section"], p["row"], p["field"], p["code"]) for p in report["problems"]]
    assert ("transactions", 6, "store_number", "missing_required") in codes
    assert ("payments", 11, "parent_ref", "parent_skipped") in codes
    assert report["counts"] == {"rows_read": 4, "documents_imported": 1, "rows_skipped": 2}

    loaded = load(client, text, dry_run=False)
    assert loaded.status_code == 201  # content problems never give an error status (5.8)
    docs = client.get(f"/api/investigations/{loaded.json()['investigation']['id']}/documents").json()
    assert [d["transaction_number"] for d in docs] == ["00482914"]
    assert docs[0]["payments"][0]["amount_cents"] == -2550  # never flipped


def test_cell_problems_are_reported(client):
    text = minimal_file(
        TXN_SECTION + "T1,00482913,14/03/2026,18:05,042,,false,\nT2,00482913,03-14-2026,18:05,042,,maybe,",
        PAY_SECTION + "T1,cash,,5.00\nT2,cash,,25.505\nT2,cash,,1e3\nT9,cash,,1.00\nT2,cash,,'3.00",
        "\nsection,gift_cards\nref,gift_card_number,activation_transaction_number,activation_date,activation_time,activation_store_number,activation_amount ($),important,notes\n"
        "G1,6.00649E+18,11112222,03-01-2026,09:41,042,-5.00,false,",
        "\nsection,mystery\na,b\n1,2",
    )
    problems = load(client, text, dry_run=True).json()["problems"]
    found = {(p["field"], p["code"]) for p in problems}
    assert ("date", "invalid_format") in found
    assert ("important", "invalid_format") in found  # a warning: the row is still read
    assert ("amount ($)", "invalid_format") in found  # 25.505 and 1e3
    assert ("parent_ref", "unknown_parent_ref") in found  # T9
    assert any(p["code"] == "unknown_section" and p["section"] == "mystery" for p in problems)
    assert "6006" not in str(problems) and "E+18" not in str(problems)  # B13
    # The ' prefix is stripped, so '3.00 is a valid amount for T2.
    assert not any(p["section"] == "payments" and p["row"] == 15 for p in problems)


def test_negative_activation_is_out_of_range(client):
    text = minimal_file(
        "\nsection,gift_cards\nref,gift_card_number,activation_transaction_number,activation_date,activation_time,activation_store_number,activation_amount ($),important,notes\n"
        "G1,6006491234567890123,11112222,03-01-2026,09:41,042,-5.00,false,"
    )
    problems = load(client, text, dry_run=True).json()["problems"]
    assert [(p["field"], p["code"]) for p in problems] == [("activation_amount ($)", "out_of_range")]


def test_duplicate_key_keeps_the_first_row(client):
    text = minimal_file(
        TXN_SECTION + "T1,00482913,03-14-2026,18:05,042,,false,\nT2,00482913,03-14-2026,18:20,042,,false,",
        PAY_SECTION + "T1,cash,,5.00\nT2,cash,,6.00",
    )
    problems = load(client, text, dry_run=True).json()["problems"]
    assert [(p["row"], p["code"]) for p in problems] == [(7, "duplicate_key"), (12, "parent_skipped")]
    assert problems[0]["message"].startswith("Duplicate of row 6 (Transaction 00482913")


def test_missing_column_and_settings_problems(client):
    text = minimal_file(
        "\nsection,transactions\nref,transaction_number,date,time,register_number\nT1,00482913,03-14-2026,18:05,",
        PAY_SECTION + "T1,cash,,5.00",
        "\nsection,settings\nsetting,color,shape\nmisc,purple,diamond\ntransaction,slate,ellipse\ntransaction,ink,star",
    )
    problems = load(client, text, dry_run=True).json()["problems"]
    found = [(p["section"], p["field"], p["code"]) for p in problems]
    assert ("transactions", "store_number", "missing_required") in found
    assert [code for section, _, code in found if section == "settings"] == ["invalid_setting", "invalid_setting"]


def test_indistinct_settings_revert_node_styles(client):
    text = minimal_file("\nsection,settings\nsetting,color,shape\nmisc,slate,ellipse\nimportant_edge,crimson,")
    loaded = load(client, text, dry_run=False).json()
    assert [p["code"] for p in loaded["report"]["problems"]] == ["indistinct_styles"]
    settings = client.get(f"/api/investigations/{loaded['investigation']['id']}/settings").json()
    assert settings["node_styles"]["misc"] == {"color": "rose", "shape": "diamond"}
    assert settings["important_edge_color"] == "crimson"


def test_file_without_settings_or_important_imports_with_defaults(client):
    text = minimal_file(
        "\nsection,transactions\nref,transaction_number,date,time,store_number\nT1,00482913,03-14-2026,18:05,042",
        PAY_SECTION + "T1,cash,,5.00",
    )
    loaded = load(client, text, dry_run=False).json()
    assert loaded["report"]["problems"] == [] and loaded["investigation"]["document_count"] == 1
    iid = loaded["investigation"]["id"]
    assert client.get(f"/api/investigations/{iid}/settings").json()["is_default"] is True
    assert client.get(f"/api/investigations/{iid}/documents").json()[0]["important"] is False


def test_missing_file_part_is_422(client):
    assert client.post("/api/investigations/import?dry_run=true").status_code == 422
