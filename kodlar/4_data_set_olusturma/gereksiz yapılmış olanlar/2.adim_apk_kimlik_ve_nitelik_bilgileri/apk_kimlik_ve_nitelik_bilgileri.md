1️⃣ APK KİMLİK & BÜTÜNLÜK

Araç: apktool, aapt2, sha256sum
Çıktı üretir:

hash

package / version

sdk bilgisi

dex & native sayısı

➡️ En başta, hızlı filtreleme için

Paylaştığınız bu JSON dosyası, hazırladığımız iş planındaki Aşama 4 (Operasyonel Analiz) sürecinin ilk adımı olan "Dijital Kimlik Kartı" (Meta Bilgiler) çıktısıdır. Scriptin (2_1.sh) başarılı bir şekilde çalıştığını ve APK dosyasından temel kimlik verilerini ayıkladığını gösterir.

İşte bu dosyanın içerdiği bilgilerin analizdeki anlamı:
📄 Dosya İçeriği ve Analizdeki Karşılığı

    apk_file: Analiz edilen dosyanın orijinal adıdır.

    sha256: Uygulamanın benzersiz parmak izidir. Bu hash değeri, ilerleyen aşamalarda VirusTotal gibi dış kaynaklardan güvenlik sorgulaması yapabilmenize ve veri setinde aynı dosyaların mükerrer olmamasını sağlamanıza yarar.

package_name: Uygulamanın Android sistemindeki kimliğidir (Örn: com.example.app). Bu isim, uygulamanın gerçekten iddia ettiği (Askeri, Popüler vb.) kategoride olup olmadığını kontrol etmenize yardımcı olur.

version_code & version_name: Uygulamanın sürüm bilgileridir.

min_sdk & target_sdk: Uygulamanın hangi Android sürümlerini hedeflediğini gösterir.

    Güvenlik Notu: Eğer target_sdk çok düşükse, uygulama modern Android güvenlik önlemlerinden (izin isteme mekanizmaları gibi) kaçmaya çalışıyor olabilir.

apk_size_kb: Dosyanın boyutudur. Boyut ve özellik (feature) sayısı arasındaki oran, "şüpheli yoğunluk" analizi için veri sağlar.

dex_count: Uygulamanın içerdiği çalıştırılabilir kod dosyası (Dalvik Executable) sayısıdır. Çok fazla .dex dosyası, uygulamanın karmaşık olduğunu veya kod gizleme (obfuscation) teknikleri kullandığını işaret edebilir.

native_lib_count: Uygulamanın içindeki .so uzantılı kütüphane sayısıdır. Bu kütüphaneler genellikle doğrudan işlemciyle konuşan yüksek performanslı (ve analizi daha zor olan) C/C++ kodlarıdır; askeri harita motorlarında veya sofistike malware'lerde sıkça görülür.
