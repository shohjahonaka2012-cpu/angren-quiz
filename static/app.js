// Misol uchun ma'lumotlarni yuborish funksiyasi:
function sendResultsToServer(userName, phone, school, mfy, score, total) {
    fetch('/api/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_name: userName,
            phone: phone,
            school: school,
            mfy: mfy,
            score: score,
            total: total
        })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'ok') {
            console.log("Saqlandi!");
        } else {
            alert("Xatolik: " + data.message);
        }
    })
    .catch(error => {
        console.error("Aloqa xatosi:", error);
        alert("Aloqa xatosi. Qayta urinib ko'ring.");
    });
}
