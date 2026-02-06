import os
import psycopg2
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Ambil URL Database dari settingan Vercel (nanti kita set)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Syntax SQL Postgres sedikit beda dengan SQLite (SERIAL vs INTEGER PRIMARY KEY AUTOINCREMENT)
    cur.execute('''CREATE TABLE IF NOT EXISTS transaksi 
                 (id SERIAL PRIMARY KEY, waktu TEXT, nominal REAL, ket TEXT, usd REAL)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS pengaturan 
                 (id SERIAL PRIMARY KEY, bot_token TEXT, rate REAL, fee_persen REAL)''')
    
    # Cek isi tabel
    cur.execute("SELECT count(*) FROM pengaturan")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO pengaturan (bot_token, rate, fee_persen) VALUES (%s, %s, %s)", 
                    ('TOKEN_DEFAULT', 17000, 2.3))
    
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transaksi ORDER BY id DESC")
    transaksi = cur.fetchall()
    
    cur.execute("SELECT * FROM pengaturan LIMIT 1")
    config = cur.fetchone() # Di Postgres, hasilnya tuple, bukan dict row
    
    # Kita rapihkan data agar mudah dibaca HTML
    config_dict = {'bot_token': config[1], 'rate': config[2], 'fee_persen': config[3]}
    
    # Ubah data transaksi jadi dictionary list
    trans_list = []
    for row in transaksi:
        trans_list.append({
            'waktu': row[1],
            'nominal': row[2],
            'ket': row[3],
            'usd': row[4]
        })
        
    cur.close()
    conn.close()
    return render_template('index.html', transaksi=trans_list, config=config_dict)

# ... (Kode Route /settings dan API sama logikanya, 
#      tapi ganti tanda tanya '?' menjadi '%s' untuk placeholder SQL) ...

# Contoh Route Simpan API yang sudah diubah ke Postgres:
@app.route('/api/simpan_transaksi', methods=['POST'])
def simpan_transaksi():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO transaksi (waktu, nominal, ket, usd) VALUES (%s, %s, %s, %s)",
              (data['waktu'], data['nominal'], data['ket'], data['usd']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})

# Vercel butuh variable 'app' ini terekspos
if __name__ == '__main__':
    # init_db() # Di Vercel kita tidak jalankan init setiap request, sebaiknya manual atau cek error
    app.run(debug=True)