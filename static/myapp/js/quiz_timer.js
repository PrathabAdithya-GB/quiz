document.addEventListener("DOMContentLoaded", function () {
    const timerEl = document.getElementById("timer");
    const form = document.getElementById("quizForm");

    if (!timerEl || !form) return;

    let timeLeft = parseInt(timerEl.dataset.minutes) * 60;

    function update() {
        const m = Math.floor(timeLeft / 60);
        const s = timeLeft % 60;
        timerEl.textContent = `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    }

    update();

    const interval = setInterval(() => {
        timeLeft--;
        update();

        if (timeLeft <= 0) {
            clearInterval(interval);
            alert("⏰ Time up! Submitting quiz.");
            form.submit();
        }
    }, 1000);
});
