// main.js - interaction front/backend avec animations

const analyzeBtn = document.getElementById("analyzeBtn");
const cipherTextEl = document.getElementById("cipherText");
const langSelectEl = document.getElementById("langSelect");
const resultCipher = document.getElementById("result-cipher");
const resultKey = document.getElementById("result-key");
const resultPlain = document.getElementById("result-plain");
const resultScore = document.getElementById("result-score");

function setResultValues(cipher, key, plain, score, color) {
  if (resultCipher) {
    resultCipher.textContent = cipher;
    resultCipher.style.color = color;
  }
  if (resultKey) {
    resultKey.textContent = key;
    resultKey.style.color = color;
  }
  if (resultPlain) {
    resultPlain.textContent = plain;
    resultPlain.style.color = color;
  }
  if (resultScore) {
    resultScore.textContent = score;
    resultScore.style.color = color;
  }
}

function renderTopCandidates(candidates) {
  const listEl = document.getElementById("top-list");
  if (!listEl) return;
  listEl.innerHTML = "";
  if (!candidates || candidates.length === 0) {
    const li = document.createElement("li");
    li.className = "list-group-item bg-transparent text-white";
    li.textContent = "—";
    listEl.appendChild(li);
    return;
  }

  // Ensure candidates are sorted by score (desc) before displaying
  const sortedCandidates = [...candidates].sort((a, b) => {
    const scoreA =
      typeof a.score === "number" ? a.score : parseFloat(a.score) || 0;
    const scoreB =
      typeof b.score === "number" ? b.score : parseFloat(b.score) || 0;
    return scoreB - scoreA;
  });

  sortedCandidates.slice(0, 5).forEach((c, idx) => {
    const li = document.createElement("li");
    li.className =
      "list-group-item bg-transparent text-white d-flex justify-content-between align-items-start";

    const left = document.createElement("div");
    left.className = "ms-2 me-auto";
    const title = document.createElement("div");
    title.className = "fw-bold";
    title.textContent = `${idx + 1}. ${
      c.plaintext || c.plain || c.plainText || "—"
    }`;
    const meta = document.createElement("small");
    const keyText =
      c.key !== null && c.key !== undefined ? `clé ${c.key}` : "—";

    // Ensure score is a number and format it
    let scoreValue = 0;
    if (typeof c.score === "number") {
      scoreValue = c.score;
    } else if (c.score !== null && c.score !== undefined) {
      scoreValue = parseFloat(c.score) || 0;
    }

    // Format score with appropriate precision
    let scorePct;
    if (scoreValue === 0) {
      scorePct = "0.0%";
    } else if (scoreValue < 0.01) {
      // For very small scores, show more decimal places
      scorePct = (scoreValue * 100).toFixed(3) + "%";
    } else {
      scorePct = (scoreValue * 100).toFixed(1) + "%";
    }
    meta.textContent = `${keyText} • Score: ${scorePct}`;

    left.appendChild(title);
    left.appendChild(meta);

    li.appendChild(left);
    listEl.appendChild(li);
  });
}

if (analyzeBtn) {
  analyzeBtn.addEventListener("click", async () => {
    const text = cipherTextEl.value.trim();

    setResultValues("Analyse en cours...", "—", "—", "—", "#00ccff");

    if (!text) {
      setResultValues(
        "Veuillez entrer un texte chiffré !",
        "—",
        "—",
        "—",
        "red"
      );
      return;
    }

    const lang = langSelectEl ? langSelectEl.value || "auto" : "auto";

    // Try server-side scoring first
    try {
      const resp = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cipherText: text, lang }),
      });

      const body = await resp.text();
      let data = null;
      try {
        data = JSON.parse(body);
      } catch (e) {
        data = null;
      }

      if (!resp.ok) {
        const msg = data && data.error ? data.error : body || "Erreur serveur";
        throw new Error(msg);
      }

      // Ensure candidates are sorted by score (desc) before displaying
      if (Array.isArray(data.candidates)) {
        // Sort by score (highest first), ensuring scores are numbers
        data.candidates.sort((a, b) => {
          const scoreA =
            typeof a.score === "number" ? a.score : parseFloat(a.score) || 0;
          const scoreB =
            typeof b.score === "number" ? b.score : parseFloat(b.score) || 0;
          return scoreB - scoreA;
        });

        // Ensure all candidates have valid scores
        data.candidates.forEach((c) => {
          if (typeof c.score !== "number") {
            c.score = parseFloat(c.score) || 0;
          }
        });
      }

      // show only best plaintext from server
      let bestScore =
        typeof data.score === "number"
          ? data.score
          : parseFloat(data.score) || 0;

      // Ensure score is never 0 for display
      if (bestScore <= 0) {
        bestScore = 0.0001;
      }

      // Format score with appropriate precision
      let scoreDisplay;
      if (bestScore < 0.01) {
        scoreDisplay = (bestScore * 100).toFixed(3) + "%";
      } else {
        scoreDisplay = (bestScore * 100).toFixed(1) + "%";
      }

      setResultValues(
        data.cipher || text,
        data.key !== null && data.key !== undefined ? `clé ${data.key}` : "—",
        data.plainText || "—",
        scoreDisplay,
        "#00ffe5"
      );

      // Render top 5 candidates (already sorted)
      if (Array.isArray(data.candidates) && data.candidates.length > 0) {
        renderTopCandidates(data.candidates.slice(0, 5));
      } else {
        renderTopCandidates([]);
      }
      return; // done
    } catch (err) {
      // server failed — fall back to client-side brute force
      console.warn(
        "Server analyze failed, falling back to client-side:",
        err.message
      );
    }

    // Client-side fallback: brute-force and score with a simple heuristic
    try {
      function caesarShift(input, k) {
        // Support multiple alphabets: Latin, Cyrillic, Greek, Arabic
        return input.replace(/[\u0000-\uFFFF]/g, (c) => {
          let base, size;

          // Latin A-Z
          if (c >= "A" && c <= "Z") {
            base = 65;
            size = 26;
          }
          // Latin a-z
          else if (c >= "a" && c <= "z") {
            base = 97;
            size = 26;
          }
          // Cyrillic А-Я
          else if (c >= "А" && c <= "Я") {
            base = 1040;
            size = 32;
          }
          // Cyrillic а-я
          else if (c >= "а" && c <= "я") {
            base = 1072;
            size = 32;
          }
          // Greek Α-Ω
          else if (c >= "Α" && c <= "Ω") {
            base = 913;
            size = 24;
          }
          // Greek α-ω
          else if (c >= "α" && c <= "ω") {
            base = 945;
            size = 24;
          }
          // Arabic ا-ي
          else if (c >= "ا" && c <= "ي") {
            base = 1575;
            size = 28;
          } else {
            return c; // Keep non-alphabetic characters
          }

          const code = c.charCodeAt(0) - base;
          const shifted = (code - k + size) % size;
          return String.fromCharCode(shifted + base);
        });
      }

      const common = {
        en: [
          "the",
          "and",
          "is",
          "to",
          "of",
          "you",
          "hello",
          "that",
          "in",
          "it",
          "dog",
          "cat",
        ],
        fr: [
          "le",
          "la",
          "et",
          "de",
          "un",
          "bonjour",
          "je",
          "tu",
          "il",
          "elle",
          "nous",
          "vous",
        ],
      };

      function scoreCandidate(text) {
        // Support Unicode word splitting for any language
        const words = text
          .toLowerCase()
          .split(/[\s\W]+/)
          .filter(Boolean);
        if (words.length === 0) return 0;
        let matches = 0;
        const list = common[lang] || common.en || [];
        for (const w of words) if (list.includes(w)) matches++;
        return matches / words.length;
      }

      const candidates = [];
      for (let k = 0; k < 26; k++) {
        const plain = caesarShift(text, k);
        const score = scoreCandidate(plain);
        candidates.push({ key: k, plain, score });
      }

      // Sort by score (highest first)
      candidates.sort((a, b) => {
        const scoreA =
          typeof a.score === "number" ? a.score : parseFloat(a.score) || 0;
        const scoreB =
          typeof b.score === "number" ? b.score : parseFloat(b.score) || 0;
        return scoreB - scoreA;
      });

      const best = candidates[0] || { key: null, plain: text, score: 0 };
      const bestScore =
        typeof best.score === "number"
          ? best.score
          : parseFloat(best.score) || 0;

      setResultValues(
        text,
        best.key !== null ? `clé ${best.key}` : "—",
        best.plain || "—",
        (bestScore * 100).toFixed(1) + "%",
        "#00ffe5"
      );

      // render the top 5 from client fallback (already sorted)
      const formatted = candidates.slice(0, 5).map((c) => ({
        key: c.key,
        plaintext: c.plain,
        score: typeof c.score === "number" ? c.score : parseFloat(c.score) || 0,
      }));
      renderTopCandidates(formatted);
    } catch (err) {
      setResultValues(`Erreur: ${err.message}`, "—", "—", "—", "red");
    }
  });
}
