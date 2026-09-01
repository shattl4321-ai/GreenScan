"""Юнит-тесты RuleEngine / KnowledgeBase без внешних API и анализа фото."""

from engine import RuleEngine
from knowledge import KnowledgeBase


def _ids(recommendations):
    return {r["id"] for r in recommendations}


def _rec(recommendations, action_id):
    for r in recommendations:
        if r["id"] == action_id:
            return r
    return None


def test_weeds_without_mowing():
    """needs_mowing=false + weed_presence → сорняки есть, mow_lawn нет."""
    engine = RuleEngine()
    state = {
        "needs_mowing": False,
        "weed_presence": True,
        "weed_density": "low",
        "weed_type": "broadleaf",
    }
    actions = engine.evaluate(state)
    recs = engine.enrich(actions, state)

    assert "mow_lawn" not in actions
    assert "mow_lawn" not in _ids(recs)
    assert "spot_weed_control" in actions
    weed_rec = _rec(recs, "spot_weed_control")
    assert weed_rec is not None
    assert weed_rec.get("knowledge_items")


def test_mowing_when_needed():
    """needs_mowing=true → mow_lawn присутствует."""
    engine = RuleEngine()
    state = {"needs_mowing": True}
    actions = engine.evaluate(state)
    recs = engine.enrich(actions, state)

    assert "mow_lawn" in actions
    assert "mow_lawn" in _ids(recs)


def test_overseed_with_seeds():
    """bare_spots → overseed + травосмеси в knowledge_items."""
    engine = RuleEngine()
    state = {"bare_spots": True}
    actions = engine.evaluate(state)
    recs = engine.enrich(actions, state)

    assert "overseed" in actions
    overseed = _rec(recs, "overseed")
    assert overseed is not None
    items = overseed.get("knowledge_items") or []
    assert len(items) >= 1
    assert any(
        "repair" in (i.get("purpose") or []) or i.get("id") == "mix_repair"
        for i in items
    ) or any(i.get("type") in ("mix", "grass") for i in items)


def test_fertilizer_enrichment():
    """pale_grass + spring → apply_fertilizer с удобрениями из fertilizers.json."""
    engine = RuleEngine()
    state = {"pale_grass": True, "spring": True}
    actions = engine.evaluate(state)
    recs = engine.enrich(actions, state)

    assert "apply_fertilizer" in actions
    fert = _rec(recs, "apply_fertilizer")
    assert fert is not None
    items = fert.get("knowledge_items") or []
    assert len(items) >= 1
    assert any("pale_grass" in (i.get("applicable_conditions") or []) for i in items)


def test_herbicides_low_density_no_type():
    """low + без weed_type → commercial_product + точечная категория, без non_selective."""
    kb = KnowledgeBase()
    state = {"weed_presence": True, "weed_density": "low"}
    items = kb.get_herbicides(state)
    ids = [i.get("id") for i in items]

    assert any(i.get("product_type") == "commercial_product" for i in items)
    assert "herb_spot_treatment" in ids or any(
        i.get("product_type") != "commercial_product" for i in items
    )
    assert "herb_non_selective" not in ids
    assert "herb_prod_agrokiller" not in ids
    assert all(i.get("category") != "non_selective" for i in items)


def test_herbicides_low_density_broadleaf():
    """low + broadleaf → минимум 2 commercial_product, категория не занимает все места."""
    kb = KnowledgeBase()
    state = {
        "weed_presence": True,
        "weed_density": "low",
        "weed_type": "broadleaf",
    }
    items = kb.get_herbicides(state)
    products = [i for i in items if i.get("product_type") == "commercial_product"]
    types = [i for i in items if i.get("product_type") != "commercial_product"]
    ids = [i.get("id") for i in items]
    names = " ".join(i.get("name", "") for i in products)

    assert len(products) >= 2
    assert len(types) <= 1
    assert len(items) <= 3
    assert any(
        x in names
        for x in ("Лонтрел", "Линтур", "Хакер", "Деймос", "Газонтрел", "Лорнет", "Прополол")
    )
    assert "herb_prod_agrokiller" not in ids


def test_herbicides_grass_no_broadleaf_products():
    """weed_type=grass → без broadleaf commercial_product."""
    kb = KnowledgeBase()
    state = {
        "weed_presence": True,
        "weed_density": "medium",
        "weed_type": "grass",
    }
    items = kb.get_herbicides(state)
    products = [i for i in items if i.get("product_type") == "commercial_product"]

    assert all("broadleaf" not in (p.get("target_weeds") or []) for p in products)
    assert all(
        p.get("parent_type_id")
        not in (
            "herb_selective_broadleaf",
            "herb_selective_combined",
        )
        for p in products
    )
    assert any(
        i.get("id") == "herb_grass_specific"
        or "grass_weeds" in (i.get("target_weeds") or [])
        for i in items
    ) or len(products) == 0


if __name__ == "__main__":
    tests = [
        test_weeds_without_mowing,
        test_mowing_when_needed,
        test_overseed_with_seeds,
        test_fertilizer_enrichment,
        test_herbicides_low_density_no_type,
        test_herbicides_low_density_broadleaf,
        test_herbicides_grass_no_broadleaf_products,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            print(f"OK  {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {test.__name__}: {e}")
        except Exception as e:
            print(f"ERROR {test.__name__}: {e}")

    print(f"\n{passed}/{len(tests)} passed")
    raise SystemExit(0 if passed == len(tests) else 1)
