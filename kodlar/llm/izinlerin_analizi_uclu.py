# -*- coding: utf-8 -*-
import pandas as pd
import sys
import re

# --- AYARLAR ---
MODEL_NAME = "mistral"
DB_KLASORU = "./chroma_db"
IZIN_DOSYASI = "Hedef_Izinler.csv" 
CIKTI_DOSYASI = "3_Kademeli_Risk_Raporu.xlsx"

print(f"--- 3 KADEMELİ RİSK ANALİZİ (MISTRAL) ---")

# --- KUTUPHANELER ---
try:
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
    from langchain_community.llms import Ollama
except ImportError:
    sys.exit("Eksik kutuphane.")

# --- BAĞLANTI ---
embeddings = FastEmbedEmbeddings()
vector_store = Chroma(persist_directory=DB_KLASORU, embedding_function=embeddings)
llm = Ollama(model=MODEL_NAME, temperature=0.0) 

# --- VERI OKUMA ---
df_izinler = pd.read_csv(IZIN_DOSYASI)
sonuclar = []

print(f"Analiz edilecek hedef: {len(df_izinler)}\n")

# --- 3 SEVIYELI AYIKLAYICI ---
def seviye_bul(metin, anahtar):
    # Regex sadece 3 kelimeyi arar: DUSUK, ORTA, YUKSEK
    kalip = fr"{anahtar}\s*[:\-]?\s*(DUSUK|ORTA|YUKSEK|DÜŞÜK|YÜKSEK)"
    eslesme = re.search(kalip, metin, re.IGNORECASE)
    
    if eslesme:
        bulunan = eslesme.group(1).upper()
        # Turkce karakterleri duzelt (Excel icin)
        bulunan = bulunan.replace("Ü", "U").replace("Ş", "S").replace("İ", "I")
        return bulunan
    return "BELIRSIZ"

# --- ANALIZ DONGUSU ---
for index, row in df_izinler.iterrows():
    izin_adi = row['Izin_Adi']
    aciklama = row['Aciklama']
    
    print(f"[{index+1}/{len(df_izinler)}] {izin_adi} ... ", end="", flush=True)

    # 1. Doktrin
    try:
        docs = vector_store.similarity_search(f"{izin_adi} risk", k=1)
        doktrin = docs[0].page_content
    except:
        doktrin = "Veri yok."

    # 2. EMIR (3 KADEME)
    prompt = f"""
    GÖREV: Bu Android iznini askeri güvenlik açısından 3 seviyede analiz et.
    İZİN: {izin_adi} ({aciklama})
    DOKTRİN İPUCU: {doktrin[:200]}
    
    KURALLAR:
    1. Sadece şu 3 seviyeden birini kullan: DUSUK, ORTA, YUKSEK.
    2. Asla açıklama yapma. Sadece şablonu doldur.
    
    CEVAP ŞABLONU:
    HAZIRLIK: [SEVİYE]
    SIZMA: [SEVİYE]
    HUCUM: [SEVİYE]
    """
    
    try:
        cevap = llm.invoke(prompt)
        
        # 3. Ayikla
        h = seviye_bul(cevap, "HAZIRLIK")
        s = seviye_bul(cevap, "SIZMA")
        m = seviye_bul(cevap, "HUCUM")
        
        sonuclar.append({
            "Izin Adi": izin_adi,
            "Hazirlik": h,
            "Sizma": s,
            "Hucum": m
        })
        print(f"Bitti -> {s}")
        
    except Exception as e:
        print("HATA")
        sonuclar.append({"Izin Adi": izin_adi, "Hazirlik": "HATA"})

# --- KAYIT ---
pd.DataFrame(sonuclar).to_excel(CIKTI_DOSYASI, index=False)
print(f"\nRAPOR HAZIR: {CIKTI_DOSYASI}")
