#!/usr/bin/env python3
import os
import json
import sys

# =========================
# ANDROGUARD IMPORT
# =========================
try:
    from androguard.core.apk import APK
except ImportError:
    print("[!] Androguard bulunamadı. Lütfen sanal ortamı aktif edin.")
    sys.exit(1)

# =========================
# AYARLAR
# =========================
APK_DIR = "/home/azureuser/dataset/apks"      # APK'ların olduğu yer
OUT_DIR = "/home/azureuser/dataset/output"    # Mevcut sonuçların olduğu yer

def update_json_with_levels(apk_path):
    apk_name = os.path.basename(apk_path).replace(".apk", "")
    json_path = os.path.join(OUT_DIR, apk_name, "summary.json")

    # 1. JSON dosyası var mı kontrol et
    if not os.path.exists(json_path):
        print(f"[-] JSON bulunamadı, atlanıyor: {apk_name}")
        return

    # 2. APK'nın sadece Manifest'ini oku (Çok hızlıdır)
    try:
        a = APK(apk_path)
        
        # Androguard'dan detaylı izin bilgilerini çek
        # Bu fonksiyon izinlerin 'danger' seviyesini döndürür
        perm_details = a.get_details_permissions_in_new_format()
        
        # Sadece bizim için önemli olan 'protectionLevel' bilgisini süz
        levels = {}
        for perm, details in perm_details.items():
            # Genellikle 'dangerous', 'normal', 'signature' döner
            levels[perm] = details.get("protectionLevel", "unknown")

    except Exception as e:
        print(f"[!] APK okuma hatası ({apk_name}): {e}")
        return

    # 3. Mevcut JSON'ı güncelle
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        # Metadata altına yeni alanı ekle
        if "metadata" in data:
            data["metadata"]["permission_details"] = levels
            # İstatistiksel kolaylık için sayıları da ekleyelim
            data["metadata"]["risk_counts"] = {
                "dangerous": sum(1 for v in levels.values() if "dangerous" in str(v).lower()),
                "normal": sum(1 for v in levels.values() if "normal" in str(v).lower())
            }

        # 4. Dosyayı üzerine yaz
        with open(json_path, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"[+] Güncellendi: {apk_name}")

    except Exception as e:
        print(f"[!] JSON yazma hatası ({apk_name}): {e}")

# =========================
# ANA DÖNGÜ
# =========================
if __name__ == "__main__":
    if not os.path.exists(APK_DIR):
        print("APK klasörü bulunamadı!")
        sys.exit(1)

    files = sorted([f for f in os.listdir(APK_DIR) if f.endswith(".apk")])
    print(f"[*] Toplam {len(files)} APK taranacak ve JSON'lar güncellenecek...")

    for f in files:
        update_json_with_levels(os.path.join(APK_DIR, f))
