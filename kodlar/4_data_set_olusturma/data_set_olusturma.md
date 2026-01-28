#1 Gerekli paketler yüklenir

aapt  apktool  android-sdk   sha256sum   jadx

#2 Ön analiz ile yapısı bozuk APK ları ayırma

İnen APK'lar aşağıdaki script ile aapt kullanılarak taranır.

etiketli_tam_liste_olustur.sh

Çıktıdaki sütunlar aşağıdaki bilgileri içerir.

SHA256: Uygulamanın benzersiz kimliğidir.

SIZE: APK dosyasının diskteki boyutudur (byte cinsinden).

MARKET: Uygulamanın hangi uygulama mağazalarından (Google Play, Anzhi vb.) geldiğini gösterir.

PERMISSIONS_LIST: Uygulamanın talep ettiği tüm izinlerin (Permissions) | işaretiyle ayrılmış ham listesidir.

api_DEVICEID: Cihaz kimliğine erişim sağlayan getDeviceId çağrısının varlığı (1 veya 0).

api_EXEC: Sistem seviyesinde komut çalıştırmayı sağlayan Runtime;->exec çağrısının varlığı (1 veya 0).

api_CIPHER: Şifreleme işlemlerinde kullanılan javax/crypto paketinin varlığı (1 veya 0).

api_SMSMANAGER: SMS yönetimi ile ilgili SmsManager sınıfının varlığı (1 veya 0).

api_DYN_LOAD: Dışarıdan dinamik kod yüklemeye yarayan DexClassLoader veya loadClass varlığı (1 veya 0).

int_BOOT: Cihaz açıldığında uygulamanın otomatik başlamasını tetikleyen BOOT_COMPLETED intent kontrolüdür (1 veya 0).

LABEL: Bizim belirlediğimiz etiket de bu listeye eklenecek. 

    0: Benign (Temiz)

    1: Malware (Zararlı)

    3: Popular (Popüler)

    4: Military (Askeri)
    
#3 
