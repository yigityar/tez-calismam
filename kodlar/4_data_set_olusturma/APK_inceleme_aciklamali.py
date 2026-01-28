#!/usr/bin/env python3
import os               #os: dosya/dizin işlemleri, batch gezinme
import hashlib          #hashlib: APK kimliklendirme (SHA-256)
import zipfile          #zipfile: APK’nin ZIP bütünlüğü ve içerik analizi
import json             #json: standartlaştırılmış çıktı üretimi
import shutil           #shutil: geçici dizin temizliği
import subprocess       #subprocess: JADX çağırma
import time             #time: performans ve süre ölçümü

# =========================
# ANDROGUARD IMPORT (SAFE)
# =========================
try:
    from androguard.core.apk import APK
except ImportError:
    from androguard.core.bytecodes.apk import APK  #Androguard’ın farklı sürümleriyle uyumluluk sağlar.

import javalang    #Java kaynak kodunu AST (Abstract Syntax Tree) olarak parse etmek için kullanılır.     

# =========================
# CONFIG
# =========================
APK_DIR = "/home/azureuser/dataset/apks"        #Girdi APK dizini
OUT_DIR = "/home/azureuser/dataset/output"      #Çıktı dataset dizini
JADX_BIN = "/usr/local/bin/jadx"                #JADX binary yolu
TEMP_WORK_DIR = "/home/azureuser/temp_jadx"     #Geçici decompile alanı

JADX_OPTS = [
    "--no-res",
    "--no-debug-info"                           #Resource’ları ve debug bilgilerini çıkartmaz, Sadece kod analizi odaklı decompile
]

os.makedirs(OUT_DIR, exist_ok=True)             #Çıktı dizini yoksa oluşturur.

# =========================
# AST TARGET METHODS
# Hangi API çağrılarının davranış sinyali sayılacağını tanımlar.
# =========================
AST_TARGETS = {
    "location": [
        "requestLocationUpdates",
        "getLastLocation",
        "getCurrentLocation"
    ],
    "microphone": [
        "startRecording"
    ],
    "camera": [
        "openCamera",
        "open"
    ],
    "media_projection": [
        "getMediaProjection",
        "createVirtualDisplay"
    ],
    "dynamic_load": [
        "DexClassLoader",
        "PathClassLoader"
    ],
    "jni": [
        "loadLibrary"
    ]
}

# =========================
# APK ANALYSIS
# =========================
def analyze_apk(apk_path: str):
    apk_name = os.path.basename(apk_path).replace(".apk", "")
    output_dir = os.path.join(OUT_DIR, apk_name)                    #Her APK için izole bir çıktı klasörü oluşturur.
    summary_file = os.path.join(output_dir, "summary.json")
    raw_file = os.path.join(output_dir, "raw_features.json")

    if os.path.exists(summary_file):
        print(f"[-] Skipped: {apk_name}")                           #Daha önce analiz edilmiş APK’yi atlar.
        return

    print(f"[*] Analyzing: {apk_name}")
    os.makedirs(output_dir, exist_ok=True)

    # ---------- HASH ----------
    #APK’ye benzersiz kimlik atar.
    try:
        with open(apk_path, "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
    except Exception:
        sha256 = None

    # ---------- ZIP VALIDATION ----------
    #Bozuk / sahte APK’leri ayıklar.
    
    if not zipfile.is_zipfile(apk_path):
        summary = {
            "apk_name": apk_name,
            "sha256": sha256,
            "analysis_state": "invalid_apk",
            "error": "File is not a valid ZIP/APK"
        }
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=4)
        print(f"[!] Invalid APK: {apk_name}")
        return

    # ---------- METADATA ----------
    # Paket bilgileri, SDK seviyeleri, İzinler, Component listeleri

    
    metadata = {}
    try:
        a = APK(apk_path)
        metadata = {
            "package_name": a.get_package(),
            "version_code": a.get_androidversion_code(),
            "version_name": a.get_androidversion_name(),
            "min_sdk": a.get_min_sdk_version(),
            "target_sdk": a.get_target_sdk_version(),
            "permissions": sorted(a.get_permissions()),
            "activities": sorted(a.get_activities()),
            "services": sorted(a.get_services()),
            "receivers": sorted(a.get_receivers())
        }
    except Exception as e:
        metadata["error"] = str(e)

    # ---------- ZIP STATS ----------
    # Dex sayısı, Native kod varlığı
    
    dex_count = 0
    native_libs = []

    with zipfile.ZipFile(apk_path, "r") as z:
        for name in z.namelist():
            if name.endswith(".dex"):
                dex_count += 1
            elif name.endswith(".so"):
                native_libs.append(name)

    # ---------- JADX ----------
    #APK’yi Java kaynak koda çevirir.
    shutil.rmtree(TEMP_WORK_DIR, ignore_errors=True)
    os.makedirs(TEMP_WORK_DIR, exist_ok=True)

    jadx_status = "ok"
    start_time = time.time()

    try:
        subprocess.run(
            [JADX_BIN] + JADX_OPTS + ["-d", TEMP_WORK_DIR, apk_path],
            timeout=600,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.TimeoutExpired:
        jadx_status = "timeout"
    except Exception:
        jadx_status = "error"

    duration = round(time.time() - start_time, 2)

    # ---------- AST + RAW FEATURE COLLECTION ----------
    ast_summary = {k: 0 for k in AST_TARGETS}
    ast_files = {k: [] for k in AST_TARGETS}
    java_files = []

    sources_dir = os.path.join(TEMP_WORK_DIR, "sources")

    if jadx_status == "ok" and os.path.isdir(sources_dir):
        for root, _, files in os.walk(sources_dir):
            for fname in files:
                if fname.endswith(".java"):
                    rel_path = os.path.relpath(os.path.join(root, fname), sources_dir)
                    java_files.append(rel_path)
        #Java dosyasını AST’ye dönüştürür.            
                    try:
                        with open(os.path.join(root, fname), "r", errors="ignore") as f:
                            tree = javalang.parse.parse(f.read())
        #Gerçek API çağrılarını yakalar.                            

                        for _, node in tree.filter(javalang.tree.MethodInvocation):
                            for cat, methods in AST_TARGETS.items():
                                if node.member in methods:
                                    ast_summary[cat] += 1
                                    ast_files[cat].append(rel_path)
                    except Exception:
                        continue

    shutil.rmtree(TEMP_WORK_DIR, ignore_errors=True)

    # ---------- RAW FEATURES ----------
    # Ham, geri dönülebilir, dosya bazlı veri üretir.
    raw_features = {
        "java_files": java_files,
        "ast_hits_by_file": ast_files,
        "native_libs": native_libs,
        "dex_files_count": dex_count,
        "exported_components": {
            "activities": metadata.get("activities", []),
            "services": metadata.get("services", []),
            "receivers": metadata.get("receivers", [])
        }
    }

    with open(raw_file, "w") as f:
        json.dump(raw_features, f, indent=4, ensure_ascii=False)

    # ---------- SUMMARY ----------
    # Toplu analiz için sadeleştirilmiş veri üretir.
    summary = {
        "apk_name": apk_name,
        "sha256": sha256,
        "metadata": metadata,
        "stats": {
            "dex_count": dex_count,
            "native_lib_count": len(native_libs)
        },
        
        "jadx": {
            "status": jadx_status,
            "duration_sec": duration,
            "sources_present": len(java_files) > 0,
            "java_file_count": len(java_files)
        },
        "ast_analysis": ast_summary,
        "analysis_state": "complete" if jadx_status == "ok" else "partial"
    }

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)

    print(f"[✓] Done: {apk_name}")

# =========================
# MAIN
#Tüm APK’leri deterministik sırayla analiz eder.
# =========================
def main():
    for fname in sorted(os.listdir(APK_DIR)):
        if fname.endswith(".apk"):
            analyze_apk(os.path.join(APK_DIR, fname))

if __name__ == "__main__":
    main()
