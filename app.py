from flask import Flask, send_from_directory, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
DB_PATH = 'data/quiz.db'

def init_db():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            phone TEXT,
            school TEXT,
            mfy TEXT,
            score INTEGER,
            total INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Asosiy sahifa static papkadan ochiladi
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Ma'lumotlarni qabul qilish API
@app.route('/api/submit', methods=['POST'])
def submit_result():
    try:
        data = request.json
        user_name = data.get('user_name', 'Anonim')
        phone = data.get('phone', '')
        school = data.get('school', '')
        mfy = data.get('mfy', '')
        score = data.get('score', 0)
        total = data.get('total', 0)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO results (user_name, phone, school, mfy, score, total) VALUES (?, ?, ?, ?, ?, ?)',
            (user_name, phone, school, mfy, score, total)
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "message": "Natija muvaffaqiyatli saqlandi!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Admin paneli
@app.route('/admin')
def admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_name, phone, school, mfy, score, total, created_at FROM results ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return render_template('admin.html', results=rows)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
