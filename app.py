from flask import Flask, render_template_string, request, jsonify
import sqlite3
import os

app = Flask(__name__)
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

# Chiroyli dizayn va funksional to'g'ridan-to'g'ri shu yerda
HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Davlat bayrog'i · Angren</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #0b192c;
            color: #fff;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            background: #1e3e62;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            max-width: 450px;
            width: 100%;
        }
        h2 { text-align: center; color: #ff6500; margin-bottom: 20px; }
        label { display: block; margin-top: 10px; font-size: 14px; color: #eee; }
        input {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            border-radius: 6px;
            border: 1px solid #000;
            background: #0b192c;
            color: #fff;
            box-sizing: border-box;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            margin-top: 20px;
            border-radius: 6px;
            border: none;
            background: #ff6500;
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover { background: #e55a00; }
        .hidden { display: none; }
        .lang-bar { display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 15px; }
        .lang-btn { padding: 5px 10px; background: #0b192c; border: 1px solid #ff6500; color: #fff; border-radius: 4px; cursor: pointer; width: auto; margin: 0; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="lang-bar">
            <button class="lang-btn">UZ</button>
            <button class="lang-btn">RU</button>
        </div>
        
        <div id="form-section">
            <h2>Bayroq Viktorinasi</h2>
            <label>Telefon raqami</label>
            <input type="text" id="phone" value="+998">
            
            <label>Ta'lim olayotgan maktab</label>
            <input type="text" id="school" placeholder="Masalan: 25-maktab">
            
            <label>MFY (mahalla fuqarolar yig'ini)</label>
            <input type="text" id="mfy" placeholder="Mahalla nomi">
            
            <button onclick="startQuiz()">Boshlash</button>
        </div>

        <div id="quiz-section" class="hidden">
            <h3 id="question-title">Savol</h3>
            <div id="options-box"></div>
        </div>
    </div>

    <script>
        const questions = [
            {
                q: "O'zbekiston Respublikasining 'Davlat bayrog'i to'g'risida'gi Qonuni ilk bor nechanchi yilda qabul qilingan va undagi yulduzlar nimani anglatadi?",
                options: [
                    "1991-yil 18-noyabr, 12 ta burj (zodiak) belgisi va osmon sferasidagi o'n ikki oy",
                    "1991-yil 31-avgust, 12 ta oy",
                    "1992-yil 2-iyul, 12 ta viloyat"
                ],
                answer: "1991-yil 18-noyabr, 12 ta burj (zodiak) belgisi va osmon sferasidagi o'n ikki oy"
            }
        ];
        let currentQ = 0;
        let score = 0;
        let userData = {};

        function startQuiz() {
            userData.phone = document.getElementById('phone').value;
            userData.school = document.getElementById('school').value;
            userData.mfy = document.getElementById('mfy').value;

            if(!userData.phone || userData.phone.length < 5) {
                alert("Telefon raqamini kiriting!");
                return;
            }

            document.getElementById('form-section').classList.add('hidden');
            document.getElementById('quiz-section').classList.remove('hidden');
            loadQuestion();
        }

        function loadQuestion() {
            if(currentQ >= questions.length) {
                submitData();
                return;
            }
            let item = questions[currentQ];
            document.getElementById('question-title').innerText = item.q;
            let box = document.getElementById('options-box');
            box.innerHTML = '';
            item.options.forEach(opt => {
                let btn = document.createElement('button');
                btn.innerText = opt;
                btn.onclick = () => {
                    if(opt === item.answer) score++;
                    currentQ++;
                    loadQuestion();
                };
                box.appendChild(btn);
            });
        }

        function submitData() {
            fetch('/api/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user_name: "O'quvchi",
                    phone: userData.phone,
                    school: userData.school,
                    mfy: userData.mfy,
                    score: score,
                    total: questions.length
                })
            }).then(res => res.json()).then(data => {
                document.querySelector('.container').innerHTML = `<h2>Natijangiz saqlandi!</h2><p>To'plagan ochko: ${score} / ${questions.length}</p>`;
            }).catch(err => {
                alert("Aloqa xatosi. Qayta urinib ko'ring.");
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/submit', methods=['POST'])
def submit_result():
    try:
        data = request.json
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO results (user_name, phone, school, mfy, score, total) VALUES (?, ?, ?, ?, ?, ?)',
            (data.get('user_name'), data.get('phone'), data.get('school'), data.get('mfy'), data.get('score'), data.get('total'))
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin')
def admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_name, phone, school, mfy, score, total, created_at FROM results ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html lang="uz">
    <head><meta charset="UTF-8"><title>Admin Panel</title>
    <style>
        body { font-family: Arial; background: #f4f6f9; padding: 20px; }
        table { width: 100%; border-collapse: collapse; background: #fff; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: center; }
        th { background: #007bff; color: white; }
    </style>
    </head>
    <body>
        <h1>Admin Panel - Natijalar Tarixi</h1>
        <table>
            <tr><th>Telefon</th><th>Maktab</th><th>MFY</th><th>Natija</th><th>Sana</th></tr>
    '''
    for r in rows:
        html += f"<tr><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><b>{r[4]}</b>/{r[5]}</td><td>{r[6]}</td></tr>"
    html += "</table></body></html>"
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    

    
