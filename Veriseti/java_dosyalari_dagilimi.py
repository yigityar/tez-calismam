import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Ayarlar ve Veri Yükleme
# Dosyanızın adını ve yolunu kontrol edin
FILE_PATH = '/home/yigit/tez-calismam/Veriseti/Dataset_Full.csv' 
OUTPUT_IMAGE = 'java_file_distribution.png'

try:
    df = pd.read_csv(FILE_PATH)
    print(f"[*] Veri yüklendi: {len(df)} satır.")
except FileNotFoundError:
    print(f"[!] Hata: {FILE_PATH} dosyası bulunamadı!")
    exit()

# 2. Hazırlık: Etiketleri isimlendirme
label_map = {0: "Benign", 1: "Malware", 2: "Popular", 3: "Military"}
df['Category'] = df['LABEL'].map(label_map)
category_order = ["Benign", "Malware", "Popular", "Military"]

# 3. Görselleştirme
plt.figure(figsize=(12, 7))
sns.set_theme(style="whitegrid")

# Keman grafiği yoğunluğu, kutu grafiği ise istatistiksel özetleri gösterir
ax = sns.violinplot(data=df, x='Category', y='jadx_java_file_count', 
                    order=category_order, palette="muted", inner="quartile")

plt.title('Kategorilere Göre Java Dosya Sayısı Dağılımı', fontsize=16, fontweight='bold')
plt.ylabel('Java Dosya Sayısı (Logaritmik Ölçek)', fontsize=12)
plt.xlabel('Uygulama Kategorisi', fontsize=12)

# Y eksenini logaritmik yapıyoruz çünkü Malware (500) ve Popular (13.000) arasında uçurum var
plt.yscale('log') 

# Ortalama değerleri grafik üzerine yazdıralım
means = df.groupby('Category')['jadx_java_file_count'].mean().reindex(category_order)
for i, mean in enumerate(means):
    plt.text(i, mean, f'Ort: {int(mean)}', 
             horizontalalignment='center', size='small', color='black', weight='semibold')

plt.tight_layout()
plt.savefig(OUTPUT_IMAGE, dpi=300) # Teze uygun yüksek çözünürlük
print(f"[✓] Grafik kaydedildi: {OUTPUT_IMAGE}")
plt.show()
