#1 genel paket secme kriterleri 
   Tüm paketler için aranan özellikler
   aciklamali_apk_secme_kriterleri.csv'de kriterler belirtilmiştir.

Ayrıca Gürültü Azaltma (Noise Reduction) için	1 <= vt_detection <= 3 olanlar APK veri setinden hariç  tutulmuştur. 
Etiketleme güvenilirliğini (Label Reliability) arttırmak, antivirüs motorları arasında tam mutabakat sağlanamayan "Gri Bölge" (şüpheli) uygulamalar analiz dışı bırakılmıştır.

#2 Kriterlere uyan APK'ların sayımı
Belirlenen kriterlerle AndroZoo'dan indirilmiş olan 2022 sonrası APK listesi içerisinde sayac.sh kodu çalıştırılmıştır.






#3 Genel liste
Sayaçla bulunan kriterlere uyan APK'lar içinden her grupta yarısı Google Play içinden yarısı Google Play dışından olacak şekilde 1.000 zararsız, 1.000 zararlı APK rastgele seçilmiştir.


--- Sayaç Sonucu ---
Toplam Temiz (Benign)   : 81562
Toplam Zararlı (Malware): 9827
------------------------

play.google.com                77693           75460           2233           
anzhi                          10036           5071            4965           
appchina                       3312            901             2411           
VirusShare                     251             4               247            
fdroid                         179             179             0              
mi.com                         7               6               1              
PlayDrone                      3               3               0              
MARKET_ADI                     TOPLAM          BENIGN          MALWARE 

1.000 er apk'dan oluşan zararlı ve zararsız listeler aşağıdadır.

3_3_balanced_benign.csv
3_3_balanced_malware.csv  

#4 Popular uygulama listesi
Cihazlarda hazır olarak bulunmayan, kullanıcıların sonradan indirdiği 500 Milyon ve üzeri indirilmiş 31 uygulama Popular uygulama listesine alınmıştır.

3_4_popular_uygulamalar.csv

#5 Askeri uygulama listesi
Bu grup tam olarak kategoriden vb etiketlerden bulunamaz. Bu sebeple önce Askeri terimlerden oluşan bir arama listesi oluşturulmuştur.  
3_5_1_askeri_uygulama_terimleri.csv

Ardından bu terimler hem uygulama ismi (2 puan) hem açıklamaları (1 puan) hem de yorumlarda (her yorum 3 puan) aratılmış, bulunan uygulamalar puanlanmıştır. 

3_5_2_playstoreda_askeri_uygulama_bulma.py

ilk sonuçlar  3_5_3_google_play_military_scores.csv dedir.

Bulunan sonuçlar içerisinden oyun tarzında olanlar manuel şekilde silinmiş ve 77 adedi seçilmiştir.

3_5_4_ayıklanmış_askeri_liste.csv

3_5_4_askeri_uygulama_APKları.csv

#6 Uygulamaların İndirilmesi

Belirlenen dört gruptaki uygulama AndroZoo'dan alınan API key ile aşağıdaki script vasıtasıyla indirilmiştir.

3_6_apk_indirme.sh




