#!/usr/bin/env python3
import os, hashlib, zipfile, json, shutil, subprocess
from androguard.misc import AnalyzeAPK

# =========================
# CONFIGURATION
# =========================
APK_DIR = "/run/media/yigit/DISK/dataset/Popular"   # Input directory with APKs
OUT_DIR = "./output"                            # Output directory
JADX_BIN = "/usr/bin/jadx"                          # Path to jadx binary
TEMP_WORK_DIR = "./temp_jadx"                       # Temporary work dir
CPU_CORES = 1                                       # Single-thread for OPSEC
JADX_OPTS = ["--threads-count", str(CPU_CORES), "--no-res", "--no-debug-info"]

os.makedirs(OUT_DIR, exist_ok=True)

def analyze_apk(apk_path):
    apk_name = os.path.basename(apk_path).replace(".apk", "")
    output_dir = os.path.join(OUT_DIR, apk_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"[*] Analyzing {apk_name}")

    # --- SHA256 ---
    sha256 = hashlib.sha256(open(apk_path, "rb").read()).hexdigest()

    # --- Manifest parsing with androguard ---
    a, d, dx = AnalyzeAPK(apk_path)
    permissions = a.get_permissions()
    activities  = a.get_activities()
    services    = a.get_services()
    receivers   = a.get_receivers()

    # --- Version info (correct methods for androguard 4.x) ---
    package_name = a.get_package()
    version_code = a.get_androidversion_code()
    version_name = a.get_androidversion_name()
    min_sdk      = a.get_min_sdk_version()
    target_sdk   = a.get_target_sdk_version()

    # --- Native libs (.so) + dex count ---
    dex_count = 0
    native_libs = []
    with zipfile.ZipFile(apk_path, "r") as z:
        for name in z.namelist():
            if name.endswith(".dex"):
                dex_count += 1
            if name.endswith(".so"):
                native_libs.append(name)

    # --- TEMP_WORK_DIR for JADX ---
    if os.path.exists(TEMP_WORK_DIR):
        shutil.rmtree(TEMP_WORK_DIR)
    os.makedirs(TEMP_WORK_DIR, exist_ok=True)

    api_hits = {}
    try:
        subprocess.run(
            [JADX_BIN] + JADX_OPTS + ["-d", TEMP_WORK_DIR, apk_path],
            timeout=300,  # 5 minutes
            check=False
        )
        src_dir = os.path.join(TEMP_WORK_DIR, "sources")
        if os.path.exists(src_dir):
            keywords = {
                "api_location": ["LocationManager", "FusedLocationProvider"],
                "api_media_projection": ["MediaProjection"],
                "api_sensor_av": ["Camera", "AudioRecord", "MediaRecorder"],
                "api_dynamic_load": ["DexClassLoader", "PathClassLoader"],
                "api_jni": ["System.loadLibrary"]
            }
            for key, patterns in keywords.items():
                api_hits[key] = []
                for root, _, files in os.walk(src_dir):
                    for f in files:
                        if f.endswith((".java", ".kt")):
                            path = os.path.join(root, f)
                            try:
                                text = open(path, errors="ignore").read()
                                if any(p in text for p in patterns):
                                    api_hits[key].append(path)
                            except Exception:
                                continue
    except subprocess.TimeoutExpired:
        print(f"[!] Timeout: {apk_name} skipped after 5 minutes")
        shutil.rmtree(TEMP_WORK_DIR)
        return

    # --- Clean up TEMP_WORK_DIR ---
    shutil.r
