#!/usr/bin/env python3
import os
import json
import pandas as pd
import glob

# ========================================================
# ⚙️ AYARLAR
# ========================================================
ROOTS = [
        "/home/yigit/tez-calismam/Veriseti/3_davranisli_sonuclar" 
    ]

# Referans CSV dosyasının yolu
REF_CSV_PATH = "/home/yigit/tez-calismam/Veriseti/4_1_etiketli_tam_liste.csv"

OUTPUT_CSV = "Master_Thesis_Dataset_Full.csv"

# CSV'den alınacak öncelikli sütunlar (Sırası korunacak)
PRIORITY_COLUMNS = [
    "SHA256", "SIZE", "MARKET", "api_DEVICEID", "api_EXEC", 
    "api_CIPHER", "api_SMSMANAGER", "api_DYN_LOAD", "int_BOOT", "LABEL"
]

def load_reference_data(csv_path):
    """CSV verisini SHA256 indeksli bir sözlüğe yükler."""
    if not os.path.exists(csv_path):
        print(f"[!] HATA: Referans CSV bulunamadı: {csv_path}")
        return {}
    
    print(f"[*] Referans CSV yükleniyor...")
    try:
        df = pd.read_csv(csv_path)
        # Sütun isimlerini temizle (boşluk vs)
        df.columns = [c.strip() for c in df.columns]
        
        # SHA256'yı string yap ve küçük harfe çevir (eşleşme garantisi için)
        if 'SHA256' in df.columns:
            df['SHA256'] = df['SHA256'].astype(str).str.strip().str.lower()
            return df.set_index('SHA256').to_dict(orient='index')
        else:
            print("[!] CSV'de SHA256 sütunu bulunamadı!")
            return {}
    except Exception as e:
        print(f"[!] CSV Okuma Hatası: {e}")
        return {}

def flatten_json(y):
    """İç içe JSON yapısını (nested dict) düzleştirir."""
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            # Listeleri string olarak birleştir (örn: izinler)
            out[name[:-1]] = "|".join([str(i) for i in x])
            # Ayrıca listenin eleman sayısını da ekle
            out[name[:-1] + "_count"] = len(x)
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

def create_dataset():
    print("[*] Veri seti oluşturma başlıyor (Tüm Özellikler)...")
    
    # 1. Referans CSV verisini yükle
    ref_data = load_reference_data(REF_CSV_PATH)
    
    dataset = []
    total_files = 0
    
    for root_dir in ROOTS:
        if not os.path.exists(root_dir):
            continue
            
        print(f"[*] Taranıyor: {root_dir}")
        
        for folder_path, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename == "summary.json":
                    json_path = os.path.join(folder_path, filename)
                    total_files += 1
                    
                    try:
                        with open(json_path, 'r') as f:
                            json_data = json.load(f)
                        
                        sha256 = json_data.get("sha256", "").strip().lower()
                        
                        # --- 1. ADIM: CSV Verilerini Al (Varsa) ---
                        # CSV'de bu SHA256 var mı?
                        csv_row_data = ref_data.get(sha256, {})
                        
                        # Satırı başlat
                        row = {}
                        
                        # Öncelikli sütunları doldur (CSV'den veya boş)
                        for col in PRIORITY_COLUMNS:
                            if col == "SHA256":
                                row[col] = sha256
                            else:
                                row[col] = csv_row_data.get(col, None) # Bulamazsa None koyar

                        # --- 2. ADIM: JSON'daki HER ŞEYİ Düzleştir ve Ekle ---
                        flat_json = flatten_json(json_data)
                        
                        # JSON verilerini satıra ekle (Çakışma varsa JSON verisi CSV'yi ezmesin diye kontrol edilebilir, 
                        # ama burada append ediyoruz, sütun adları farklı olduğu sürece sorun yok)
                        for k, v in flat_json.items():
                            # Eğer sütun adı zaten öncelikli listede varsa (örn: sha256), dokunma
                            if k.upper() not in PRIORITY_COLUMNS: 
                                row[k] = v
                                
                        dataset.append(row)
                        
                    except Exception as e:
                        # print(f"Hata: {e}")
                        pass

    # DataFrame oluştur
    if dataset:
        df = pd.DataFrame(dataset)
        
        # --- 3. ADIM: Sütun Sıralamasını Garantiye Al ---
        # Mevcut sütunların listesi
        all_cols = df.columns.tolist()
        
        # Öncelikli olanları listeden çıkar (çünkü en başa manuel ekleyeceğiz)
        remaining_cols = [c for c in all_cols if c not in PRIORITY_COLUMNS]
        
        # Nihai sıralama: [Öncelikliler] + [Kalan JSON verileri]
        final_order = PRIORITY_COLUMNS + remaining_cols
        
        # Sütun eksikse (örn: CSV'de var ama hiç veri gelmediyse) hata vermemesi için reindex
        # (Sadece mevcut olanları sıralar, olmayanları NaN yapar)
        df = df.reindex(columns=final_order)
        
        # Kaydet
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n[✓] İŞLEM TAMAM: {OUTPUT_CSV}")
        print(f"    Toplam İşlenen: {len(df)}")
        print(f"    Toplam Sütun Sayısı: {len(df.columns)}")
        print(f"    İlk 10 Sütun: {df.columns[:10].tolist()}")
        
    else:
        print("[!] Veri bulunamadı.")

if __name__ == "__main__":
    create_dataset()
