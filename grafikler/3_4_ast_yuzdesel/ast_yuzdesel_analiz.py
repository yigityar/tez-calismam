import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Veri Setini Yükleme
df = pd.read_csv('Dataset_Full.csv', low_memory=False)

# 2. Kategorileri Tanımlama (İstediğin formatta)
label_map = {0: 'Zararsız', 1: 'Zararlı', 2: 'Popüler', 3: 'Askeri'}
df['Kategori'] = df['LABEL'].map(label_map)

# Her kategorideki toplam uygulama sayısını hesapla (Yüzde hesabı için payda)
kategori_toplamlari = df['Kategori'].value_counts()

# Analiz edilecek AST sütunları
ast_cols = {
    'ast_analysis_camera': 'Kamera',
    'ast_analysis_jni': 'JNI Kullanımı',
    'ast_analysis_location': 'Konum',
    'ast_analysis_microphone': 'Mikrofon',
    'ast_analysis_media_projection' : 'Medya Projeksiyonu'
}

# 3. Yüzdesel Veri Tablosunu Oluşturma
plot_verisi = []
for col, label_tr in ast_cols.items():
    if col in df.columns:
        # Davranışı sergileyenlerin kategorilere göre sayısını al
        davranis_sayilari = df[df[col] > 0].groupby('Kategori').size()
        
        for kat in label_map.values():
            sayi = davranis_sayilari.get(kat, 0)
            toplam = kategori_toplamlari.get(kat, 0)
            yuzde = (sayi / toplam * 100) if toplam > 0 else 0
            
            plot_verisi.append({
                'Davranış': label_tr,
                'Kategori': kat,
                'Yüzde (%)': yuzde
            })

df_plot = pd.DataFrame(plot_verisi)

# 4. Görselleştirme Ayarları
sns.set_theme(style="whitegrid")
plt.figure(figsize=(14, 8))

# Palette: 'viridis' veya 'Set2' akademik metinlerde iyi durur
ax = sns.barplot(data=df_plot, x='Davranış', y='Yüzde (%)', hue='Kategori', palette='viridis')

# Y eksenini %100'e kadar sınırla (Gerekirse biraz pay bırakılabilir)
ax.set_ylim(0, 110)

# Başlık ve Etiketler
plt.title('Uygulama Kategorilerine Göre AST Davranış Prevalansı (%)', fontsize=16, fontweight='bold', pad=25)
plt.xlabel('AST ile Tespit Edilen Kritik API Çağrıları', fontsize=13)
plt.ylabel('Kategori İçindeki Görülme Oranı (%)', fontsize=13)

# Çubukların üzerine yüzde değerlerini yazdıralım
for p in ax.patches:
    y_degeri = p.get_height()
    if y_degeri > 0:
        ax.annotate(f'%{y_degeri:.1f}', 
                    (p.get_x() + p.get_width() / 2., y_degeri), 
                    ha='center', va='center', 
                    xytext=(0, 10), 
                    textcoords='offset points',
                    fontsize=9, fontweight='bold')

sns.despine(left=True)
plt.legend(title='Uygulama Sınıfı', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()

# 5. Kaydetme
plt.savefig('ast_yuzdesel_analiz.png', dpi=300, bbox_inches='tight')
plt.show()
