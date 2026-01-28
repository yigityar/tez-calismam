# -*- coding: utf-8 -*-
import os
import sys
import shutil

# --- GEREKLİ KÜTÜPHANELERİ KONTROL ET VE GÜVENLİ IMPORT YAP ---
try:
    # TextLoader eklendi (TXT okumak için)
    from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    print("❌ EKSİK KÜTÜPHANE HATASI!")
    print(f"Hata Detayı: {e}")
    sys.exit()

# --- AYARLAR ---
PDF_KLASORU = "./talimnameler" # Hem PDF hem TXT buraya atılacak
DB_KLASORU = "./chroma_db"

print("--- HİBRİT EĞİTİM SİSTEMİ (PDF + TXT) ---")

# 1. Klasör kontrolü
if not os.path.exists(PDF_KLASORU):
    os.makedirs(PDF_KLASORU)
    print(f"⚠️ UYARI: '{PDF_KLASORU}' klasörü bulunamadı, oluşturuldu.")
    sys.exit()

# 2. Eski Veritabanını Temizle (Temiz Kurulum için şart)
if os.path.exists(DB_KLASORU):
    print(f"🧹 Eski hafıza temizleniyor ({DB_KLASORU})...")
    shutil.rmtree(DB_KLASORU)

documents = []

# --- ADIM 1: PDF'leri Oku (Askeri Doktrin) ---
print("1️⃣  PDF Talimnameler taranıyor...")
try:
    pdf_loader = DirectoryLoader(
        PDF_KLASORU, 
        glob="**/*.pdf", 
        loader_cls=PyPDFLoader
    )
    pdf_docs = pdf_loader.load()
    
    # Metadata ekle: Bunların "Doktrin" olduğunu bilsin
    for doc in pdf_docs:
        doc.metadata["source_type"] = "military_doctrine"
        
    documents.extend(pdf_docs)
    print(f"   -> {len(pdf_docs)} sayfa PDF doktrin yüklendi.")

except Exception as e:
    print(f"   ⚠️ PDF okuma hatası (Önemli değilse geçiliyor): {e}")

# --- ADIM 2: TXT'leri Oku (Teknik Sözlük) ---
print("2️⃣  TXT Teknik Dokümanlar taranıyor...")
try:
    # TextLoader kullanıyoruz, UTF-8 desteği ile
    txt_loader = DirectoryLoader(
        PDF_KLASORU, 
        glob="**/*.txt", 
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    txt_docs = txt_loader.load()

    # Metadata ekle: Bunların "Teknik Bilgi" olduğunu bilsin
    for doc in txt_docs:
        doc.metadata["source_type"] = "technical_spec"

    documents.extend(txt_docs)
    print(f"   -> {len(txt_docs)} adet teknik doküman parçası yüklendi.")

except Exception as e:
    print(f"   ⚠️ TXT okuma hatası: {e}")

# --- KONTROL ---
if not documents:
    print(f"❌ '{PDF_KLASORU}' klasöründe hiç PDF veya TXT bulunamadı!")
    sys.exit()

print(f"Σ  TOPLAM: {len(documents)} parça veri hafızaya işleniyor...")

# --- ADIM 3: Parçala ve Kaydet ---
# Doktrin bütünlüğü için chunk size biraz büyük tutuldu
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1800, 
    chunk_overlap=300
)
chunks = text_splitter.split_documents(documents)

print(f"-> Metinler analiz için {len(chunks)} vektör parçasına bölündü.")
print("⏳ Yapay Zeka Modeli (FastEmbed) veriyi işliyor... (Bekleyiniz)")

try:
    embeddings = FastEmbedEmbeddings()
    vector_store = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=DB_KLASORU
    )
    print(f"\n✅ EĞİTİM BAŞARIYLA TAMAMLANDI!")
    print(f"Sistem artık hem Askeri Kuralları (PDF) hem de Teknik Tanımları (TXT) biliyor.")
    
except Exception as e:
    print(f"❌ Veritabanı oluşturma hatası: {e}")
