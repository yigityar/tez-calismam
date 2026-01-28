import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Hedef Adres (Resmi Android Dokümantasyonu)
URL = "https://developer.android.com/reference/android/Manifest.permission"

print("--- Android Resmi İzin Sözlüğü Oluşturuluyor ---")
print(f"🌍 Bağlanılıyor: {URL}")

try:
    # Sayfayı çek
    response = requests.get(URL)
    response.raise_for_status() # Hata varsa durdur
    soup = BeautifulSoup(response.content, 'html.parser')
    
    permissions_list = []
    
    # Android Developer sayfasındaki "Constants" (Sabitler) bölümünü bul
    # Genellikle 'api-item' class'ına sahip div'ler içinde yer alır
    api_items = soup.find_all('div', {'data-version-added': True})

    print(f"📊 Toplam {len(api_items)} adet tanımlı nesne bulundu. İşleniyor...")

    for item in api_items:
        try:
            # 1. İzin Adını Bul (Örn: ACCESS_FINE_LOCATION)
            # Genellikle h3 veya pre etiketleri içindedir.
            header = item.find('h3', class_='api-name')
            if not header:
                continue
                
            perm_name = header.get_text(strip=True)
            
            # Sadece büyük harfli olanları (İzin sabitlerini) al, metodları atla
            if not perm_name.isupper() or "_" not in perm_name:
                continue

            # 2. Açıklamayı ve Detayları Bul
            description_div = item.find('div', class_='api-level')
            if description_div:
                # Genellikle açıklama bu div'den sonra gelen paragraflardadır
                # Ancak sayfada yapı bazen karışıktır, metni bütün olarak alalım
                full_text = item.get_text(" ", strip=True)
            else:
                full_text = item.get_text(" ", strip=True)

            # 3. Açıklamayı Temizle (Regex ile)
            # "public static final String" gibi kod kalıntılarını temizle
            clean_desc = full_text.replace(f"public static final String {perm_name}", "")
            clean_desc = clean_desc.replace(f"Constant Value: \"android.permission.{perm_name}\"", "")
            
            # Protection Level (Koruma Seviyesi) Askeri Analiz için KRİTİK
            protection_level = "Unknown"
            prot_match = re.search(r"Protection level:\s*(\w+)", clean_desc, re.IGNORECASE)
            if prot_match:
                protection_level = prot_match.group(1)

            # Açıklamanın sadece ilk birkaç cümlesini al (Çok uzun teknik detayları at)
            # "Added in API level" yazısından sonrasını alalım
            desc_split = re.split(r"Added in API level \d+", clean_desc)
            if len(desc_split) > 1:
                final_desc = desc_split[-1].strip()
            else:
                final_desc = clean_desc
            
            # Gereksiz boşlukları temizle
            final_desc = " ".join(final_desc.split())
            
            # 4. Listeye Ekle
            permissions_list.append({
                "Izin_Adi": perm_name,
                "Tam_Deger": f"android.permission.{perm_name}",
                "Koruma_Seviyesi": protection_level,
                "Aciklama": final_desc[:1500] # Excel hücresi taşmasın diye sınırla
            })

        except Exception as e:
            continue # Hata veren satırı atla

    # CSV'ye Kaydet
    if permissions_list:
        df = pd.DataFrame(permissions_list)
        
        # Sadece tehlikeli (Dangerous) veya önemli izinleri filtrelemek isterseniz:
        # df = df[df['Koruma_Seviyesi'] == 'dangerous'] 
        
        dosya_adi = "Resmi_Android_Izin_Sozlugu.csv"
        df.to_csv(dosya_adi, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ BAŞARILI! Toplam {len(df)} adet izin çekildi.")
        print(f"📁 Dosya oluşturuldu: {dosya_adi}")
        print("💡 İPUCU: Bu dosyayı RAG (Retrieval-Augmented Generation) için kaynak olarak kullanabilirsiniz.")
        
    else:
        print("❌ Veri çekilemedi. Site yapısı değişmiş olabilir.")

except Exception as e:
    print(f"Hata oluştu: {e}")
