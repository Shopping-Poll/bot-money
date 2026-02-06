import telebot
import requests
from datetime import datetime
import time

API_URL = "http://127.0.0.1:5000/api"

def get_settings():
    try:
        resp = requests.get(f"{API_URL}/get_config")
        return resp.json()
    except:
        return None

# Tunggu sampai website siap
settings = None
while settings is None:
    print("Menunggu koneksi ke website...")
    settings = get_settings()
    time.sleep(2)

print(f"Bot Connect! Rate: {settings['rate']}")
bot = telebot.TeleBot(settings['token'])

@bot.message_handler(commands=['in'])
def catat_masuk(message):
    current_config = get_settings()
    rate_skrg = current_config['rate']
    fee_skrg = current_config['fee']
    
    try:
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
        requests.post(f"{API_URL}/simpan_transaksi", json=payload)
        
        balasan = (
            f"✅ **Sukses!**\nRate: {rate_skrg} | Fee: {fee_skrg}%\n"
            f"{waktu}  {int(nominal)} / {rate_skrg} * ({fee_multiplier:.3f})={usd:.2f}U {keterangan}"
        )
        bot.reply_to(message, balasan)

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

bot.infinity_polling()