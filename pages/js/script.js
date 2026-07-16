// ---------- copy install command ----------
function wireCopyButton(btn) {
  if (!btn) return;
  btn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText("pip install betterqr");
    } catch (e) {
      // Fallback for environments without clipboard permission
      const ta = document.createElement("textarea");
      ta.value = "pip install betterqr";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    const original = btn.innerHTML;
    btn.innerHTML = "&#10003;";
    btn.style.color = "#8CE8D0";
    setTimeout(() => {
      btn.innerHTML = original;
      btn.style.color = "";
    }, 1600);
  });
}
wireCopyButton(document.getElementById("copyInstall"));
wireCopyButton(document.getElementById("copyInstall2"));

// ---------- code tabs ----------
document.querySelectorAll(".code-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    document.querySelectorAll(".code-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".code-block").forEach((b) => b.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`tab-${target}`).classList.add("active");
  });
});

// ---------- scroll reveal ----------
const revealEls = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window && revealEls.length) {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  revealEls.forEach((el) => io.observe(el));
  // Safety net: never leave content invisible if something goes wrong above.
  setTimeout(() => revealEls.forEach((el) => el.classList.add("in")), 3000);
} else {
  revealEls.forEach((el) => el.classList.add("in"));
}
