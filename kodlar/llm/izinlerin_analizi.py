# -*- coding: utf-8 -*-
import pandas as pd
import os
import sys
import time

# --- 1. AYARLAR VE SABITLER ---
MODEL_NAME = "mistral"  # Eger RAM yetmezse burayi "gemma:2b" yapin
DB_KLASORU = "./chroma_db"
IZIN_DOSYASI = "Resmi_Android_Izin_Sozlugu.csv"
CIKTI_DOSYASI = "Askeri_Izin_Risk_Raporu.xlsx"

print(f"--- ASKERI ANALIZ SISTEMI BASLATILIYOR ({MODEL_NAME}) ---")

# --- 2. KUTUPHANE KONTROLU ---
try:
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
    from langchain_community.llms import Ollama
    print("[1/4] Kutuphaneler ve Telsiz Baglantisi: OK")
except ImportError as e:
    print(f"KRITIK HATA: Eksik kutuphane -> {e}")
    sys.exit()

# --- 3. VERI VE HAFIZA KONTROLU ---
if not os.path.exists(IZIN_DOSYASI):
    print(f"HATA: '{IZIN_DOSYASI}' bulunamadi. Operasyon iptal.")
    sys.exit()
    
# CSV Okuma (Hata toleransli)
try:
    df_izinler = pd.read_csv(IZIN_DOSYASI, encoding='utf-8')
except:
    df_izinler = pd.read_csv(IZIN_DOSYASI, encoding='ISO-8859-1') # Yedek encoding

print(f"[2/4] Hedef Listesi Yuklendi. Toplam Hedef: {len(df_izinler)}")

# --- 4. MODEL VE VEKTOR BAGLANTISI ---
print(f"[3/4] Model ({MODEL_NAME}) ve Doktrin Hafizasi Yukleniyor... ", end="")
try:
    embeddings = FastEmbedEmbeddings()
    vector_store = Chroma(persist_directory=DB_KLASORU, embedding_function=embeddings)
    # temperature=0 -> Modelin yaraticiligini kapatir, robot gibi net cevap verir.
    llm = Ollama(model=MODEL_NAME, temperature=0.0) 
    print("OK")
except Exception as e:
    print(f"\nBAGLANTI HATASI: {e}")
    print("IPUCU: Terminalde 'ollama serve' acik mi?")
    sys.exit()

# --- YARDIMCI FONKSIYON: CEVAP AYIKLAYICI ---
def askeri_cevabi_ayikla(metin):
    """
    Modelden gelen metni parcalar ve 3 safhaya ayirir.
    Hata durumunda 'Belirsiz' doner.
    """
    h, s, m = "Belirsiz", "Belirsiz", "Belirsiz" # h=Hazirlik, s=Sizma, m=Hucum(Mudahale)
    
    satirlar = metin.split('\n')
    for satir in satirlar:
        satir_lower = satir.lower().strip()
        # Temizleme
        icerik = satir.split(":", 1)[-1].strip() if ":" in satir else satir
        
        if "hazirlik" in satir_lower:
            h = icerik
        elif "sizma" in satir_lower or "intikal" in satir_lower:
            s = icerik
        elif "hucum" in satir_lower or "temas" in satir_lower:
            m = icerik
            
    return h, s, m

# --- 5. OPERASYON DONGUSU ---
print(f"\n[4/4] ANALIZ BASLIYOR (Cikis icin CTRL+C basin)...\n")
sonuclar = []
baslangic_zamani = time.time()

for index, row in df_izinler.iterrows():
    try:
        # Veri cekme
        izin_adi = str(row.get('Izin_Adi', row.get('name', 'Bilinmiyor')))
        aciklama = str(row.get('Aciklama', row.get('description', 'Yok')))
        
        print(f"--> Analiz {index+1}/{len(df_izinler)}: {izin_adi} ... ", end="", flush=True)
        
        # A. Doktrin Sorgusu (RAG)
        context = ""
        try:
            arama = f"{izin_adi} {aciklama} risk"
            docs = vector_store.similarity_search(arama, k=2) # En alakali 2 dokumani getir
            context = "\n".join([d.page_content for d in docs])
        except:
            context = "Doktrin verisi bulunamadi."

        # B. Emir (Prompt)
        prompt = f"""
        SEN: TSK İstihbarat Subayısın.
        GÖREV: Aşağıdaki Android iznini 3 askeri safhada analiz et.
        
        ANALİZ EDİLECEK İZİN: {izin_adi}
        TEKNİK AÇIKLAMA: {aciklama}
        İLGİLİ ASKERİ TALİMNAME: {context}
        
        KURALLAR:
        1. Sadece aşağıdaki formatı doldur.
        2. Risk Seviyeleri: DÜŞÜK, ORTA, YÜKSEK, KRİTİK.
        3. Her safha için kısa askeri gerekçe yaz.
        
        CEVAP ŞABLONU:
        Hazırlık: [SEVİYE] - [Gerekçe]
        Sızma: [SEVİYE] - [Gerekçe]
        Hücum: [SEVİYE] - [Gerekçe]
        """
        
        # C. Atesleme (Invoke)
        cevap = llm.invoke(prompt)
        
        # D. Sonuc Isleme
        r_hazirlik, r_sizma, r_hucum = askeri_cevabi_ayikla(cevap)
        
        sonuclar.append({
            "Izin Adi": izin_adi,
            "Hazirlik (Planlama) Risk": r_hazirlik,
            "Sizma (Intikal) Risk": r_sizma,
            "Hucum (Temas) Risk": r_hucum,
            "Teknik Aciklama": aciklama,
            "Referans Doktrin": context[:150] + "..." # Excel sismesin diye kisalttim
        })
        print("TAMAM.")

    except KeyboardInterrupt:
        print("\n\nOperasyon kullanici tarafindan durduruldu.")
        break
    except Exception as e:
        print(f"HATA ({e})")
        sonuclar.append({"Izin Adi": izin_adi, "Hazirlik (Planlama) Risk": f"Sistem Hatasi: {e}"})
        # Hata durumunda bekleme yapma, devam et

# --- 6. RAPORLAMA ---
print("\n--- RAPOR OLUSTURULUYOR ---")
if sonuclar:
    df_sonuc = pd.DataFrame(sonuclar)
    
    # Excel Kayit
    try:
        df_sonuc.to_excel(CIKTI_DOSYASI, index=False, engine='openpyxl')
        print(f"✅ BASARILI: Rapor '{CIKTI_DOSYASI}' olarak kaydedildi.")
    except Exception as e:
        csv_adi = CIKTI_DOSYASI.replace(".xlsx", ".csv")
        df_sonuc.to_csv(csv_adi, index=False, sep=";", encoding="utf-8-sig")
        print(f"⚠️ EXCEL HATASI: Rapor '{csv_adi}' olarak CSV formatinda kaydedildi.")
else:
    print("❌ HIC SONUC ALINAMADI.")

gecen_sure = time.time() - baslangic_zamani
print(f"Toplam Sure: {gecen_sure:.2f} saniye.")
