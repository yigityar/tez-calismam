# -*- coding: utf-8 -*-
from google_play_scraper import app, search
import pandas as pd
import time
import socket

# --- 0. Internet Baglantisi Kontrolu ---
def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("? Internet baglantisi mevcut.")
        return True
    except OSError:
        pass
    print("? Internet baglantisi YOK.")
    return False

if not check_internet():
    exit()

# 1. GÜNCELLENM?? SIKI ASKER? ARAMA TER?MLER?
# Bu liste sivil uygulamalar? eler, do?rudan taktiksel araçlara odaklan?r.
search_queries = [
    "mgrs gps",                # Military Grid Reference System (Askeri Koordinat Sistemi)
    "ballistic calculator",    # Keskin ni?anc?/Topçu at?? hesaplay?c?lar?
    "sniper dope",             # At?? kart? ve balistik veriler
    "tccc guidelines",         # Tactical Combat Casualty Care (Taktik Muharebe Yaral? Bak?m?)
    "mil-dot rangefinder",     # Dürbün içi mesafe tahmini (Askeri standart)
    "call for fire",           # Topçu/Havan ate? iste?i simülasyonlar? veya araçlar?
    "nato map symbols",        # APP-6 askeri harita sembolojisi
    "cbrn defense",            # KBRN (Kimyasal Biyolojik Radyolojik Nükleer) savunma
    "us army survival fm",     # Do?rudan FM (Field Manual) referansl? hayatta kalma
    "tak civtak",              # Team Awareness Kit (Sivil/Askeri Durumsal Fark?ndal?k)
    "morse code encoder",      # Muhabere
    "satellite tracker"        # Uydu geçi? takibi (?stihbarat/Gözetleme)
]

data_list = []
processed_packages = set()

print("\n--- Guvenli Veri Toplama Basliyor (Askeri Odakli) ---\n")

for query in search_queries:
    print(f"ARANIYOR: '{query}'")
    
    try:
        # Arama yap
        search_results = search(
            query,
            lang='en',
            country='us'
        )
        
        print(f"   -> Bulunan ham sonuc: {len(search_results)}")
        
        # Sonuçlar? i?le (?lk 20 uygulama)
        for result in search_results[:20]: 
            package_name = result['appId']
            
            if package_name in processed_packages:
                continue
                
            try:
                # Detaylar? çek
                app_details = app(
                    package_name,
                    lang='en',
                    country='us'
                )
                
                # --- HATA KORUMALI IZIN CEKME KISMI ---
                perms = app_details.get('permissions') 
                perm_str = "Belirtilmemis"
                perm_count = 0
                
                if perms:
                    try:
                        perm_list_temp = [p.get('permission') for p in perms if isinstance(p, dict) and 'permission' in p]
                        perm_str = ", ".join(perm_list_temp)
                        perm_count = len(perm_list_temp)
                    except:
                        perm_str = "Izin verisi hatali formatta"

                # Veriyi paketle
                app_info = {
                    'Arama Terimi': query,
                    'Uygulama Adi': app_details.get('title', 'Adsiz'),
                    'Paket Ismi': package_name,
                    'Kategori': app_details.get('genre', 'Bilinmiyor'),
                    'Indirme': app_details.get('minInstalls', 0),
                    'Puan': app_details.get('score', 0),
                    'Izin Sayisi': perm_count,
                    'Izin Listesi': perm_str,
                    # EKSTRA: Aç?klamay? da alal?m, izinler bo? gelirse analiz için kullan?rs?n?z
                    'Aciklama': app_details.get('description', '')[:200] + "..." # ?lk 200 karakter
                }
                
                data_list.append(app_info)
                processed_packages.add(package_name)
                
                print(".", end="", flush=True)
                time.sleep(1) 
                
            except Exception as e:
                pass
        
        print("\n   -> Kategori tamamlandi.")
        
    except Exception as e:
        print(f"   -> Arama hatasi: {e}")

# 3. Kayit
print(f"\n\nToplam {len(data_list)} uygulama basariyla toplandi.")

if data_list:
    df = pd.DataFrame(data_list)
    file_name = "Military_Specialized_Apps.csv"
    
    df.to_csv(file_name, index=False, encoding='utf-8-sig', sep=',')
    print(f"? Dosya kaydedildi: {file_name}")
else:
    print("? Veri toplanamadi.")
