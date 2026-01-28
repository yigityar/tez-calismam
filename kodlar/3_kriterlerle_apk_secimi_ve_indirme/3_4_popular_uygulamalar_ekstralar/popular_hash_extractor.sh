#!/bin/bash

# =========================================================
#  POPULAR APPS HASH EXTRACTOR (Robust Version)
# =========================================================

INPUT_CSV="latest.csv"
VIP_LIST="vip_list.txt"
OUTPUT_CSV="populer_apps.csv"

# Create header
head -n 1 "$INPUT_CSV" > "$OUTPUT_CSV"

echo "------------------------------------------------"
echo "Starting extraction of popular app hashes..."
echo "------------------------------------------------"

# Clean vip_list.txt from Windows line endings (CRLF to LF)
sed -i 's/\r//' "$VIP_LIST"

total_apps=$(wc -l < "$VIP_LIST")
current=0

while read -r pkg; do
    [[ -z "$pkg" ]] && continue
    ((current++))
    
    # Remove any quotes or spaces from the input package name
    pkg_clean=$(echo "$pkg" | tr -d '"' | tr -d ' ' | tr -d '\r')
    
    echo -n "[$current/$total_apps] Searching for: $pkg_clean ... "

    # IMPROVED SEARCH:
    # We look for the package name surrounded by quotes or commas
    # Example: ,"com.whatsapp", or ,com.whatsapp,
    match=$(grep -E ",\"$pkg_clean\",|,$pkg_clean," "$INPUT_CSV" | awk -F, '$8 == 0' | sort -t, -k4 -r | head -n 1)

    if [[ -n "$match" ]]; then
        echo "$match" >> "$OUTPUT_CSV"
        echo "FOUND [OK]"
    else
        # Last resort: try a simple grep if the exact match fails
        match=$(grep ",$pkg_clean," "$INPUT_CSV" | awk -F, '$8 == 0' | sort -t, -k4 -r | head -n 1)
        if [[ -n "$match" ]]; then
            echo "$match" >> "$OUTPUT_CSV"
            echo "FOUND [OK]"
        else
            echo "NOT FOUND [MISSING]"
        fi
    fi

done < "$VIP_LIST"

echo "------------------------------------------------"
echo "Done! Check $OUTPUT_CSV"
