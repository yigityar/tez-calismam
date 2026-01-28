#AndroZoo'da yer alan script listesinden 2022 sonrası tüm apk ların listesi indirilmiştir.

zcat latest.csv.gz | awk -F, '{if ( $4 >= "2022-12" ) {print} }'
