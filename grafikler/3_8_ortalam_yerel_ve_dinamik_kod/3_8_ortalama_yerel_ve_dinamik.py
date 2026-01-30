import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# 1. Veri Yükleme
df = pd.read_csv('Dataset_Full.csv', low_memory=False)

# 2. Kategori Etiketleme ve Sıralama
label_map = {0: 'Zararsız', 1: 'Zararlı', 2: 'Popüler', 3: 'Askeri'}
category_order = ['Zararsız', 'Zararlı', 'Popüler', 'Askeri']
df['Kategori'] = df['LABEL'].map(label_map)

# 3. Analiz Edilecek Dinamik ve Yapısal Öznitelikler
feature_map = {
    
    'behavioral_structural_data_dynamic_features_jni_usage': 'JNI (Yerel Kod)',
    'behavioral_structural_data_dynamic_features_dynamic_loading': 'Dinamik Kod Yükleme'
}

# 4. Veriyi Hazırlama
subset_cols = ['Kategori'] + list(feature_map.keys())
df_subset = df[subset_cols].copy()
df_subset.rename(columns=feature_map, inplace=True)

# Uzun formata çevirme
df_melted = df_subset.melt(id_vars='Kategori', var_name='Öznitelik', value_name='Ortalama Sayı')

# 5. Görselleştirme
sns.set_theme(style="whitegrid")
plt.figure(figsize=(14, 8))

# hue='Öznitelik' ile özellikleri yan yana sütunlar halinde çizelim
ax = sns.barplot(
    data=df_melted,
    x='Kategori',
    y='Ortalama Sayı',
    hue='Öznitelik',
    order=category_order,
    palette='viridis', 
    errorbar=None
)

# 6. Estetik Ayarlar
plt.title('Ortalama Yerel ve Dinamik Kod Miktarları', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Uygulama Kategorisi', fontsize=13)
plt.ylabel('Ortalama Tespit Sayısı (Adet)', fontsize=13)

# Y ekseni formatı
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.ticklabel_format(style='plain', axis='y')

# Değerleri sütunların üzerine yazdırma
# Reflection değerleri yüksek olduğu için grafik skalası genişleyebilir,
# küçük değerlerin de okunabilmesi için etiketleme (annotation) çok önemlidir.
for p in ax.patches:
    height = p.get_height()
    if height > 0:
        # Değer 1'den küçükse ondalıklı, büyükse tam sayı göster
        label_text = f'{height:.1f}' if height < 10 else f'{int(height)}'
        
        ax.annotate(label_text, 
                    (p.get_x() + p.get_width() / 2., height), 
                    ha='center', va='center', 
                    xytext=(0, 9), 
                    textcoords='offset points',
                    fontsize=9, fontweight='bold')

sns.despine(left=True)
plt.legend(title='Ortalama Yerel ve Dinamik Kod Miktarları', bbox_to_anchor=(1.01, 1), loc='upper left')
plt.tight_layout()

# Kaydetme
plt.savefig('dinamik_yapisal_analiz.png', dpi=300, bbox_inches='tight')
plt.show()
