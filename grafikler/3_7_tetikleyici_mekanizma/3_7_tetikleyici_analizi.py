import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# 1. Veri Yükleme
df = pd.read_csv('Dataset_Full.csv', low_memory=False)

# 2. Kategorileri Tanımlama
label_map = {0: 'Zararsız', 1: 'Zararlı', 2: 'Popüler', 3: 'Askeri'}
category_order = ['Zararsız', 'Zararlı', 'Popüler', 'Askeri']
df['Kategori'] = df['LABEL'].map(label_map)

# 3. İlgili Sütunların Seçimi
cols = {
    'behavioral_structural_data_trigger_types_auto_triggered': 'Auto-Triggered (Otomatik)',
    'behavioral_structural_data_trigger_types_user_triggered': 'User-Triggered (Kullanıcı)'
}

# 4. Veriyi Görselleştirmeye Hazırlama
subset = df[['Kategori'] + list(cols.keys())].copy()
subset.rename(columns=cols, inplace=True)

# Veriyi uzun formata (Long Format) çeviriyoruz
df_melted = subset.melt(id_vars='Kategori', var_name='Tetikleyici Türü', value_name='Sayaç')

# 5. Görselleştirme
sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 7))

ax = sns.barplot(
    data=df_melted,
    x='Kategori',
    y='Sayaç',
    hue='Tetikleyici Türü',
    order=category_order,
    palette='Set2',  # Akademik ve ayırt edici renkler
    errorbar=None    # Hata çubuklarını kaldırıp ortalamaya odaklanalım
)

# 6. Grafik Düzenlemeleri
plt.title('Ortalama Uygulama Başlatma Mekanizmaları', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Uygulama Kategorisi', fontsize=13)
plt.ylabel('Ortalama Tespit Sayısı', fontsize=13)

# Y ekseni formatı (Bilimsel gösterimi kapatma)
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.ticklabel_format(style='plain', axis='y')

# Sütunların üzerine değerleri yazdırma
for p in ax.patches:
    height = p.get_height()
    if height > 0:
        ax.annotate(f'{height:.1f}', 
                    (p.get_x() + p.get_width() / 2., height), 
                    ha='center', va='center', 
                    xytext=(0, 9), 
                    textcoords='offset points',
                    fontsize=10, fontweight='bold')

sns.despine(left=True)
plt.legend(title='Başlatma Mekanizması', bbox_to_anchor=(1.01, 1), loc='upper left')
plt.tight_layout()

# Kaydetme
plt.savefig('tetikleyici_analizi.png', dpi=300, bbox_inches='tight')
plt.show()
