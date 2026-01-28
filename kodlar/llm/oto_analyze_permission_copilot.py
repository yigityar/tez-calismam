import pandas as pd
import requests
from tqdm import tqdm

# Step 1: Load CSV
permissions_df = pd.read_csv("Resmi_Android_Izin_Sozlugu.csv")

# Step 2: Pick 4 permissions with varied risk levels (no fine location)
sample_perms = [
    "ACCEPT_HANDOVER",       # mixed risks
    "ACCESS_NETWORK_STATE",  # low risk
    "BODY_SENSORS",          # high risk
    "BLUETOOTH_CONNECT"      # medium risk
]

# Step 3: Ollama config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"  # change if your fine-tuned model has a different name

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
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        return f"ERROR: {e}"

# Step 5: Run sample permissions with progress bar
results = []
for perm in tqdm(sample_perms, desc="Testing varied risk permissions", unit="perm"):
    output = query_ollama(perm)
    results.append({"Permission": perm, "Analysis": output})

# Step 6: Show results
for r in results:
    print("\n---")
    print(f"Permission: {r['Permission']}")
    print(r["Analysis"])
