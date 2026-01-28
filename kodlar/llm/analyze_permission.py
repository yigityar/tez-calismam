# -*- coding: utf-8 -*-
import pandas as pd
import sys
import re
import time

# --- CONFIGURATION ---
MODEL_NAME = "mistral"
DB_FOLDER = "./chroma_db"
INPUT_FILE = "Resmi_Android_Izin_Sozlugu.csv"
OUTPUT_FILE = "Military_Risk_Report_3Phase.xlsx"

print(f"--- MILITARY RISK ANALYSIS SYSTEM ({MODEL_NAME}) ---")

# --- LIBRARIES ---
try:
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
    from langchain_community.llms import Ollama
    print("[OK] Libraries loaded.")
except ImportError:
    sys.exit("[ERROR] Missing libraries.")

# --- CONNECTION ---
print("[...] Connecting to Doctrine Database...", end="")
try:
    embeddings = FastEmbedEmbeddings()
    vector_store = Chroma(persist_directory=DB_FOLDER, embedding_function=embeddings)
    llm = Ollama(model=MODEL_NAME, temperature=0.1)
    print(" Done.")
except Exception as e:
    sys.exit(f"\n[ERROR] Connection failed: {e}")

# --- DATA LOADING ---
try:
    df_permissions = pd.read_csv(INPUT_FILE)
    print(f"[OK] Targets Loaded: {len(df_permissions)}\n")
except FileNotFoundError:
    sys.exit(f"[ERROR] Input file '{INPUT_FILE}' not found.")

results = []
start_time = time.time()

# --- PARSING ENGINE ---
def extract_risk_and_reason(text, phase_key):
    """
    Parses "PHASE: LEVEL - Reason" format.
    """
    pattern = fr"{phase_key}\s*[:\-]?\s*(LOW|MEDIUM|HIGH|CRITICAL)\s*[:\-\.]?\s*(.*)"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        level = match.group(1).upper()
        reason = match.group(2).strip()
        if "CRIT" in level: level = "HIGH"
        return level, reason
        
    return "UNKNOWN", "Parsing Error"

# --- ANALYSIS LOOP ---
print("--- STARTING ANALYSIS ---\n")

for index, row in df_permissions.iterrows():
    perm_name = row.get('Izin_Adi', row.get('name', 'Unknown'))
    tech_desc = row.get('Aciklama', row.get('description', ''))
    
    print(f"[{index+1}/{len(df_permissions)}] {perm_name} ... ", end="", flush=True)

    # 1. Doctrine Check
    try:
        docs = vector_store.similarity_search(f"{perm_name} risk", k=1)
        doctrine_context = docs[0].page_content
    except:
        doctrine_context = "Standard OPSEC rules."

    # 2. PROMPT (Refined for 3 Phases)
    prompt = f"""
    ROLE: You are a Senior Military Intelligence Officer (S-2).
    TASK: Analyze the operational risk of this Android permission for 3 specific mission phases.
    
    PERMISSION: {perm_name}
    TECHNICAL_DESC: {tech_desc}
    DOCTRINE: {doctrine_context[:150]}
    
    PHASE DEFINITIONS (STRICTLY APPLY THESE CONDITIONS):
    
    1. PREPARATION (Hazirlik):
       - Context: Main base is safe from direct fire but WITHIN effective range of enemy artillery and air strikes.
       - Activity: Planning and Rehearsals.
       - Risk Focus: Secrecy of the plan and equipment. Any leak (Audio/Data) puts the base under artillery threat.
       
    2. INFILTRATION (Intikal/Sizma):
       - Context: Deep penetration (30-40 km) into enemy zone. Moving to target unseen.
       - Activity: Avoiding enemy surveillance, listening systems, rear-area patrols, and civilians.
       - Risk Focus: CRITICAL. Zero visual/audio/electronic signature allowed. Location data leak here is fatal.
       
    3. ENGAGEMENT (Hucum/Baskin):
       - Context: Raid-style assault in darkness (Close Combat), lasting 5-10 minutes.
       - Risk Focus: Loss of surprise element and failure to complete mission before Enemy Reinforcements (QRF) arrive.
    
    INSTRUCTIONS:
    - Determine Risk Level (LOW/MEDIUM/HIGH).
    - Provide a SHORT Military Rationale (Max 10 words).
    - IF permission leaks Location or Audio in Phase 2 -> MARK AS HIGH.
    
    OUTPUT FORMAT:
    PREPARATION: [LEVEL] - [Rationale]
    INFILTRATION: [LEVEL] - [Rationale]
    ENGAGEMENT: [LEVEL] - [Rationale]
    """
    
    try:
        response = llm.invoke(prompt)
        
        # 3. Parse 3 Phases
        l_prep, r_prep = extract_risk_and_reason(response, "PREPARATION")
        l_inf, r_inf = extract_risk_and_reason(response, "INFILTRATION")
        l_eng, r_eng = extract_risk_and_reason(response, "ENGAGEMENT")
        
        # Debug
        if "UNKNOWN" in [l_prep, l_inf, l_eng]:
            print(" [!] Format Warning ", end="")

        results.append({
            "Permission": perm_name,
            "Prep_Risk": l_prep, "Prep_Reason": r_prep,
            "Inf_Risk": l_inf,   "Inf_Reason": r_inf,
            "Eng_Risk": l_eng,   "Eng_Reason": r_eng
        })
        print("Done.")

    except Exception as e:
        print(f" ERROR: {e}")
        results.append({"Permission": perm_name, "Prep_Risk": "ERROR"})

# --- REPORTING ---
if results:
    df_results = pd.DataFrame(results)
    
    # Organize Columns
    cols = [
        "Permission", 
        "Prep_Risk", "Prep_Reason", 
        "Inf_Risk", "Inf_Reason", 
        "Eng_Risk", "Eng_Reason"
    ]
    # Filter columns that exist
    df_results = df_results[[c for c in cols if c in df_results.columns]]
    
    df_results.to_excel(OUTPUT_FILE, index=False)
    print(f"\n✅ REPORT SAVED: {OUTPUT_FILE}")
