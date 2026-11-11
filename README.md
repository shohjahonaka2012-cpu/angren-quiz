# Davlat bayrogʻi viktorinasi · Angren (Python / Flask)

Ikki tilli (UZ/RU) viktorina sayti. Backend: Flask + SQLite. Oldingi dizayn bilan bir xil.

## Tuzilishi
- `app.py` — server, API va admin panel
- `questions.py` — savollar va toʻgʻri javoblar (faqat serverda, brauzerga yuborilmaydi)
- `static/` — sayt (index.html, app.js, style.css); faktlar `app.js` ichida `F:` boʻlimida
- `templates/admin.html` — admin panel
- `data/quiz.db` — maʼlumotlar bazasi (avtomatik yaratiladi)

## Lokal ishga tushirish
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
export ADMIN_PASSWORD="kuchli-parol"              # Windows: set ADMIN_PASSWORD=...
python app.py                                      # http://localhost:8000
```
Admin panel: `/admin` (login: `ADMIN_USER`, standart `admin`). `ADMIN_PASSWORD` berilmasa admin oʻchiq turadi.

## Serverga (production)
```bash
gunicorn -w 2 -b 127.0.0.1:8000 app:app
```
Nginx yoki Caddy orqali HTTPS bilan ulang va `TRUST_PROXY=1` qoʻying. Yoki Docker:
```bash
docker build -t bayroq . && docker run -d -p 8000:8000 -v bayroq-data:/data -e ADMIN_PASSWORD=... bayroq
```

## Muhim
- Har bir telefon raqami bir marta qatnashadi (`ONE_ATTEMPT_PER_PHONE=0` — cheklovsiz).
- Ball serverda hisoblanadi: toʻgʻri javoblar brauzerga oldindan yuborilmaydi.
- Ommaviy jadvalda faqat "Ali V." koʻrinishidagi ism va maktab chiqadi; telefon va MFY faqat adminda.
- Maʼlumotlar bazasini (`data/quiz.db`) muntazam zaxiralang.
- Oʻquvchilarning koʻpchiligi voyaga yetmagan: telefon raqamini yigʻishdan oldin ota-ona/maktab roziligi va maxfiylik matnini tayyorlang.
- Savol qoʻshish: `questions.py` ga yangi band qoʻshing (ikkala tilda), jami son avtomatik hisoblanadi.
