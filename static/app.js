
let questions = [];
let currentIndex = 0;
let userAnswers = [];

async function startQuiz() {
  const response = await fetch("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });

  const data = await response.json();

  questions = data.questions;
  currentIndex = 0;
  userAnswers = [];

  showQuestion();
}

function showQuestion() {
  const q = questions[currentIndex];

  document.getElementById("question").textContent = q.question;

  const options = document.getElementById("options");
  options.innerHTML = "";

  q.options.forEach((option, index) => {
    const button = document.createElement("button");
    button.textContent = option;

    button.onclick = () => {
      userAnswers.push({
        question_id: q.id,
        answer: index
      });

      currentIndex++;

      if (currentIndex < questions.length) {
        showQuestion();
      } else {
        finishQuiz();
      }
    };

    options.appendChild(button);
  });
}

async function finishQuiz() {
  const response = await fetch("/api/finish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers: userAnswers })
  });

  const result = await response.json();

  document.getElementById("question").textContent =
    "Viktorina yakunlandi!";

  document.getElementById("options").innerHTML =
    `Sizning natijangiz: ${result.score} / ${result.total}`;
}

