import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# 1. Veri Yükleme
df = pd.read_csv('Dataset_Full.csv', low_memory=False)

# 2. Kategorileri Tanımlama ve Sıralama
label_map = {0: 'Zararsız', 1: 'Zararlı', 2: 'Popüler', 3: 'Askeri'}
category_order = ['Zararsız', 'Zararlı', 'Popüler', 'Askeri']
df['Kategori'] = df['LABEL'].map(label_map)

# 3. Analiz Edilecek API Envanteri Sütunları
# İsimleri daha anlaşılır yapmak için bir sözlük kullanalım
api_map = {
    'behavioral_structural_data_api_inventory_torch': 'El feneri',
    'behavioral_structural_data_api_inventory_microphone': 'Mikrofon',
    'behavioral_structural_data_api_inventory_location': 'Konum',
    'behavioral_structural_data_api_inventory_system_commands': 'Sistem Komutları',
    'behavioral_structural_data_api_inventory_network_io': 'Ağ Erişimi',
    'behavioral_structural_data_api_inventory_vibration': 'Titreşim'
}

# 4. Veriyi Hazırlama (Ortalama Alma ve Format Değiştirme)
# Sadece ilgili sütunları ve kategoriyi alalım
subset_cols = ['Kategori'] + list(api_map.keys())
df_subset = df[subset_cols].copy()

# Sütun isimlerini Türkçeleştirelim
df_subset.rename(columns=api_map, inplace=True)

# "Melt" işlemi ile veriyi uzun formata çevirelim (Seaborn için)
df_melted = df_subset.melt(id_vars='Kategori', var_name='Yetenek (API)', value_name='Çağrı Sayısı')

# 5. Görselleştirme
sns.set_theme(style="whitegrid")
plt.figure(figsize=(14, 8))

ax = sns.barplot(
    data=df_melted,
    x='Kategori',
    y='Çağrı Sayısı',
    hue='Yetenek (API)',
    order=category_order,
    palette='mako', # Mako paleti teknik/siber temaya uygundur
    errorbar=None   # Güven aralığı çizgilerini sadelik için kapatalım
)

# 6. Grafik Ayarları
plt.title('Bytecode Analizi: Uygulama Kategorilerine Göre Ortalama API Çağrıları', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Uygulama Kategorisi', fontsize=13)
plt.ylabel('Ortalama Çağrı Sayısı (Adet)', fontsize=13)

# Y eksenini sadeleştirelim
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.ticklabel_format(style='plain', axis='y')

# Çubukların üzerine değerleri yazdıralım
for p in ax.patches:
    height = p.get_height()
    if height > 0:
        # Değer çok küçükse 0.1, büyükse tam sayı formatında gösterelim
        label_text = f'{height:.1f}' if height < 10 else f'{int(height)}'
        ax.annotate(label_text, 
                    (p.get_x() + p.get_width() / 2., height), 
                    ha='center', va='center', 
                    xytext=(0, 9), 
                    textcoords='offset points',
                    fontsize=9, fontweight='bold')

sns.despine(left=True)
plt.legend(title='Teknik Yetenekler', bbox_to_anchor=(1.01, 1), loc='upper left')
plt.tight_layout()

# Dosya ismini 'bytecode_analiz.py' olarak kaydedebilirsiniz
plt.savefig('bytecode_yapisal_oznitelik.png', dpi=300, bbox_inches='tight')
plt.show()
