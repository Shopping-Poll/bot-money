from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)
DB_NAME = 'keuangan_pro.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
                 (id INTEGER PRIMARY KEY, waktu TEXT, nominal REAL, ket TEXT, usd REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pengaturan 
                 (id INTEGER PRIMARY KEY, bot_token TEXT, rate REAL, fee_persen REAL)''')
    c.execute("SELECT count(*) FROM pengaturan")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO pengaturan (id, bot_token, rate, fee_persen) VALUES (1, 'TOKEN_DEFAULT', 17000, 2.3)")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM transaksi ORDER BY id DESC")
    transaksi = c.fetchall()
    c.execute("SELECT * FROM pengaturan WHERE id=1")
    config = c.fetchone()
    conn.close()
    # Sekarang menggunakan render_template untuk memanggil file di folder templates
    return render_template('index.html', transaksi=transaksi, config=config)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    msg = ""
    if request.method == 'POST':
        c.execute("UPDATE pengaturan SET bot_token=?, rate=?, fee_persen=? WHERE id=1", 
                  (request.form['token'], request.form['rate'], request.form['fee']))
        conn.commit()
        msg = "Pengaturan berhasil disimpan!"
    
    c.execute("SELECT * FROM pengaturan WHERE id=1")
    config = c.fetchone()
    conn.close()
    return render_template('settings.html', config=config, msg=msg)

@app.route('/api/get_config')
def get_config():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM pengaturan WHERE id=1")
    row = c.fetchone()
    conn.close()
    return jsonify({"token": row[1], "rate": row[2], "fee": row[3]})

@app.route('/api/simpan_transaksi', methods=['POST'])
def simpan_transaksi():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO transaksi (waktu, nominal, ket, usd) VALUES (?, ?, ?, ?)",
              (data['waktu'], data['nominal'], data['ket'], data['usd']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)