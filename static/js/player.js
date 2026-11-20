(function () {
  const config = window.RAGA_CONFIG;
  if (!config) return;

  const audio = document.getElementById("ragaAudio");
  const timer = document.getElementById("timer");
  const bar = document.getElementById("listenProgress");
  const status = document.getElementById("unlockStatus");
  const formLock = document.getElementById("formLock");
  const submit = document.getElementById("submitRatings");

  let total = Number(config.initialSeconds || 0);
  let pending = 0;
  let lastTick = Date.now();

  function display() {
    const mins = Math.floor(total / 60);
    const secs = String(total % 60).padStart(2, "0");
    if (timer) timer.textContent = `${mins}:${secs}`;
    if (bar) bar.style.width = `${Math.min(100, total / 60 * 100)}%`;
    if (total >= 60) {
      if (status) { status.textContent = "Unlocked"; status.classList.add("done"); }
      if (formLock) { formLock.textContent = "Available"; formLock.classList.add("done"); }
      if (submit) submit.disabled = false;
    }
  }

  async function saveProgress(amount) {
    if (amount <= 0) return;
    try {
      const response = await fetch(config.progressUrl, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({raga_id: config.ragaId, seconds: amount})
      });
      const data = await response.json();
      if (data.ok) {
        total = Math.max(total, Number(data.total));
        display();
      }
    } catch (error) {
      console.error("Could not save listening progress", error);
    }
  }

  if (audio) {
    audio.addEventListener("play", () => { lastTick = Date.now(); });
    audio.addEventListener("pause", () => { saveProgress(pending); pending = 0; });
    audio.addEventListener("ended", () => { saveProgress(pending); pending = 0; });
    setInterval(() => {
      if (!audio.paused && !audio.ended) {
        const now = Date.now();
        const elapsed = Math.max(0, Math.min(2, Math.floor((now - lastTick) / 1000)));
        lastTick = now;
        if (elapsed > 0) {
          total += elapsed;
          pending += elapsed;
          display();
          if (pending >= 5) {
            const amount = pending;
            pending = 0;
            saveProgress(amount);
          }
        }
      } else {
        lastTick = Date.now();
      }
    }, 1000);
    window.addEventListener("beforeunload", () => {
      if (pending > 0) {
        const data = new Blob([JSON.stringify({raga_id: config.ragaId, seconds: Math.min(pending, 10)})],
                              {type: "application/json"});
        navigator.sendBeacon(config.progressUrl, data);
      }
    });
  }
  display();
})();
