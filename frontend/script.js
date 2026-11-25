(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  const MAX_MB = 5;
  const MIN_JD = 100;
  const MIN_DETAIL = 15;
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$/;

  const state = {
    sessionId: null,
    file: null,
    questions: [],
    choices: [],
    isSafe: false,
    sending: false,
  };

  /* ---------- helpers ---------- */

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function toast(message, type = "info") {
    const t = el("div", `toast ${type}`, message);
    $("#toasts").appendChild(t);
    requestAnimationFrame(() => t.classList.add("show"));
    setTimeout(() => {
      t.classList.remove("show");
      setTimeout(() => t.remove(), 300);
    }, 4500);
  }

  let loaderTimer = null;
  function startLoader(title, messages) {
    const msg = $("#loader-msg");
    let i = 0;
    $("#loader-title").textContent = title;
    msg.textContent = messages[0];
    $("#loader").classList.add("show");
    clearInterval(loaderTimer);
    loaderTimer = setInterval(() => {
      i = (i + 1) % messages.length;
      msg.classList.add("swap");
      setTimeout(() => {
        msg.textContent = messages[i];
        msg.classList.remove("swap");
      }, 200);
    }, 2200);
  }
  function stopLoader() {
    clearInterval(loaderTimer);
    $("#loader").classList.remove("show");
  }

  async function api(url, options = {}) {
    let res;
    try {
      res = await fetch(url, options);
    } catch {
      throw new Error("Cannot reach the server. Is it running?");
    }
    let data = null;
    try {
      data = await res.json();
    } catch {
      /* response had no JSON body */
    }
    if (!res.ok) {
      const detail = data && (data.detail || data.message);
      throw new Error(typeof detail === "string" ? detail : "Something went wrong. Please try again.");
    }
    return data;
  }

  function goTo(step) {
    $$(".screen").forEach((s) => s.classList.toggle("active", s.id === `screen-${step}`));
    $$("#stepper li").forEach((li) => {
      const n = Number(li.dataset.step);
      li.classList.toggle("active", n === step);
      li.classList.toggle("done", n < step);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* ---------- cursor glow (desktop only) ---------- */

  const glow = $("#glow");
  if (glow) {
    if (window.matchMedia("(hover: hover)").matches) {
      window.addEventListener("pointermove", (e) => {
        glow.style.left = `${e.clientX}px`;
        glow.style.top = `${e.clientY}px`;
      });
    } else {
      glow.remove();
    }
  }

  /* ---------- screen 1: upload ---------- */

  const drop = $("#drop");
  const fileInput = $("#resume-input");

  function setFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return toast("Please upload a PDF file.", "error");
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      return toast(`The file is larger than ${MAX_MB} MB.`, "error");
    }
    state.file = file;
    drop.classList.add("has-file");
    $("#drop-title").textContent = file.name;
    $("#drop-sub").textContent = `${Math.max(1, Math.round(file.size / 1024))} KB. Click to replace.`;
  }

  fileInput.addEventListener("change", () => setFile(fileInput.files[0]));
  ["dragenter", "dragover"].forEach((evt) =>
    drop.addEventListener(evt, (e) => {
      e.preventDefault();
      drop.classList.add("drag");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    drop.addEventListener(evt, (e) => {
      e.preventDefault();
      drop.classList.remove("drag");
    })
  );
  drop.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));

  $("#jd").addEventListener("input", (e) => {
    $("#jd-count").textContent = `${e.target.value.length.toLocaleString()} characters`;
  });

  async function analyze() {
    if (!state.file) return toast("Please upload your resume (PDF).", "error");
    const jd = $("#jd").value.trim();
    if (jd.length < MIN_JD) return toast("Please paste the full job description.", "error");

    const form = new FormData();
    form.append("resume", state.file);
    form.append("jd", jd);

    startLoader("Analyzing your fit", [
      "Reading your resume...",
      "Understanding the job description...",
      "Comparing skills and keywords...",
      "Finding the gaps...",
    ]);
    try {
      const data = await api("/api/analyze", { method: "POST", body: form });
      state.sessionId = data.session_id;
      renderAnalysis(data);
      goTo(2);
    } catch (err) {
      toast(err.message, "error");
    } finally {
      stopLoader();
    }
  }

  /* ---------- screen 2: analysis ---------- */

  function animateScore(score) {
    const C = 2 * Math.PI * 52;
    const ring = $("#ring");
    ring.style.strokeDasharray = C;
    ring.style.strokeDashoffset = C;
    requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        ring.style.strokeDashoffset = C * (1 - score / 100);
      })
    );

    const num = $("#score-num");
    const start = performance.now();
    const duration = 1200;
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      num.textContent = Math.round(score * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function scoreMessage(score) {
    if (score >= 80) return "Strong match. A few small tweaks will make you stand out.";
    if (score >= 60) return "Good foundation. Closing the gaps below will lift your chances.";
    return "There are real gaps for this role. Answer honestly below, and the agent will highlight what you truly have.";
  }

  function fillChips(selector, items, kind, emptyText) {
    const box = $(selector);
    box.replaceChildren();
    if (!items || !items.length) {
      box.appendChild(el("span", "muted", emptyText));
      return;
    }
    items.forEach((t) => box.appendChild(el("span", `chip ${kind}`, t)));
  }

  function renderAnalysis(d) {
    const score = Math.max(0, Math.min(100, Number(d.match_score) || 0));
    animateScore(score);
    $("#score-text").textContent = scoreMessage(score);
    if (score < 40) {
      toast("This job looks very different from your resume. The agent can only highlight what you really have.", "error");
    }

    fillChips("#match-chips", d.matching_skills, "good", "No direct matches found.");
    fillChips("#missing-chips", d.missing_skills, "bad", "No gaps found. Great fit!");

    const improvements = d.sections_to_improve || [];
    const list = $("#improve-list");
    list.replaceChildren();
    improvements.forEach((t) => list.appendChild(el("li", "", t)));
    $("#improve-card").classList.toggle("hidden", improvements.length === 0);

    renderQuestions(d.questions || []);
  }

  function renderQuestions(questions) {
    state.questions = questions;
    state.choices = questions.map(() => ({ confirmed: false, detail: "" }));
    const wrap = $("#questions");
    wrap.replaceChildren();

    if (!questions.length) {
      wrap.appendChild(el("p", "muted", "No questions. The agent already has everything it needs."));
      return;
    }

    questions.forEach((q, i) => {
      const item = el("div", "q");
      const seg = el("div", "seg");
      const yes = el("button", "", "Yes, I have");
      const no = el("button", "on", "No");
      yes.type = "button";
      no.type = "button";

      const detail = el("div", "q-detail hidden");
      const ta = el("textarea");
      ta.rows = 2;
      ta.placeholder = "What exactly did you do? Tool or platform name, and where you used it.";
      detail.append(ta, el("small", "hint", `At least ${MIN_DETAIL} characters. Only what you actually did.`));

      const setChoice = (confirmed) => {
        state.choices[i].confirmed = confirmed;
        yes.classList.toggle("on", confirmed);
        no.classList.toggle("on", !confirmed);
        detail.classList.toggle("hidden", !confirmed);
        item.classList.remove("invalid");
        if (confirmed) ta.focus();
      };
      yes.addEventListener("click", () => setChoice(true));
      no.addEventListener("click", () => setChoice(false));
      ta.addEventListener("input", () => {
        state.choices[i].detail = ta.value;
        item.classList.remove("invalid");
      });

      seg.append(yes, no);
      item.append(el("p", "q-text", q), seg, detail);
      wrap.appendChild(item);
    });
  }

  function collectAnswers() {
    const items = $$("#questions .q");
    let firstBad = null;
    const answers = state.questions.map((q, i) => {
      const c = state.choices[i];
      const detail = c.detail.trim();
      if (c.confirmed && detail.length < MIN_DETAIL) {
        items[i].classList.add("invalid");
        firstBad = firstBad || items[i];
      }
      return { question: q, answer: c.confirmed ? detail : "", confirmed: c.confirmed };
    });
    return firstBad ? { bad: firstBad } : { answers };
  }

  async function generate() {
    const out = collectAnswers();
    if (out.bad) {
      out.bad.scrollIntoView({ behavior: "smooth", block: "center" });
      return toast(`Add details (at least ${MIN_DETAIL} characters) or choose "No".`, "error");
    }

    startLoader("Building your application", [
      "Tailoring your resume to the job...",
      "Fact-checking every claim...",
      "Writing your email...",
      "Creating the PDF...",
    ]);
    try {
      const data = await api("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: state.sessionId, answers: out.answers }),
      });
      renderPreview(data);
      goTo(3);
    } catch (err) {
      toast(err.message, "error");
    } finally {
      stopLoader();
    }
  }

  /* ---------- screen 3: review & send ---------- */

  function renderPreview(d) {
    state.isSafe = Boolean(d.is_safe);

    const badge = $("#fact-badge");
    badge.className = `badge ${state.isSafe ? "good" : "bad"}`;
    badge.textContent = state.isSafe ? "Fact-check passed" : "Fact-check failed";

    const issues = $("#fact-issues");
    issues.replaceChildren();
    issues.classList.toggle("hidden", state.isSafe);
    if (!state.isSafe) {
      issues.appendChild(el("strong", "", "Some claims are not backed by your resume, so sending is blocked."));
      const claims = d.unsupported_claims || [];
      if (claims.length) {
        const ul = el("ul");
        claims.forEach((c) => ul.appendChild(el("li", "", c)));
        issues.appendChild(ul);
      }
    }

    $("#pdf-frame").src = `${d.pdf_url}#toolbar=0&navpanes=0`;
    $("#pdf-open").href = d.pdf_url;
    $("#file-name").textContent = d.filename || "resume.pdf";
    $("#attach-name").textContent = d.filename || "resume.pdf";

    $("#to").value = d.to_email || "";
    $("#subject").value = d.subject || "";
    $("#body").value = d.body || "";
    $("#reviewed").checked = false;

    const found = $("#found");
    const emails = d.to_emails || [];
    found.replaceChildren();
    if (emails.length > 1) {
      emails.forEach((mail) => {
        const chip = el("button", "chip", mail);
        chip.type = "button";
        chip.addEventListener("click", () => {
          $("#to").value = mail;
              state.demo = Boolean(d.demo);
    if (state.demo) {
      $("#send-btn").textContent = "Sending disabled in demo";
      toast("Demo mode: you can preview and download the PDF, but emails are not sent.", "success");
    }
          updateSend();
        });
        found.appendChild(chip);
      });
    }

    const hint = $("#to-hint");
    hint.className = "hint";
    if (!emails.length) {
      hint.textContent = "No email address was found in the job description. Please enter the recipient.";
      hint.classList.add("warn");
    } else if (emails.length > 1) {
      hint.textContent = "Several email addresses were found in the job description. Pick one.";
    } else {
      hint.textContent = "Found in the job description.";
    }

    updateSend();
  }

  function updateSend() {
    const ok =
      state.isSafe &&
      EMAIL_RE.test($("#to").value.trim()) &&
      $("#subject").value.trim() !== "" &&
      $("#body").value.trim() !== "" &&
      $("#reviewed").checked;
    $("#send-btn").disabled = !ok || state.sending;
  }

  async function send() {
    if ($("#send-btn").disabled || state.sending) return;
    state.sending = true;
    updateSend();

    const payload = {
      session_id: state.sessionId,
      to_email: $("#to").value.trim(),
      subject: $("#subject").value.trim(),
      body: $("#body").value.trim(),
    };

    startLoader("Sending your application", [
      "Attaching your resume...",
      "Connecting to Gmail...",
      "Sending...",
    ]);
    try {
      await api("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      $("#sent-text").textContent = `Your resume and email were sent to ${payload.to_email}.`;
      goTo(4);
    } catch (err) {
      toast(err.message, "error");
    } finally {
      state.sending = false;
      stopLoader();
      updateSend();
      $("#send-btn").disabled = state.demo || !ok || state.sending;
    }
  }

  /* ---------- wiring ---------- */

  $("#analyze-btn").addEventListener("click", analyze);
  $("#generate-btn").addEventListener("click", generate);
  $("#send-btn").addEventListener("click", send);
  $("#back-1").addEventListener("click", () => goTo(1));
  $("#back-2").addEventListener("click", () => goTo(2));
  $("#restart-btn").addEventListener("click", () => window.location.reload());

  ["#to", "#subject", "#body"].forEach((sel) => $(sel).addEventListener("input", updateSend));
  $("#reviewed").addEventListener("change", updateSend);
})();