# -*- coding: utf-8 -*-
import os
import sys

# --- GEREKLİ KÜTÜPHANELERİ KONTROL ET VE GÜVENLİ IMPORT YAP ---
try:
    from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
    # Yeni LangChain versiyonlarında import yolu değişti:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    print("❌ EKSİK KÜTÜPHANE HATASI!")
    print(f"Hata Detayı: {e}")
    print("Lütfen şu komutu terminalde çalıştırıp tekrar deneyin:")
    print("pip install langchain-community langchain-chroma langchain-text-splitters fastembed pypdf chromadb")
    sys.exit()

# --- AYARLAR ---
PDF_KLASORU = "./talimnameler"
DB_KLASORU = "./chroma_db"

print("--- 1. ADIM: PDF'ler Okunuyor ---")

# Klasör kontrolü
if not os.path.exists(PDF_KLASORU):
    os.makedirs(PDF_KLASORU)
    print(f"⚠️ UYARI: '{PDF_KLASORU}' klasörü bulunamadı, oluşturuldu.")
    print(f"Lütfen PDF talimnamelerinizi '{PDF_KLASORU}' klasörüne atın ve tekrar çalıştırın.")
    sys.exit()

# Recursive arama (**/*.pdf) ile alt klasörleri de kapsar
try:
    loader = DirectoryLoader(
        PDF_KLASORU, 
        glob="**/*.pdf", 
        loader_cls=PyPDFLoader
    )
    documents = loader.load()
except Exception as e:
    print(f"❌ PDF okuma sırasında hata oluştu: {e}")
    sys.exit()

if not documents:
    print(f"⚠️ '{PDF_KLASORU}' klasöründe hiç PDF bulunamadı!")
    sys.exit()

# Metadata etiketleme
for doc in documents:
    doc.metadata["source_type"] = "military_doctrine"

print(f"-> {len(documents)} sayfa doküman hafızaya alındı.")

# --- ASKERİ METİN PARÇALAMA AYARI (1800 Karakter) ---
# Doktrin bütünlüğü için büyük parçalar kullanıyoruz.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1800, 
    chunk_overlap=300
)
chunks = text_splitter.split_documents(documents)

print(f"-> Metinler {len(chunks)} parçaya bölündü.")
print("--- 2. ADIM: Kalıcı Hafızaya (Diske) Yazılıyor ---")
print("⏳ Yapay Zeka Modeli (FastEmbed) hazırlanıyor... (İlk seferde indirme yapabilir)")

# Embedding ve Kayıt
try:
    embeddings = FastEmbedEmbeddings()
    vector_store = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=DB_KLASORU
    )
    print(f"✅ ÖĞRENME BAŞARIYLA TAMAMLANDI!")
    print(f"Bilgiler '{DB_KLASORU}' klasörüne kalıcı olarak kaydedildi.")
    print("Artık 'analiz.py' kodunu çalıştırıp sorularınızı sorabilirsiniz.")
    
except Exception as e:
    print(f"❌ Veritabanı oluşturma hatası: {e}")
