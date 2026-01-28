#!/bin/bash

# =========================================================
#  ANDROZOO NAME SEARCHER (APP NAME BASED)
# =========================================================

INPUT_FILE="names_list.txt"
DB_FILE="latest.csv"
OUTPUT_FILE="bulunan_askeri_uygulamalar.csv"

# 1. TÜRKÇE KARAKTER SORUNUNU ÇÖZ (UTF-8'e zorla)
# iconv ile dosyay? temizleyip geçici bir dosyaya aktar?yoruz
echo "Karakter kodlamasi duzeltiliyor..."
iconv -f WINDOWS-1254 -t UTF-8 "$INPUT_FILE" > input_utf8.csv 2>/dev/null || cp "$INPUT_FILE" input_utf8.csv

echo "--- Arama Baslatiliyor ---"
echo "Toplam $(wc -l < names_list.txt) uygulama ismi araniyor..."

# 3. BA?LIK OLU?TUR
head -n 1 "$DB_FILE" > "$OUTPUT_FILE"

# 4. ?S?M TABANLI ARAMA (BÜYÜK/KÜÇÜK HARF DUYARSIZ)
# latest.csv içinde uygulama isimleri genellikle 2. veya 6. sütunda olur. 
# H?z için her ismi tek tek grep ile ar?yoruz.
while read -r app_name; do
    if [[ -n "$app_name" ]]; then
        echo "Araniyor: $app_name"
        # -i: Case-insensitive (Büyük/küçük harf fark etmez)
        # -F: Fixed strings (?smi oldu?u gibi ara)
        grep -i -F "$app_name" "$DB_FILE" >> "$OUTPUT_FILE"
    fi
done < names_list.txt


echo "--- Islem Tamamlandi ---"
echo "Bulunan sonuclar: $OUTPUT_FILE"
