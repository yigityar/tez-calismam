# -*- coding: utf-8 -*-
import sys
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.llms import Ollama

# --- AYARLAR ---
DB_KLASORU = "./chroma_db"
MODEL_NAME = "mistral"

# SADECE 3 İZİN (Test Kümesi)
TEST_IZINLERI = [
    "android.permission.ACCESS_FINE_LOCATION", # Konum
    "android.permission.FLASHLIGHT",           # Işık
    "android.permission.VIBRATE"               # Ses/Titreşim
]

# SADECE 3 SAFHA (Hiçbir kural yok, sadece isimler var)
SAFHALAR = ["PREPARATION (Hazırlık)", "INFILTRATION (Sızma)", "ENGAGEMENT (Hücum)"]

print(f"--- 3x3 OTONOM ANALİZ BAŞLIYOR ({MODEL_NAME}) ---")
print("Kural: Kodun içinde bilgi yok. Her şey veritabanından çekilecek.\n")

# 1. HAFIZAYA BAĞLAN
try:
    embeddings = FastEmbedEmbeddings()
    db = Chroma(persist_directory=DB_KLASORU, embedding_function=embeddings)
    llm = Ollama(model=MODEL_NAME, temperature=0.1) # Ciddi olması için 0.1
except Exception as e:
    sys.exit(f"HATA: Veritabanı yok. Önce 'ogret.py' çalıştırın. Detay: {e}")

# 2. DOKTRİNİ HAFIZADAN ÇEK (Sadece Safha İsimlerini kullanarak arıyoruz)
print("[1/2] Askeri Doktrin (Ranger Handbook vb.) Hafızadan Çağrılıyor...")
doktrin_bilgisi = {}
for safha in SAFHALAR:
    # Safha ismini veritabanına soruyoruz: "Bu safhada kurallar nedir?"
    docs = db.similarity_search(f"Rules and security discipline for {safha} phase", k=2)
    bulunan_bilgi = " ".join([d.page_content[:500] for d in docs]) # İlk 500 karakteri al
    doktrin_bilgisi[safha] = bulunan_bilgi
    print(f"   > '{safha}' için veritabanından {len(bulunan_bilgi)} karakter bilgi bulundu.")

print("\n[2/2] İzinler Analiz Ediliyor...\n")

# 3. ANALİZ DÖNGÜSÜ
for izin in TEST_IZINLERI:
    print(f"--- ANALİZ EDİLEN: {izin} ---")
    
    # A. İznin Teknik Detayını Hafızadan Çek (TXT dosyasından öğrenmişti)
    teknik_docs = db.similarity_search(f"Technical definition and hardware access of {izin}", k=1)
    teknik_bilgi = teknik_docs[0].page_content if teknik_docs else "No technical info found."
    
    # B. LLM'e Sor (Bilgileri birleştir)
    prompt = f"""
    ROLE: Senior Military Intelligence Officer.
    TASK: Assess risk for the following permission based ONLY on the provided context.

    1. TECHNICAL INTELLIGENCE (From Android Manual):
    {teknik_bilgi}

    2. MISSION PHASE DOCTRINE (From Ranger Handbook):
    - PHASE 1 ({SAFHALAR[0]}): {doktrin_bilgisi[SAFHALAR[0]]}
    - PHASE 2 ({SAFHALAR[1]}): {doktrin_bilgisi[SAFHALAR[1]]}
    - PHASE 3 ({SAFHALAR[2]}): {doktrin_bilgisi[SAFHALAR[2]]}

    INSTRUCTION:
    Evaluate the risk (LOW, MEDIUM, HIGH) for each phase.
    If Infiltration Phase requires silence/darkness and this permission violates it -> HIGH RISK.
    
    OUTPUT FORMAT:
    {SAFHALAR[0]}: [RISK LEVEL] - [Reasoning based on doctrine]
    {SAFHALAR[1]}: [RISK LEVEL] - [Reasoning based on doctrine]
    {SAFHALAR[2]}: [RISK LEVEL] - [Reasoning based on doctrine]
    """

    cevap = llm.invoke(prompt)
    print(cevap)
    print("-" * 50)
