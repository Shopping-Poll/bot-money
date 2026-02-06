import telebot
import requests
import time
from datetime import datetime

# ---------------------------------------------------------
# PENTING: GANTI INI DENGAN LINK VERCEL ANDA YANG SUDAH JADI
# Contoh: https://bot-keuangan-saya.vercel.app/api
# Jangan lupa pakai /api di belakangnya
# ---------------------------------------------------------
API_URL = "https://bot-money.vercel.app/api" 

def get_settings():
    try:
        # Kita tambahkan timeout agar bot tidak hang kalau internet lemot
        resp = requests.get(f"{API_URL}/get_config", timeout=10)
        
        # Cek jika website error (bukan 200 OK)
        if resp.status_code != 200:
            print(f"Website Error: {resp.status_code}")
            return None
            
        return resp.json()
    except Exception as e:
        print(f"Gagal konek ke Vercel: {e}")
        return None

# --- SETUP AWAL ---
print("Sedang menghubungkan ke Vercel...")
settings = None

# Loop sampai berhasil konek (agar tidak crash di awal)
while settings is None:
    settings = get_settings()
    if settings is None:
        print("Mencoba lagi dalam 5 detik...")
        time.sleep(5)

print(f"✅ BERHASIL TERHUBUNG! Bot aktif dengan Rate: {settings['rate']}")
bot = telebot.TeleBot(settings['token'])

@bot.message_handler(commands=['in'])
def catat_masuk(message):
    try:
        current_config = get_settings()
        if not current_config:
            bot.reply_to(message, "Gagal konek ke server database!")
            return

        rate_skrg = current_config['rate']
        fee_skrg = current_config['fee']
        
        args = message.text.split(maxsplit=2)
        if len(args) < 2:
            bot.reply_to(message, "Gunakan: /in [nominal] [ket]")
            return

        nominal = float(args[1])
        keterangan = args[2] if len(args) > 2 else ""
        
        fee_multiplier = 1 - (fee_skrg / 100)
        usd = (nominal / rate_skrg) * fee_multiplier
        waktu = datetime.now().strftime("%H:%M:%S")

        payload = {'waktu': waktu, 'nominal': nominal, 'ket': keterangan, 'usd': usd}
        
        # Kirim data ke Vercel
        kirim = requests.post(f"{API_URL}/simpan_transaksi", json=payload)
        
        if kirim.status_code == 200:
            balasan = (
                f"✅ **Sukses!**\nRate: {rate_skrg} | Fee: {fee_skrg}%\n"
                f"{waktu}  {int(nominal)} / {rate_skrg} * ({fee_multiplier:.3f})={usd:.2f}U {keterangan}"
            )
            bot.reply_to(message, balasan)
        else:
            bot.reply_to(message, "Gagal menyimpan ke database Vercel.")

    except Exception as e:
        bot.reply_to(message, f"Error di bot: {e}")

# Jalankan Bot
bot.infinity_polling()
