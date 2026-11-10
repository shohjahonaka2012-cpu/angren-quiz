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

# Asosiy sahifa (Frontend to'g'ridan-to'g'ri shu yerda)
HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bayroq Viktorinasi - Angren</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0d1b2a; color: #fff; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { background: #1b263b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); max-width: 500px; width: 100%; text-align: center; }
        input, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; font-size: 16px; box-sizing: border-box; }
        input { background: #415a77; color: #fff; }
        input::placeholder { color: #e0e1dd; }
        button { background: #e0a96d; color: #0d1b2a; font-weight: bold; cursor: pointer; }
        button:hover { background: #f4a261; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container" id="form-container">
        <h2>O'zbekiston Bayrog'i - Olimpiada Viktorinasi</h2>
        <p>Iltimos, ma'lumotlaringizni kiriting:</p>
        <input type="text" id="username" placeholder="F.I.Sh. (Ism familiyangiz)">
        <input type="text" id="phone" placeholder="Telefon raqami (+998...)">
        <input type="text" id="school" placeholder="Ta'lim olayotgan maktabingiz">
        <input type="text" id="mfy" placeholder="MFY (Mahalla fuqarolar yig'ini)">
        <button onclick="startQuiz()">Viktorinani Boshlash</button>
    </div>

    <div class="container hidden" id="quiz-container">
        <h3 id="question-text">Savol</h3>
        <div id="options-container"></div>
    </div>

    <script>
        let userData = {};
        const questions = [
            {
                question: "O'zbekiston Respublikasining 'Davlat bayrog'i to'g'risida'gi Qonuni ilk bor nechanchi yilda qabul qilingan va undagi yulduzlar nimani anglatadi?",
                options: [
                    "1991-yil 18-noyabr, 12 ta ma'muriy hudud",
                    "1991-yil 18-noyabr, 12 ta burj (zodiak) belgisi va osmon sferasidagi o'n ikki oy",
                    "1992-yil 2-iyul, 12 ta viloyat"
                ],
                answer: "1991-yil 18-noyabr, 12 ta burj (zodiak) belgisi va osmon sferasidagi o'n ikki oy"
            },
            {
                question: "Bayroqdagi moviy rang qadimgi turkiy tilda va Temuriylar davrida nimaning ramzi hisoblangan?",
                options: [
                    "Tinchlik va osmon",
                    "Mangulik, osmon va suv (sobitqadamlik)",
                    "Faqatgina musaffo osmon"
                ],
                answer: "Mangulik, osmon va suv (sobitqadamlik)"
            }
        ];
        let currentIdx = 0;
        let score = 0;

        function startQuiz() {
            userData.name = document.getElementById('username').value;
            userData.phone = document.getElementById('phone').value;
            userData.school = document.getElementById('school').value;
            userData.mfy = document.getElementById('mfy').value;

            if(!userData.name || !userData.phone) {
                alert("Iltimos, ism va telefon raqamingizni kiriting!");
                return;
            }

            document.getElementById('form-container').classList.add('hidden');
            document.getElementById('quiz-container').classList.remove('hidden');
            loadQuestion();
        }

        function loadQuestion() {
            if(currentIdx >= questions.length) {
                finishQuiz();
                return;
            }
            let q = questions[currentIdx];
            document.getElementById('question-text').innerText = `${currentIdx + 1}-savol: ${q.question}`;
            let optDiv = document.getElementById('options-container');
            optDiv.innerHTML = '';
            q.options.forEach(opt => {
                let btn = document.createElement('button');
                btn.innerText = opt;
                btn.onclick = () => checkAnswer(opt, q.answer);
                optDiv.appendChild(btn);
            });
        }

        function checkAnswer(selected, correct) {
            if(selected === correct) score++;
            currentIdx++;
            loadQuestion();
        }

        function finishQuiz() {
            fetch('/api/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user_name: userData.name,
                    phone: userData.phone,
                    school: userData.school,
                    mfy: userData.mfy,
                    score: score,
                    total: questions.length
                })
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('quiz-container').innerHTML = `<h2>Tabriklaymiz!</h2><p>Natijangiz: ${score} / ${questions.length}</p><p>Ma'lumotlaringiz saqlandi.</p>`;
            })
            .catch(err => {
                alert("Aloqa xatosi!");
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
            <tr><th>Ism</th><th>Telefon</th><th>Maktab</th><th>MFY</th><th>Natija</th><th>Sana</th></tr>
    '''
    for r in rows:
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><b>{r[4]}</b>/{r[5]}</td><td>{r[6]}</td></tr>"
    html += "</table></body></html>"
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
