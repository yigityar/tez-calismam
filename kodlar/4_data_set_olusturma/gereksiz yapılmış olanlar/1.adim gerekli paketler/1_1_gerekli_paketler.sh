# Ad?m 1.1: apktool kurulumu
sudo apt update
sudo apt install apktool -y

# Ad?m 1.2: aapt2 kurulumu (Android SDK Build-tools içinde)
sudo apt install android-sdk -y
# aapt2 genelde /usr/lib/android-sdk/build-tools/ dizininde olur

# Ad?m 1.3: hash için coreutils (Kali'de zaten var)
which sha256sum

# Ad?m 1.4: jadx CLI (opsiyonel, sonraki ad?mlar için)
sudo apt install jadx -y
