/* FurrOS · Lapa's School — renderer, progress, quizzes, bridge to the real system. */
(() => {
  const params = new URLSearchParams(location.search);
  const ASSETS = params.get("assets") || "file:///usr/share/furros";
  const DE = (params.get("de") || "kde").toLowerCase();
  const MODE = params.get("mode") || "";
  const STORE = "furros-academy-v1";
  const LANGS = ["ru", "en", "pl", "es"];

  let state = load();
  if (!["lapa", "pixie", "danyok"].includes(state.level)) state.level = "lapa";
  let lang = params.get("lang") || state.lang || (navigator.language || "ru").slice(0, 2);
  if (!LANGS.includes(lang)) lang = "en";
  let bridge = null;

  const $ = (sel, root = document) => root.querySelector(sel);
  const el = (tag, attrs = {}, html) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") e.className = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    if (html !== undefined) e.innerHTML = html;
    return e;
  };
  const C = () => window.CONTENT[lang];
  const QUICK = [
    ["⟳", "update", { cmd: "furros-update" }],
    ["🎮", "drivers", { cmd: "furros-drivers" }],
    ["⏪", "snapshots", { cmd: "btrfs-assistant-launcher" }],
    ["🛡", "firewall", { cmd: "sudo ufw status verbose" }],
    ["💬", "discord", { url: "https://discord.gg/ZA3GuBYKwG" }],
    ["✈", "telegram", { url: "https://t.me/FurrOS_Linux" }],
  ];
  const U = (k, ...a) => (C().ui[k] || k).replace(/\{(\d)\}/g, (_, i) => a[i]);
  const lapaImg = (mood) => `${ASSETS}/lapa/lapa-${mood || "hoodie"}-small.png`;
  // three teachers, harder each time: Lapa (the basics), Pixie (a confident user), Danyok (the system inside out)
  const LEVELS = ["lapa", "pixie", "danyok"];
  // Pixie and Danyok have two arts each: calm moods (hoodie, timer, lying) show the second one
  const CALM = ["hoodie", "timer", "lying"];
  const teacherImg = (lv, mood) => (lv === "pixie" ? (CALM.includes(mood) ? "img/pixie-lying.png" : "img/pixie.png")
    : lv === "danyok" ? (CALM.includes(mood) ? "img/danyok-sketch.png" : "img/danyok.png") : lapaImg(mood));
  const chaptersOf = (lv) => (lv === "lapa" ? C().chapters : ((C().levels || {})[lv] || { chapters: [] }).chapters);
  const levelOf = (id) => LEVELS.find((lv) => chaptersOf(lv).some((c) => c.id === id)) || "lapa";
  const levelDone = (lv) => chaptersOf(lv).filter((c) => state.done[c.id]).length;

  function load() {
    try { return JSON.parse(localStorage.getItem(STORE)) || { done: {}, quiz: {} }; }
    catch (e) { return { done: {}, quiz: {} }; }
  }
  function save() {
    try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) { /* private mode */ }
    // a copy for Lapa in the tray: achievements count finished chapters
    if (bridge && bridge.saveProgress) bridge.saveProgress(JSON.stringify(state));
  }

  function toast(text) {
    const t = $("#toast");
    t.textContent = text;
    t.classList.add("show");
    clearTimeout(toast.h);
    toast.h = setTimeout(() => t.classList.remove("show"), 2200);
  }

  async function copy(text) {
    if (bridge) bridge.copy(text);
    else {
      try { await navigator.clipboard.writeText(text); }
      catch (e) {
        const ta = el("textarea"); ta.value = text; document.body.append(ta); ta.select();
        document.execCommand("copy"); ta.remove();
      }
    }
    toast(U("copied"));
  }

  function runInTerminal(cmd) {
    if (bridge) { bridge.runInTerminal(cmd); toast(U("opened")); }
    else { copy(cmd); }
  }

  // ---------------------------------------------------------------- blocks
  function block(b) {
    if (b.p) return el("p", {}, b.p);
    if (b.h) return el("h3", {}, b.h);
    if (b.ul) { const u = el("ul"); b.ul.forEach((i) => u.append(el("li", {}, i))); return u; }
    if (b.ol) { const u = el("ol"); b.ol.forEach((i) => u.append(el("li", {}, i))); return u; }
    if (b.warn) return el("div", { class: "card warn" }, b.warn);
    if (b.tip) return el("div", { class: "card tip" }, "💡 " + b.tip);
    if (b.lapa || b.say) {
      const lv = b.lapa ? "lapa" : state.level;
      const d = el("div", { class: "lapa" });
      d.append(el("img", { src: teacherImg(lv, b.mood), alt: "" }));
      const bub = el("div", { class: "bubble" });
      bub.append(el("div", { class: "who" }, lv === "lapa" ? U("lapaSays") : U("says_" + lv)));
      bub.append(el("div", {}, b.lapa || b.say));
      d.append(bub);
      return d;
    }
    if (b.cmd) {
      const frag = document.createDocumentFragment();
      const box = el("div", { class: "cmd" });
      box.append(el("pre", {}, escapeHtml(b.cmd)));
      const act = el("div", { class: "actions" });
      act.append(el("button", { onclick: () => copy(b.cmd), "aria-label": U("copy") + ": " + b.cmd }, U("copy")));
      if (!b.noRun) act.append(el("button", { onclick: () => runInTerminal(b.cmd) }, U("tryTerm")));
      box.append(act);
      frag.append(box);
      if (b.note) frag.append(el("div", { class: "cmd-note" }, b.note));
      return frag;
    }
    if (b.table) {
      const t = el("table");
      const tr = el("tr");
      b.table.head.forEach((h) => tr.append(el("th", {}, h)));
      t.append(tr);
      b.table.rows.forEach((r) => {
        const row = el("tr");
        r.forEach((c) => row.append(el("td", {}, c)));
        t.append(row);
      });
      return t;
    }
    if (b.keys) return keysTable(DE);
    if (b.terminal) return window.FurrTerminal.create(b.terminal, C(), (msg) => toast(msg));
    if (b.img) {
      const f = el("figure", { class: "card" });
      f.append(el("img", { src: `${ASSETS}/${b.img}`, alt: b.cap || "", style: "max-width:100%;border-radius:12px" }));
      if (b.cap) f.append(el("figcaption", { class: "dim" }, b.cap));
      return f;
    }
    return el("div");
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  function keysTable(de) {
    const k = window.FURROS_KEYS[de] || window.FURROS_KEYS.kde;
    const t = el("table");
    const tr = el("tr");
    tr.append(el("th", {}, U("keyCombo")), el("th", {}, U("keyAction")));
    t.append(tr);
    k.keys.forEach(([combo, id]) => {
      const row = el("tr");
      row.append(el("td", {}, combo.split(" ").map((p) => (p === "+" ? " + " : `<kbd>${p}</kbd>`)).join("")));
      row.append(el("td", {}, C().keydesc[id] || id));
      t.append(row);
    });
    return t;
  }

  // ---------------------------------------------------------------- views
  function sidebar(activeId) {
    $("#t-school").textContent = U("school");
    $("#t-sub").textContent = U("sub");
    $("#brand-logo").src = `${ASSETS}/furros-logo.png`;
    $("#lang").value = lang;
    const nav = $("#chapters");
    nav.innerHTML = "";
    const home = el("button", { class: "ch" + (activeId === "home" ? " active" : ""), onclick: () => go("home") });
    home.append(el("span", { class: "num" }, "🏠"), el("span", {}, U("home")));
    nav.append(home);
    const lvRow = el("div", { class: "levels-switch", role: "tablist", "aria-label": U("levelsTitle") });
    LEVELS.forEach((lv, i) => {
      const b = el("button", { class: "lvl" + (lv === state.level ? " active" : ""), role: "tab",
        "aria-selected": String(lv === state.level), title: U("lvl_" + lv), onclick: () => go("level-" + lv) });
      b.append(el("img", { src: teacherImg(lv, "wave"), alt: "" }), el("span", {}, String(i + 1)));
      lvRow.append(b);
    });
    nav.append(lvRow);
    const lvHead = el("button", { class: "ch" + (activeId === "level-" + state.level ? " active" : ""),
      onclick: () => go("level-" + state.level) });
    lvHead.append(el("span", { class: "num" }, "★"), el("span", {}, U("lvl_" + state.level)));
    nav.append(lvHead);
    chaptersOf(state.level).forEach((ch, i) => {
      const b = el("button", {
        class: "ch" + (ch.id === activeId ? " active" : "") + (state.done[ch.id] ? " done" : ""),
        onclick: () => go(ch.id), "aria-current": ch.id === activeId ? "page" : "false",
      });
      b.append(el("span", { class: "num" }, state.done[ch.id] ? "✓" : String(i + 1)), el("span", {}, ch.title));
      nav.append(b);
    });
    const keys = el("button", { class: "ch" + (activeId === "keys" ? " active" : ""), onclick: () => go("keys") });
    keys.append(el("span", { class: "num" }, "⌨"), el("span", {}, U("keysTitle")));
    nav.append(keys);
    const total = chaptersOf(state.level).length;
    const done = levelDone(state.level);
    $("#overall-fill").style.width = `${(done / total) * 100}%`;
    $("#overall-text").textContent = U("progress", done, total);
  }

  function viewHome() {
    const w = el("div", { class: "wrap" });
    const hero = el("div", { class: "hero" });
    const left = el("div");
    left.append(el("div", { class: "crumbs" }, "FurrOS · " + U("school")));
    left.append(el("h1", {}, U("homeTitle")));
    left.append(el("p", {}, U("homeIntro")));
    const next = chaptersOf(state.level).find((c) => !state.done[c.id])
      || LEVELS.map((lv) => chaptersOf(lv).find((c) => !state.done[c.id])).find(Boolean);
    const row = el("div", { class: "navrow", style: "justify-content:flex-start;margin-top:18px" });
    if (next) row.append(el("button", { class: "btn primary", onclick: () => go(next.id) },
      (Object.keys(state.done).length ? U("continue") : U("start")) + " →"));
    else row.append(el("button", { class: "btn primary", onclick: () => go("diploma") }, U("diplomaBtn") + " 🎓"));
    row.append(el("button", { class: "btn", onclick: () => go("keys") }, "⌨ " + U("keysTitle")));
    left.append(row);
    hero.append(left, el("img", { src: lapaImg("wave"), alt: "" }));
    w.append(hero);

    // quick start: the things a new user wants on day one, one click each
    w.append(el("h2", {}, U("quickTitle")));
    const qg = el("div", { class: "grid quick" });
    QUICK.forEach(([icon, key, act]) => {
      const c = el(act.url ? "a" : "div", { class: "card chapter-card quick-card", tabindex: "0", role: "button" });
      if (act.url) c.setAttribute("href", act.url);
      else {
        const fire = () => runInTerminal(act.cmd);
        c.addEventListener("click", fire);
        c.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") fire(); });
      }
      c.append(el("div", { class: "n" }, icon));
      c.append(el("h3", {}, U("q_" + key)));
      c.append(el("div", { class: "dim" }, U("q_" + key + "_d")));
      if (act.cmd) c.append(el("code", {}, act.cmd));
      qg.append(c);
    });
    w.append(qg);

    w.append(el("h2", {}, U("levelsTitle")));
    w.append(el("p", { class: "dim" }, U("levelsIntro")));
    const lg = el("div", { class: "grid levels" });
    LEVELS.forEach((lv, i) => {
      const total = chaptersOf(lv).length;
      const c = el("div", { class: "card chapter-card level-card", tabindex: "0", role: "button",
        onclick: () => go("level-" + lv), onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") go("level-" + lv); } });
      c.append(el("img", { src: teacherImg(lv, "wave"), alt: "" }));
      const t = el("div");
      t.append(el("div", { class: "n" }, `${U("level")} ${i + 1} · ${U("diff_" + lv)}`));
      t.append(el("h3", {}, U("lvl_" + lv)));
      t.append(el("div", { class: "dim" }, U("lvlIntro_" + lv)));
      const bar = el("div", { class: "bar", style: "margin-top:10px" });
      bar.append(el("div", { style: `width:${total ? (levelDone(lv) / total) * 100 : 0}%` }));
      t.append(bar, el("div", { class: "dim" }, U("progress", levelDone(lv), total)));
      c.append(t);
      lg.append(c);
    });
    w.append(lg);
    w.append(el("div", { class: "navrow" }, ""));
    const reset = el("button", { class: "btn", onclick: () => {
      if (confirmReset()) { state = { done: {}, quiz: {}, lang, level: "lapa" }; save(); go("home"); }
    } }, "↺ " + U("reset"));
    w.lastChild.append(reset);
    return w;
  }

  // a teacher's own page: who teaches, the bones of this level and its chapters
  function viewLevel(lv) {
    const chs = chaptersOf(lv);
    const n = LEVELS.indexOf(lv);
    const w = el("div", { class: "wrap" });
    const hero = el("div", { class: "hero" });
    const left = el("div");
    left.append(el("div", { class: "crumbs" }, `${U("level")} ${n + 1} · ${U("diff_" + lv)}`));
    left.append(el("h1", {}, U("lvlHello_" + lv)));
    left.append(el("p", {}, U("lvlText_" + lv)));
    if (n > 0 && levelDone(LEVELS[n - 1]) < chaptersOf(LEVELS[n - 1]).length)
      left.append(el("div", { class: "card tip" }, "💡 " + U("lvlFirst", U("lvl_" + LEVELS[n - 1]))));
    const next = chs.find((c) => !state.done[c.id]);
    const row = el("div", { class: "navrow", style: "justify-content:flex-start;margin-top:18px" });
    if (next) row.append(el("button", { class: "btn primary", onclick: () => go(next.id) },
      (levelDone(lv) ? U("continue") : U("start")) + " →"));
    else row.append(el("button", { class: "btn primary", onclick: () => go("diploma") }, U("diplomaBtn") + " 🎓"));
    left.append(row);
    hero.append(left, el("img", { src: teacherImg(lv, "wave"), alt: "" }));
    w.append(hero);

    w.append(el("h2", {}, U("badges")));
    const bd = el("div", { class: "badges" });
    chs.forEach((ch) => bd.append(el("span", { class: "badge" + (state.done[ch.id] ? " got" : ""),
      title: ch.title }, ch.badge)));
    w.append(bd);

    w.append(el("h2", {}, U("chaptersTitle")));
    const g = el("div", { class: "grid" });
    chs.forEach((ch, i) => {
      const c = el("div", { class: "card chapter-card", tabindex: "0", role: "button", onclick: () => go(ch.id),
        onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") go(ch.id); } });
      c.append(el("div", { class: "n" }, `${U("chapter")} ${i + 1}${state.done[ch.id] ? " · ✓" : ""}`));
      c.append(el("h3", {}, ch.title));
      c.append(el("div", { class: "dim" }, ch.intro));
      g.append(c);
    });
    w.append(g);
    return w;
  }

  function confirmReset() {
    // no blocking dialogs: second click within 3s confirms
    const now = Date.now();
    if (confirmReset.t && now - confirmReset.t < 3000) return true;
    confirmReset.t = now;
    toast(U("resetConfirm"));
    return false;
  }

  function viewChapter(id) {
    const lv = levelOf(id);
    const chs = chaptersOf(lv);
    const i = chs.findIndex((c) => c.id === id);
    const ch = chs[i];
    const w = el("div", { class: "wrap" });
    const hero = el("div", { class: "hero" });
    const left = el("div");
    left.append(el("div", { class: "crumbs" }, `${U("lvl_" + lv)} · ${U("chapter")} ${i + 1} / ${chs.length}`));
    left.append(el("h1", {}, ch.title));
    left.append(el("p", { class: "dim", style: "font-size:17px" }, ch.intro));
    hero.append(left, el("img", { src: teacherImg(lv, ch.mood), alt: "" }));
    w.append(hero);

    ch.lessons.forEach((ls) => {
      w.append(el("h2", {}, ls.title));
      ls.blocks.forEach((b) => w.append(block(b)));
    });

    if (ch.quiz && ch.quiz.length) w.append(quiz(ch));

    const nav = el("div", { class: "navrow" });
    nav.append(el("button", { class: "btn", onclick: () => go(i > 0 ? chs[i - 1].id : "level-" + lv) }, "← " + U("prev")));
    const nextId = i < chs.length - 1 ? chs[i + 1].id : "diploma";
    const nextBtn = el("button", { class: "btn primary", onclick: () => {
      if (!ch.quiz || !ch.quiz.length) markDone(ch);
      go(nextId);
    } }, U("next") + " →");
    nav.append(nextBtn);
    w.append(nav);
    return w;
  }

  function markDone(ch) {
    if (!state.done[ch.id]) {
      state.done[ch.id] = true;
      save();
      toast(U("chapterDone", ch.badge));
      sidebar(ch.id);
    }
  }

  function quiz(ch) {
    const box = el("div", { class: "card quiz" });
    box.append(el("h2", { style: "margin-top:0" }, "🦴 " + U("quiz")));
    box.append(el("p", { class: "dim" }, U("quizIntro")));
    const answered = state.quiz[ch.id] || {};
    const check = () => {
      if (ch.quiz.every((_, qi) => answered[qi] === true)) markDone(ch);
    };
    ch.quiz.forEach((q, qi) => {
      box.append(el("div", { class: "q" }, `${qi + 1}. ${q.q}`));
      const opts = [];
      const explain = el("div", { class: "explain", "aria-live": "polite" });
      // answers in a fixed but mixed order (seeded by chapter and question), so the right one isn't always first
      let seed = 0;
      for (const c of ch.id + qi) seed = (seed * 31 + c.charCodeAt(0)) >>> 0;
      const order = q.a.map((_, i) => i);
      for (let k = order.length - 1; k > 0; k--) {
        seed = (Math.imul(seed, 1103515245) + 12345) >>> 0;
        const j = seed % (k + 1);
        [order[k], order[j]] = [order[j], order[k]];
      }
      order.forEach((ai) => {
        const a = q.a[ai];
        const o = el("button", { class: "opt" }, a);
        if (answered[qi] === true && ai === q.ok) o.classList.add("right");
        o.addEventListener("click", () => {
          if (ai === q.ok) {
            opts.forEach((x) => x.classList.remove("wrong"));
            o.classList.add("right");
            explain.innerHTML = "✓ " + U("correct") + " " + (q.why || "");
            answered[qi] = true;
          } else {
            o.classList.add("wrong");
            explain.innerHTML = "✕ " + U("wrong");
            answered[qi] = answered[qi] === true;
          }
          state.quiz[ch.id] = answered;
          save();
          check();
        });
        opts.push(o);
        box.append(o);
      });
      if (answered[qi] === true) explain.innerHTML = "✓ " + (q.why || "");
      box.append(explain);
    });
    return box;
  }

  function viewKeys() {
    const w = el("div", { class: "wrap" });
    const hero = el("div", { class: "hero" });
    const left = el("div");
    left.append(el("div", { class: "crumbs" }, "FurrOS"));
    left.append(el("h1", {}, U("keysTitle")));
    left.append(el("p", {}, U("keysIntro")));
    hero.append(left, el("img", { src: lapaImg("timer"), alt: "" }));
    w.append(hero);
    const mine = window.FURROS_KEYS[DE];
    if (mine) {
      w.append(el("h2", {}, `${U("yourDesktop")}: ${mine.name}`));
      w.append(keysTable(DE));
    }
    w.append(el("h2", {}, U("everywhere")));
    w.append(keysTable("common"));
    w.append(el("h2", {}, U("otherDesktops")));
    const sel = el("select", { "aria-label": U("otherDesktops"), style: "max-width:320px" });
    Object.entries(window.FURROS_KEYS).filter(([k]) => k !== "common").forEach(([k, v]) => {
      const o = el("option", { value: k }, v.name);
      if (k === DE) o.selected = true;
      sel.append(o);
    });
    const holder = el("div");
    holder.append(keysTable(sel.value));
    sel.addEventListener("change", () => { holder.innerHTML = ""; holder.append(keysTable(sel.value)); });
    w.append(sel, holder);
    return w;
  }

  function viewDiploma() {
    const w = el("div", { class: "wrap" });
    const lv = state.level;
    const chs = chaptersOf(lv);
    const total = chs.length;
    const done = levelDone(lv);
    const d = el("div", { class: "card diploma" });
    d.append(el("img", { src: teacherImg(lv, done === total ? "wave" : "grr"), alt: "", style: "height:260px" }));
    if (done === total) {
      d.append(el("h1", {}, lv === "lapa" ? U("diplomaTitle") : U("diplomaTitle_" + lv)));
      d.append(el("p", {}, lv === "lapa" ? U("diplomaText") : U("diplomaText_" + lv)));
      const b = el("div", { class: "badges", style: "justify-content:center" });
      chs.forEach((ch) => b.append(el("span", { class: "badge got" }, ch.badge)));
      d.append(b);
    } else {
      d.append(el("h1", {}, U("notYetTitle")));
      d.append(el("p", {}, U("notYetText", total - done)));
    }
    w.append(d);
    const nav = el("div", { class: "navrow" });
    nav.append(el("button", { class: "btn", onclick: () => go("level-" + lv) }, "← " + U("lvl_" + lv)));
    const nx = LEVELS[LEVELS.indexOf(lv) + 1];
    if (done === total && nx) nav.append(el("button", { class: "btn primary", onclick: () => go("level-" + nx) },
      U("nextLevel", U("lvl_" + nx)) + " →"));
    w.append(nav);
    return w;
  }

  function go(id) {
    const main = $("#main");
    main.innerHTML = "";
    let v;
    if (id.startsWith("level-") && LEVELS.includes(id.slice(6))) state.level = id.slice(6);
    else if (id !== "home" && id !== "keys" && id !== "diploma") {
      if (!LEVELS.some((lv) => chaptersOf(lv).some((c) => c.id === id))) id = "home";  // a chapter that no longer exists
      else state.level = levelOf(id);
    }
    if (id === "home") v = viewHome();
    else if (id === "keys") v = viewKeys();
    else if (id === "diploma") v = viewDiploma();
    else if (id.startsWith("level-")) v = viewLevel(state.level);
    else v = viewChapter(id);
    main.append(v);
    main.scrollTop = 0;
    main.focus({ preventScroll: true });
    sidebar(id);
    state.last = id;
    save();
    document.documentElement.lang = lang;
    document.title = U("school");
  }

  $("#lang").addEventListener("change", (e) => {
    lang = e.target.value;
    state.lang = lang;
    save();
    go(state.last || "home");
  });

  function start() {
    let first = "home";
    if (MODE === "keys") first = "keys";
    else if (MODE !== "welcome" && state.last) first = state.last;
    go(first);
  }

  if (typeof qt !== "undefined" && qt.webChannelTransport) {
    const s = document.createElement("script");
    s.src = "qrc:///qtwebchannel/qwebchannel.js";
    s.onload = () => new QWebChannel(qt.webChannelTransport, (ch) => { bridge = ch.objects.furros; save(); });
    document.head.append(s);
  }
  start();
})();
