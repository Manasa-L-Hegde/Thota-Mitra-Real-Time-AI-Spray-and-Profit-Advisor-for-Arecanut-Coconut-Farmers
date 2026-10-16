import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Thota Mitra" in data["app"]


def test_get_defaults():
    response = client.get("/api/defaults")
    assert response.status_code == 200
    data = response.json()
    assert "_meta" in data
    assert "plantation_defaults" in data
    assert "cost_presets" in data
    assert "mandi_prices_reference" in data
    assert len(data["mandi_prices_reference"]) >= 4
    assert all(p["user_editable"] is True and p["citation"] for p in data["mandi_prices_reference"])


def test_get_active_rules():
    response = client.get("/api/rules")
    assert response.status_code == 200
    rules = response.json()
    assert "_meta" in rules
    assert "validate against" in rules["_meta"]["status"].lower()
    assert "schedule_engine" in rules


def test_api_weather_endpoint():
    response = client.get("/api/weather?lat=13.6934&lon=75.2427")
    assert response.status_code == 200
    data = response.json()
    assert "hourly" in data
    assert "daily" in data
    assert len(data["daily"]) >= 7


def test_api_risk_endpoint():
    response = client.get("/api/risk?lat=13.6934&lon=75.2427&crop=arecanut")
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["total_risk_score"] <= 100
    assert data["conducive_conditions_index"] == data["total_risk_score"]
    assert data["methodology"] == "HEURISTIC_TO_BE_VALIDATED"
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert data["crop"] == "arecanut"
    assert len(data["factors"]) == 4


def test_api_spray_plan_endpoint():
    response = client.get("/api/spray-plan?lat=13.6934&lon=75.2427&crop=arecanut")
    assert response.status_code == 200
    data = response.json()
    assert "decisions" in data
    assert len(data["decisions"]) >= 5


def test_api_dashboard_endpoint():
    response = client.get("/api/dashboard?lat=13.6934&lon=75.2427&crop=arecanut")
    assert response.status_code == 200
    data = response.json()
    assert "location" in data
    assert "weather" in data
    assert "risk" in data
    assert "spray_plan" in data


def test_mandi_prices():
    response = client.get("/api/mandi/prices")
    assert response.status_code == 200
    prices = response.json()
    assert len(prices) >= 4
    kundapura = next((p for p in prices if "Kundapura" in p["market"]), None)
    assert kundapura is not None
    assert kundapura["modal_price_per_quintal"] == 44000.0


def test_economics_calculation():
    payload = {
        "acres": 1.0,
        "trees_per_acre": 575,
        "labour_wage_per_day": 650.0,
        "spray_rounds": 3,
        "spray_cost_per_round": 10350.0,
        "manure_fertilizer_cost": 35000.0,
        "harvest_labour_cost": 45000.0,
        "expected_yield_kg": 2730.0,
        "selling_price_per_qtl": 44000.0
    }
    response = client.post("/api/economics/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "financial_summary" in data
    assert data["financial_summary"]["is_profitable"] is True
    assert data["financial_summary"]["break_even_price_per_qtl"] > 0
    assert data["cost_breakdown"]["spraying_pct"] > 0
    assert len(data["plain_insights"]["en"]) > 0
    assert len(data["plain_insights"]["kn"]) > 0

    # Prove dynamic computation: change wage from 650 to 950 and acres to 3
    payload_modified = dict(payload, acres=3.0, labour_wage_per_day=950.0, selling_price_per_qtl=35000.0)
    response_mod = client.post("/api/economics/calculate", json=payload_modified)
    data_mod = response_mod.json()

    # Dynamic values must differ based on input math
    assert data_mod["financial_summary"]["total_cultivation_cost"] != data["financial_summary"]["total_cultivation_cost"]
    assert data_mod["plain_insights"]["en"] != data["plain_insights"]["en"]
    assert f"{data_mod['financial_summary']['break_even_price_per_qtl']:,.0f}" in data_mod["plain_insights"]["en"]


def test_economics_save_scenario():
    payload = {
        "acres": 2.0,
        "trees_per_acre": 575,
        "labour_wage_per_day": 700.0,
        "spray_rounds": 3,
        "spray_cost_per_round": 20700.0,
        "manure_fertilizer_cost": 70000.0,
        "harvest_labour_cost": 90000.0,
        "expected_yield_kg": 5460.0,
        "selling_price_per_qtl": 44000.0,
        "scenario_name": "Test 2-Acre Scenario"
    }
    response = client.post("/api/economics/save-scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "saved"
    assert "scenario_id" in data


def test_farm_diary_flow():
    # 1. Post a new diary entry
    entry_payload = {
        "entry_date": "2026-07-22",
        "event_type": "fruit_rot_seen",
        "severity": "Moderate",
        "affected_trees_count": 12,
        "notes": "Spotted water-soaked rot near stream boundary"
    }
    res_post = client.post("/api/diary", json=entry_payload)
    assert res_post.status_code == 200
    entry_data = res_post.json()
    assert entry_data["entry_date"] == "2026-07-22"

    # 2. Get diary entries
    res_get = client.get("/api/diary")
    assert res_get.status_code == 200
    entries = res_get.json()
    assert len(entries) >= 1
    found = any(e["entry_date"] == "2026-07-22" for e in entries)
    assert found is True

    # 3. Export CSV
    res_csv = client.get("/api/diary/export.csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "fruit_rot_seen" in res_csv.text
    assert res_csv.content.startswith(b"\xef\xbb\xbf")


def test_ask_mitra_rag_verified_query():
    # Query with answer in docs_corpus
    payload = {"question": "How to prepare 1% Bordeaux mixture for koleroga?"}
    res = client.post("/api/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["found_in_corpus"] is True
    assert len(data["sources"]) > 0
    assert "copper sulphate" in data["answer_en"].lower() or "bordeaux" in data["answer_en"].lower()


def test_ask_mitra_rag_refusal_for_unverified_query():
    # Query completely unrelated to plantation corpus
    payload = {"question": "How do I cultivate wheat in Punjab during winter season?"}
    res = client.post("/api/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["found_in_corpus"] is False
    assert data["refusal_reason"] == "NOT_FOUND_IN_CORPUS"
    assert "refuse" in data["answer_en"].lower()
    assert "verified cpcri/kau reference corpus" in data["answer_en"].lower()


def test_ask_mitra_system_and_alerts_queries():
    # Conversational & app-feature queries matching docs_corpus/thota_mitra_system_and_alerts_guide.md
    queries = [
        "will this give alert?",
        "how does spray window work?",
        "when should I spray?",
        "what is conducive index?",
        "ಈ ಆ್ಯಪ್ ಎಚ್ಚರಿಕೆ ನೀಡುತ್ತದೆಯೇ?"
    ]
    for q in queries:
        res = client.post("/api/ask", json={"question": q})
        assert res.status_code == 200
        data = res.json()
        assert data["found_in_corpus"] is True, f"Failed for query: {q}"
        assert len(data["sources"]) > 0
        assert "thota_mitra_system_and_alerts_guide.md" in data["sources"] or "kau_bordeaux_mixture_preparation.txt" in data["sources"] or "frontiers_monsoon_timing_reference.txt" in data["sources"]


def test_ask_mitra_unverified_chemicals_refusal():
    # Queries containing unverified chemicals or non-arecanut crops must strictly refuse
    refusal_queries = [
        "Can I use streptomycin antibiotic on tomato blight?",
        "Is glyphosate good for betel vine?",
        "How do I control fall armyworm on maize crop?"
    ]
    for q in refusal_queries:
        res = client.post("/api/ask", json={"question": q})
        assert res.status_code == 200
        data = res.json()
        assert data["found_in_corpus"] is False
        assert data["refusal_reason"] == "NOT_FOUND_IN_CORPUS"
        assert "refuse" in data["answer_en"].lower()


def test_geocode_search_offline_and_autocomplete():
    # Test typing 'yalavalli'
    res = client.get("/api/geocode/search?q=yalavalli")
    assert res.status_code == 200
    results = res.json()["results"]
    assert len(results) > 0
    yalavalli = next((r for r in results if r["name"].lower() == "yalavalli"), None)
    assert yalavalli is not None
    assert yalavalli["taluk"] == "Sirsi"
    assert yalavalli["district"] == "Uttara Kannada"
    assert "Yalavalli, Sirsi, Uttara Kannada" in yalavalli["display_label_en"]

    # Test typing 'hegde'
    res_hegde = client.get("/api/geocode/search?q=hegde")
    assert res_hegde.status_code == 200
    hegde_results = res_hegde.json()["results"]
    assert any(r["name"].lower() == "hegde" and r["taluk"] == "Kumta" for r in hegde_results)


def test_geocode_reverse_karnataka():
    # Reverse geocode Yalavalli coordinates
    res = client.get("/api/geocode/reverse?lat=14.6542&lon=74.8724")
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert "taluk" in data
    assert "district" in data
    assert data["lat"] == 14.6542
    assert data["lon"] == 74.8724

