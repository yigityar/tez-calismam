import pandas as pd
import requests
from tqdm import tqdm

# Step 1: Load CSV
permissions_df = pd.read_csv("Resmi_Android_Izin_Sozlugu.csv")

# Step 2: Pick 10 unused permissions
sample_perms = [
    "ACCESS_BACKGROUND_LOCATION",
    "ACCESS_BLOBS_ACROSS_USERS",
    "ACCESS_CHECKIN_PROPERTIES",
    "ACCESS_HIDDEN_PROFILES",
    "ACCESS_LAUNCHER_DATA",
    "ACCESS_NOTIFICATION_POLICY",
    "ACCOUNT_MANAGER",
    "ADD_VOICEMAIL",
    "APPLY_PICTURE_PROFILE",
    "BIND_APPWIDGET"
]

# Step 3: Ollama config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

SYSTEM_INSTRUCTIONS = """You are a doctrine-aware assessor trained on the U.S. Ranger Handbook and Android permissions.
Task: Given ONLY an Android permission name, classify risk for three phases:
- Planning
- Infiltration
- Actions on the Objective

Rules:
- Output strictly in the format below.
- Use LOW, MEDIUM, or HIGH for each phase.
- Provide a concise rationale (1–2 sentences) per phase.
- Do not add extra sections, disclaimers, or metadata.

Format:
Planning: <LEVEL> - <Rationale>
Infiltration: <LEVEL> - <Rationale>
Actions on the Objective: <LEVEL> - <Rationale>
"""

# Step 4: Query Ollama
def query_ollama(permission_name: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_INSTRUCTIONS}\n\nPermission: {permission_name}",
        "options": {
            "temperature": temperature,
            "num_ctx": 4096,
            "num_predict": max_tokens,
        },
        "stream": False
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        return f"ERROR: {e}"

# Step 5: Run sample permissions with progress bar
results = []
for perm in tqdm(sample_perms, desc="Testing 10 new permissions", unit="perm"):
    output = query_ollama(perm)
    results.append({"Permission": perm, "Analysis": output})

# Step 6: Print results directly
for r in results:
    print("\n---")
    print(f"Permission: {r['Permission']}")
    print(r["Analysis"])

# Step 7: Save results to CSV
results_df = pd.DataFrame(results)
results_df.to_csv("Permission_Risk_Assessment_10.csv", index=False)
print("\n✅ Results saved to Permission_Risk_Assessment_10.csv")
