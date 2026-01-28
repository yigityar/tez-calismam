# -*- coding: utf-8 -*-
import pandas as pd
import os
import sys
import re  # RegEx kutuphanesi eklendi (Kelime Avcisi)

# --- AYARLAR ---
MODEL_NAME = "mistral"
DB_KLASORU = "./chroma_db"
IZIN_DOSYASI = "Hedef_Izinler.csv"  # YENI KUCUK DOSYA
CIKTI_DOSYASI = "Kritik_Izin_Raporu.xlsx"

print(f"--- ANALIZ SISTEMI ({MODEL_NAME}) ---")

# --- KUTUPHANELER ---
try:
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
    from langchain_community.llms import Ollama
    print("Sistem hazir.")
except ImportError:
    sys.exit("Eksik kutuphane.")

# --- MODEL BAGLANTISI ---
embeddings = FastEmbedEmbeddings()
vector_store = Chroma(persist_directory=DB_KLASORU, embedding_function=embeddings)
llm = Ollama(model=MODEL_NAME, temperature=0.0)

# --- VERI OKUMA ---
df_izinler = pd.read_csv(IZIN_DOSYASI)
sonuclar = []

print(f"\nAnaliz edilecek izin sayisi: {len(df_izinler)}")
print("Mistral agir modeldir, her izin icin 30-60 saniye bekletebilir.\n")

# --- ANALIZ DONGUSU ---
for index, row in df_izinler.iterrows():
    izin_adi = row['Izin_Adi']
    aciklama = row['Aciklama']
    
    print(f"[{index+1}/3] {izin_adi} isleniyor... ", end="", flush=True)

    # 1. Doktrin (Hafiza)
    docs = vector_store.similarity_search(f"{izin_adi} risk", k=1)
    doktrin = docs[0].page_content if docs else "Doktrin yok."

    # 2. Emir (Prompt) - Format zorlamasi artirildi
    prompt = f"""
    GÖREV: Bu Android iznini askeri güvenlik açısından 3 safhada analiz et.
    İZİN: {izin_adi} ({aciklama})
    
    CEVAP FORMATI (Kesinlikle bu kelimeleri kullan):
    HAZIRLIK: [DUSUK / ORTA / YUKSEK / KRITIK] - Sebebi
    SIZMA: [DUSUK / ORTA / YUKSEK / KRITIK] - Sebebi
    HUCUM: [DUSUK / ORTA / YUKSEK / KRITIK] - Sebebi
    """
    
    try:
        cevap = llm.invoke(prompt)
        
        # 3. Akilli Ayiklama (RegEx) - "Belirsiz" hatasini bitiren kisim
        # Metnin icinde "HAZIRLIK: (kelime)" yapisini arar.
        
        def risk_bul(metin, anahtar_kelime):
            # Ornek: "HAZIRLIK: YUKSEK" -> YUKSEK kelimesini bulur
            kalip = fr"{anahtar_kelime}\s*[:\-]?\s*(\w+)"
            eslesme = re.search(kalip, metin, re.IGNORECASE)
            if eslesme:
                return eslesme.group(1).upper() # YUKSEK, KRITIK vb doner
            return "BELIRSIZ"

        r_hazirlik = risk_bul(cevap, "HAZIRLIK")
        r_sizma = risk_bul(cevap, "SIZMA")
        r_hucum = risk_bul(cevap, "HUCUM")
        
        # Cevabi komple kaydetmek yerine ozeti aliyoruz
        sonuclar.append({
            "Izin": izin_adi,
            "Hazirlik": r_hazirlik,
            "Sizma": r_sizma,
            "Hucum": r_hucum,
            "Tam Cevap": cevap[:300] # Kontrol icin cevabin basini da sakla
        })
        print(f"Bitti. (Risk: {r_sizma})")
        
    except Exception as e:
        print("HATA")
        sonuclar.append({"Izin": izin_adi, "Hazirlik": f"Hata: {e}"})

# --- KAYIT ---
pd.DataFrame(sonuclar).to_excel(CIKTI_DOSYASI, index=False)
print(f"\nRapor hazir: {CIKTI_DOSYASI}")
