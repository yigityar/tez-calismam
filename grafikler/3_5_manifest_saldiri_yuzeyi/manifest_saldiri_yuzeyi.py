import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Veri Yükleme
df = pd.read_csv('Dataset_Full.csv', low_memory=False)

# 2. Kategori Etiketleme ve Kesin Sıralama Tanımı
label_map = {0: 'Zararsız', 1: 'Zararlı', 2: 'Popüler', 3: 'Askeri'}
# Grafikte görünecek x-ekseni sırası:
category_order = ['Zararsız', 'Zararlı', 'Popüler', 'Askeri']
df['Kategori'] = df['LABEL'].map(label_map)

# 3. İzin Sütunları ve Risk Hiyerarşisi
risk_cols = [
    'metadata_risk_counts_dangerous', 
    'metadata_risk_counts_signature',
    'metadata_risk_counts_normal', 
    
]

rename_map = {
    'metadata_risk_counts_dangerous': 'Tehlikeli',
    'metadata_risk_counts_normal': 'Normal',
    'metadata_risk_counts_signature': 'Signature (İmza)',
}

# Grupların kendi içindeki (renk) sırası:
hue_order = [ 'Normal', 'Tehlikeli', 'Signature (İmza)' ]

# 4. Veriyi Hazırlama
subset = df[['Kategori'] + risk_cols].copy()
subset.rename(columns=rename_map, inplace=True)
df_melted = subset.melt(id_vars='Kategori', var_name='İzin Seviyesi', value_name='İzin Sayısı')

# 5. Görselleştirme
sns.set_theme(style="whitegrid")
plt.figure(figsize=(14, 8))

# 'order' ve 'hue_order' parametreleri sıralamayı kesinleştirir
ax = sns.barplot(
    data=df_melted, 
    x='Kategori', 
    y='İzin Sayısı', 
    hue='İzin Seviyesi', 
    order=category_order,     # X ekseni sırası
    hue_order=hue_order,      # Renk/Grup sırası
    palette='rocket_r',
    errorbar=None
)

# 6. Estetik Ayarlar
plt.title('Manifest Tabanlı Saldırı Yüzeyi: Kategori Başına Ortalama İzin Dağılımı', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Uygulama Kategorisi (Sıralı)', fontsize=13)
plt.ylabel('Ortalama İzin Sayısı (Adet)', fontsize=13)

# Sayısal değerleri ekleme
for p in ax.patches:
    height = p.get_height()
    if height > 0:
        ax.annotate(f'{height:.1f}', 
                    (p.get_x() + p.get_width() / 2., height), 
                    ha='center', va='center', 
                    xytext=(0, 9), 
                    textcoords='offset points',
                    fontsize=9, fontweight='bold')

sns.despine(left=True)
plt.legend(title='Koruma Seviyesi', bbox_to_anchor=(1.01, 1), loc='upper left')
plt.tight_layout()

# Kaydetme (Önemli: Dosya adını 'manifest_sirali.py' olarak kaydedin)
plt.savefig('manifest_saldiri_yuzeyi_sirali.png', dpi=300, bbox_inches='tight')
plt.show()
