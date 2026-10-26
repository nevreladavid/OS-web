import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")

def get_db_connection():
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            return conn
        except psycopg2.OperationalError:
            print("Čekám na databázi...")
            time.sleep(2)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hodnoty (
            id SERIAL PRIMARY KEY,
            hodnota TEXT,
            vytvoreno TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("SELECT count(*) FROM hodnoty;")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("INSERT INTO hodnoty (hodnota) VALUES (%s);", ('Ahoj z Dockeru a PostgreSQL! 🚀',))
        conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nova_hodnota = request.form.get('hodnota')
        
        if nova_hodnota and nova_hodnota.strip():
            cisty_text = nova_hodnota.strip()
            
            # Bezpečnostní kontrola: povolíme maximálně 255 znaků
            if len(cisty_text) <= 255:
                cur.execute("INSERT INTO hodnoty (hodnota) VALUES (%s);", (cisty_text,))
                conn.commit()
                print(f"Příchozí zpráva z webu: {cisty_text}")
                
        cur.close()
        conn.close()
        return redirect(url_for('index'))

    cur.execute("SELECT id, hodnota, vytvoreno FROM hodnoty ORDER BY id DESC;")
    zaznamy = cur.fetchall()
    
    cur.close()
    conn.close()

    zaznamy_data = []
    for z in zaznamy:
        if z[2]:
            dt_utc = z[2].replace(tzinfo=timezone.utc) if z[2].tzinfo is None else z[2]
            dt_local = dt_utc.astimezone(ZoneInfo("Europe/Prague"))
            datum_formatted = dt_local.strftime('%d.%m.%Y %H:%M:%S')
        else:
            datum_formatted = ""
        
        zaznamy_data.append({
            'text': z[1],
            'date': datum_formatted
        })

    return render_template('index.html', zaznamy=zaznamy_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)