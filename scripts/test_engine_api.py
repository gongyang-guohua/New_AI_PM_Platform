import httpx
import json

base_url = "http://localhost:8000/api/v1/engine/cpm/calculate"
mc_url = "http://localhost:8000/api/v1/engine/cpm/monte-carlo"

payload = {
  "activities": [
    {
      "id": "A",
      "duration": 10,
      "optimistic_duration": 8,
      "most_likely_duration": 10,
      "pessimistic_duration": 15
    },
    {
      "id": "B",
      "duration": 20,
      "constraint_type": "FNLT",
      "constraint_date": 25,
      "optimistic_duration": 15,
      "most_likely_duration": 20,
      "pessimistic_duration": 35
    }
  ],
  "relationships": [
    {
      "predecessor": "A",
      "successor": "B",
      "relation_type": "FS",
      "lag": 0
    }
  ],
  "with_ai_insights": False 
}

def test_api():
    print("Testing CPM Calculator API...")
    try:
        response = httpx.post(base_url, json=payload, timeout=30.0)
        print("Status code:", response.status_code)
        resp_json = response.json()
        print(json.dumps(resp_json, indent=2))
        
        # Verify deterministic negative float logic
        b_act = next(act for act in resp_json["activities"] if act["id"] == "B")
        if b_act["total_float"] < 0:
            print("[OK] Negative float correctly calculated due to FNLT constraint.")
    except Exception as e:
        print("API test failed:", e)

    print("\n----------------\nTesting Monte Carlo API...")
    try:
        response_mc = httpx.post(mc_url, json=payload, timeout=30.0)
        print("Status code:", response_mc.status_code)
        resp_mc_json = response_mc.json()
        del resp_mc_json["criticality_index"] # Omit heavy dict for printing succinctness
        print(json.dumps(resp_mc_json, indent=2))
    except Exception as e:
        print("MC API test failed:", e)

if __name__ == "__main__":
    test_api()
