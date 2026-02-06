import os
import psycopg2
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Mengambil Link Database dari Settingan Vercel
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# --- KHUSUS VERCEL: Route untuk bikin tabel pertama kali ---
@app.route('/setup_db')
def setup_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Buat Tabel Transaksi (SERIAL = Auto Increment di Postgres)
        cur.execute('''CREATE TABLE IF NOT EXISTS transaksi 
                     (id SERIAL PRIMARY KEY, waktu TEXT, nominal REAL, ket TEXT, usd REAL)''')
        
        # Buat Tabel Pengaturan
        cur.execute('''CREATE TABLE IF NOT EXISTS pengaturan 
                     (id SERIAL PRIMARY KEY, bot_token TEXT, rate REAL, fee_persen REAL)''')
        
        # Isi data default jika kosong
        cur.execute("SELECT count(*) FROM pengaturan")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO pengaturan (bot_token, rate, fee_persen) VALUES (%s, %s, %s)", 
                        ('TOKEN_DEFAULT', 17000, 2.3))
        
        conn.commit()
        cur.close()
        conn.close()
        return "Database Berhasil Dibuat! Silakan kembali ke Home."
    except Exception as e:
        return f"Gagal setup db: {e}"

# --- HALAMAN UTAMA ---
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM transaksi ORDER BY id DESC")
        transaksi_raw = cur.fetchall()
        
        cur.execute("SELECT * FROM pengaturan LIMIT 1")
        config_raw = cur.fetchone()
        
        cur.close()
        conn.close()

        # Konversi data tuple ke dictionary agar HTML tidak error
        # Struktur Tuple Postgres: (id, waktu, nominal, ket, usd) -> Index 0,1,2,3,4
        transaksi = []
        for row in transaksi_raw:
            transaksi.append({
                'waktu': row[1],
                'nominal': row[2],
                'ket': row[3],
                'usd': row[4]
            })

        # Struktur Config: (id, token, rate, fee)
        config = {
            'bot_token': config_raw[1], 
            'rate': config_raw[2], 
            'fee_persen': config_raw[3]
        }
        
        return render_template('index.html', transaksi=transaksi, config=config)
    except Exception as e:
        # Jika error, mungkin database belum disetup
        return f"Error: {e}. <br> <a href='/setup_db'>Klik disini untuk Setup Database Pertama Kali</a>"

# --- HALAMAN PENGATURAN ---
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    conn = get_db_connection()
    cur = conn.cursor()
    msg = ""
    
    if request.method == 'POST':
        # Syntax Update Postgres menggunakan %s
        cur.execute("UPDATE pengaturan SET bot_token=%s, rate=%s, fee_persen=%s WHERE id=1", 
                  (request.form['token'], request.form['rate'], request.form['fee']))
        conn.commit()
        msg = "Pengaturan berhasil disimpan!"
    
    cur.execute("SELECT * FROM pengaturan LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    config = {'bot_token': row[1], 'rate': row[2], 'fee_persen': row[3]}
    return render_template('settings.html', config=config, msg=msg)

# --- API ---
@app.route('/api/get_config')
def get_config():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pengaturan LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({"token": row[1], "rate": row[2], "fee": row[3]})

@app.route('/api/simpan_transaksi', methods=['POST'])
def simpan_transaksi():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    # Syntax Insert Postgres menggunakan %s
    cur.execute("INSERT INTO transaksi (waktu, nominal, ket, usd) VALUES (%s, %s, %s, %s)",
              (data['waktu'], data['nominal'], data['ket'], data['usd']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})

# Hapus baris if __name__ == main karena Vercel menjalankannya otomatis
