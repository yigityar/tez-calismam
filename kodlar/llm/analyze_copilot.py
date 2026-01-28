# -*- coding: utf-8 -*-
"""
Military Risk Analysis for Android Permissions

This script evaluates operational risk across three mission phases (Preparation, Infiltration, Engagement)
for Android permissions using a vector database (doctrine context) and a language model.

Academic design principles:
- Reproducibility: deterministic LLM settings, explicit schema, documented pipeline.
- Unbiased processing: criteria-based evaluation, no role priming, constrained rationale.
- Transparency: provenance fields, methodology notes, and parsing diagnostics.
- Robustness: modular functions, consistent error handling, validation, and logging.

Author: (Your Name)
Date: (YYYY-MM-DD)
"""

import os
import re
import sys
import time
import json
import logging
from typing import Dict, Tuple, Any, Optional, List

import pandas as pd

# --- CONFIGURATION ---
MODEL_NAME = "mistral"
DB_FOLDER = "./chroma_db"
INPUT_FILE = "Hedef_Izinler.csv"
OUTPUT_FILE = "Military_Risk_Report_Final.xlsx"

LLM_TEMPERATURE = 0.0  # deterministic behavior
TOP_K_DOCS = 1         # minimal context to reduce noise
MAX_DOCTRINE_CHARS = 500
MAX_RATIONALE_WORDS = 12

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("risk-analysis")

logger.info(f"--- MILITARY RISK ANALYSIS SYSTEM ({MODEL_NAME}) ---")

# --- LIBRARIES ---
try:
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
    from langchain_community.llms import Ollama
except ImportError:
    sys.exit("[ERROR] Required libraries are missing. Please install dependencies.")

# --- CONNECTION ---
def init_services(db_folder: str, model_name: str, temperature: float):
    """
    Initialize embeddings, vector store, and LLM.
    """
    logger.info("Connecting to doctrine database and LLM...")
    embeddings = FastEmbedEmbeddings()
    vector_store = Chroma(persist_directory=db_folder, embedding_function=embeddings)
    llm = Ollama(model=model_name, temperature=temperature)
    logger.info("Services initialized.")
    return vector_store, llm

# --- DATA LOADING ---
def load_permissions_csv(path: str) -> pd.DataFrame:
    """
    Load CSV with fallback encodings.
    """
    if not os.path.exists(path):
        sys.exit(f"[ERROR] Input file '{path}' not found. Please check file name.")
    try:
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="ISO-8859-1")
        logger.info(f"Targets loaded: {len(df)}")
        return df
    except Exception as e:
        sys.exit(f"[ERROR] Could not read CSV: {e}")

# --- DOCTRINE RETRIEVAL ---
def get_doctrine_context(vector_store: Any, query: str, k: int = TOP_K_DOCS, max_chars: int = MAX_DOCTRINE_CHARS) -> str:
    """
    Retrieve doctrine context via similarity search with truncation.
    """
    try:
        docs = vector_store.similarity_search(query, k=k)
        if not docs:
            return "Standard OPSEC rules apply."
        content = docs[0].page_content or ""
        return content[:max_chars]
    except Exception:
        return "Standard OPSEC rules apply."

# --- PROMPT & PARSING ---
def build_prompt(permission: str, tech_desc: str, doctrine: str, max_words: int = MAX_RATIONALE_WORDS) -> str:
    """
    Construct a bias-aware, criteria-driven prompt with explicit JSON schema.
    """
    return f"""
You are to evaluate operational risk for an Android permission across three mission phases.
Use only the criteria below. Do not assume intent, capability, or context beyond what is provided.
Return a strict JSON object matching the schema. Do not include extra text.

PERMISSION: {permission}
TECHNICAL_DESC: {tech_desc}
DOCTRINE_CONTEXT: {doctrine}

PHASE DEFINITIONS:
1. PREPARATION (Hazirlik):
   - Situation: Unit at Main Base; vulnerable to long-range strikes.
   - Critical: Troop numbers, future plans, equipment lists.
   - Logic: Does this permission reveal identity or planning?

2. INFILTRATION (Intikal/Sizma):
   - Situation: Deep behind enemy lines; total stealth required.
   - Critical: Real-time location, electronic emissions (Radio/Bluetooth/Wi-Fi).
   - Logic: Does this permission create a detectable footprint or signal?

3. ENGAGEMENT (Hucum/Baskin):
   - Situation: Active firefight; comms and targeting are critical.
   - Critical: Tactical communication, real-time targeting updates.
   - Logic: Does this permission interfere with comms or aid enemy targeting?

RISK LEVELS: "LOW", "MEDIUM", "HIGH".
RATIONALE: concise, evidence-based, <= {max_words} words, no speculation.

SCHEMA (JSON):
{{
  "preparation": {{"level": "LOW|MEDIUM|HIGH", "rationale": "string"}},
  "infiltration": {{"level": "LOW|MEDIUM|HIGH", "rationale": "string"}},
  "engagement": {{"level": "LOW|MEDIUM|HIGH", "rationale": "string"}}
}}
""".strip()

VALID_LEVELS = {"LOW", "MEDIUM", "HIGH"}

def parse_llm_json(text: str) -> Optional[Dict[str, Dict[str, str]]]:
    """
    Parse and validate the LLM JSON response.
    Returns None if parsing fails.
    """
    try:
        data = json.loads(text)
        # Basic schema validation
        for phase in ["preparation", "infiltration", "engagement"]:
            if phase not in data or not isinstance(data[phase], dict):
                return None
            level = str(data[phase].get("level", "")).upper()
            rationale = str(data[phase].get("rationale", "")).strip()
            if level not in VALID_LEVELS or not rationale:
                return None
        return data
    except Exception:
        return None

def fallback_parse(text: str) -> Dict[str, Dict[str, str]]:
    """
    Fallback regex parsing for formats like:
    PHASE: LEVEL - Rationale
    """
    def extract(phase_key: str) -> Tuple[str, str]:
        pattern = rf"{phase_key}\s*[:\-]?\s*(LOW|MEDIUM|HIGH)\s*[:\-\.]?\s*(.*)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            level = match.group(1).upper()
            rationale = match.group(2).strip()
            return level, rationale
        return "MEDIUM", "Insufficient structured output; defaulted."

    prep_level, prep_rat = extract("PREPARATION")
    inf_level, inf_rat = extract("INFILTRATION")
    eng_level, eng_rat = extract("ENGAGEMENT")

    return {
        "preparation": {"level": prep_level, "rationale": prep_rat},
        "infiltration": {"level": inf_level, "rationale": inf_rat},
        "engagement": {"level": eng_level, "rationale": eng_rat},
    }

def enforce_rationale_length(text: str, max_words: int = MAX_RATIONALE_WORDS) -> str:
    """
    Truncate rationale to max_words without altering meaning excessively.
    """
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])

# --- ANALYSIS ---
def analyze_permission(
    llm: Any,
    vector_store: Any,
    perm_name: str,
    tech_desc: str
) -> Dict[str, Any]:
    """
    Analyze a single permission and return structured results with provenance.
    """
    doctrine_context = get_doctrine_context(
        vector_store,
        query=f"{perm_name} risk",
        k=TOP_K_DOCS,
        max_chars=MAX_DOCTRINE_CHARS
    )

    prompt = build_prompt(perm_name, tech_desc, doctrine_context)

    try:
        response = llm.invoke(prompt)
        parsed = parse_llm_json(response)
        if parsed is None:
            logger.warning("Structured JSON parsing failed; using fallback parser.")
            parsed = fallback_parse(response)
            parse_status = "fallback"
        else:
            parse_status = "json"
    except Exception as e:
        logger.error(f"LLM invocation error: {e}")
        parsed = {
            "preparation": {"level": "MEDIUM", "rationale": "LLM error; defaulted."},
            "infiltration": {"level": "MEDIUM", "rationale": "LLM error; defaulted."},
            "engagement": {"level": "MEDIUM", "rationale": "LLM error; defaulted."},
        }
        parse_status = "error"

    # Enforce rationale length
    for phase in parsed:
        parsed[phase]["rationale"] = enforce_rationale_length(parsed[phase]["rationale"])

    return {
        "Permission": perm_name,
        "Tech_Desc": tech_desc,
        "Prep_Risk": parsed["preparation"]["level"],
        "Prep_Reason": parsed["preparation"]["rationale"],
        "Inf_Risk": parsed["infiltration"]["level"],
        "Inf_Reason": parsed["infiltration"]["rationale"],
        "Eng_Risk": parsed["engagement"]["level"],
        "Eng_Reason": parsed["engagement"]["rationale"],
        # Provenance & diagnostics
        "Doctrine_Snippet": doctrine_context,
        "Parse_Status": parse_status,
        "Model_Name": MODEL_NAME,
        "LLM_Temperature": LLM_TEMPERATURE,
    }

# --- REPORTING ---
def save_report(df: pd.DataFrame, output_path: str, metadata: Dict[str, Any]) -> None:
    """
    Save results to Excel with an additional sheet for metadata.
    Falls back to CSV if Excel write fails.
    """
    try:
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Results", index=False)
            meta_df = pd.DataFrame([metadata])
            meta_df.to_excel(writer, sheet_name="Methodology", index=False)
        logger.info(f"Report saved: {output_path}")
    except Exception:
        csv_file = output_path.replace(".xlsx", ".csv")
        df.to_csv(csv_file, index=False)
        logger.warning(f"Excel write failed. Saved as CSV: {csv_file}")

def build_metadata(start_time: float, total_items: int) -> Dict[str, Any]:
    """
    Construct methodology and provenance metadata for academic reporting.
    """
    return {
        "Pipeline_Version": "1.0",
        "Model_Name": MODEL_NAME,
        "LLM_Temperature": LLM_TEMPERATURE,
        "Vector_DB_Folder": DB_FOLDER,
        "Input_File": INPUT_FILE,
        "Output_File": OUTPUT_FILE,
        "Total_Items": total_items,
        "Total_Time_Min": round((time.time() - start_time) / 60, 2),
        "Methodology_Notes": (
            "Risk levels derived from explicit phase criteria. "
            "LLM constrained to JSON schema; rationales truncated to limit verbosity. "
            "Doctrine context retrieved via similarity search and truncated to reduce noise. "
            "Parsing includes validation and fallback to regex. "
            "This is a decision-support tool; results require human review."
        ),
        "Bias_Mitigation": (
            "No role priming; criteria-based evaluation; deterministic settings; "
            "short, evidence-based rationales; explicit schema; provenance recorded."
        ),
        "Limitations": (
            "LLM outputs may vary across versions; doctrine retrieval may omit relevant context; "
            "technical descriptions may be incomplete; operational risk is situational."
        ),
    }

# --- MAIN ---
def main():
    vector_store, llm = init_services(DB_FOLDER, MODEL_NAME, LLM_TEMPERATURE)
    df_permissions = load_permissions_csv(INPUT_FILE)

    start_time = time.time()
    logger.info("Starting analysis...")

    results: List[Dict[str, Any]] = []
    total = len(df_permissions)

    for idx, row in df_permissions.iterrows():
        perm_name = str(row.get("Izin_Adi", row.get("name", row.get("Permission", "Unknown"))))
        tech_desc = str(row.get("Aciklama", row.get("description", row.get("Description", ""))))
        logger.info(f"[{idx + 1}/{total}] Analyzing: {perm_name}")

        try:
            result = analyze_permission(llm, vector_store, perm_name, tech_desc)
            results.append(result)
        except Exception as e:
            logger.error(f"Analysis error for '{perm_name}': {e}")
            results.append({
                "Permission": perm_name,
                "Tech_Desc": tech_desc,
                "Prep_Risk": "MEDIUM",
                "Prep_Reason": "Unhandled error; defaulted.",
                "Inf_Risk": "MEDIUM",
                "Inf_Reason": "Unhandled error; defaulted.",
                "Eng_Risk": "MEDIUM",
                "Eng_Reason": "Unhandled error; defaulted.",
                "Doctrine_Snippet": "",
                "Parse_Status": "error",
                "Model_Name": MODEL_NAME,
                "LLM_Temperature": LLM_TEMPERATURE,
            })

    if results:
        df_results = pd.DataFrame(results)
        metadata = build_metadata(start_time, total_items=len(results))
        save_report(df_results, OUTPUT_FILE, metadata)
        logger.info(f"Total operation time: {metadata['Total_Time_Min']} minutes.")
    else:
        logger.warning("No results produced.")

if __name__ == "__main__":
    main()
