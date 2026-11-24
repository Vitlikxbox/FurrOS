/* A safe pretend shell for lessons: virtual files, fake pacman/sudo, missions with checks. */
window.FurrTerminal = (() => {
  const HOME = "/home/furry";

  function makeFs(T) {
    return {
      "/": { d: 1 }, "/home": { d: 1 }, [HOME]: { d: 1 },
      [HOME + "/Documents"]: { d: 1 }, [HOME + "/Downloads"]: { d: 1 }, [HOME + "/Pictures"]: { d: 1 },
      [HOME + "/Music"]: { d: 1 },
      [HOME + "/Documents/todo.txt"]: { c: T.files.todo },
      [HOME + "/Pictures/lapa.png"]: { c: "\u0089PNG…" },
      [HOME + "/.bashrc"]: { c: "# ~/.bashrc\n[[ -f /etc/furros/bashrc ]] && . /etc/furros/bashrc\n" },
      "/etc": { d: 1 }, "/etc/hostname": { c: "furros\n" }, "/etc/os-release": { c: 'NAME="FurrOS"\nID=furros\nID_LIKE=arch\n' },
      "/usr": { d: 1 }, "/usr/bin": { d: 1 }, "/tmp": { d: 1 },
    };
  }

  const REPO = {
    cowsay: "3.8.4-1", sl: "5.05-4", cmatrix: "2.0-6", gimp: "3.0.4-2", steam: "1.0.0.83-1",
    firefox: "141.0-1", lolcat: "100.0.1-7", htop: "3.4.1-1", neofetch: "7.1.0-2", telegram: "5.16-1",
  };

  // mission checks: (st, argv, raw) => bool
  const SETS = {
    basics: [
      (s, a) => a[0] === "pwd",
      (s, a) => a[0] === "ls",
      (s) => s.cwd === HOME + "/Documents",
      (s, a) => a[0] === "cd" && s.cwd === HOME && s.flags.wasDocs,
      (s) => !!s.fs[HOME + "/kosti"]?.d,
      (s) => s.fs[HOME + "/kosti/lapa.txt"] !== undefined,
      (s) => (s.fs[HOME + "/kosti/lapa.txt"]?.c || "").trim().length > 0,
      (s, a) => a[0] === "cat" && s.flags.catLapa,
      (s) => s.fs[HOME + "/kosti/copy.txt"] !== undefined,
      (s) => s.flags.copyRemoved,
    ],
    packages: [
      (s, a) => a[0] === "pacman" && /^-Ss/.test(a[1] || "") && a.includes("cowsay"),
      (s) => s.installed.has("cowsay"),
      (s, a) => a[0] === "cowsay",
      (s) => s.flags.updated,
      (s) => s.flags.removedCowsay,
    ],
  };

  function create(setId, C, toast) {
    const T = C.term;
    const st = {
      fs: makeFs(T), cwd: HOME, hist: [], hi: 0, mission: 0, flags: {}, installed: new Set(["bash", "fastfetch"]),
      pending: null,
    };
    const checks = SETS[setId] || [];
    const texts = (C.missions && C.missions[setId]) || [];

    const root = document.createElement("div");
    root.className = "term";
    root.innerHTML = `<div class="top"><span class="dot" style="background:#E23A44"></span><span class="dot" style="background:#FFBE5A"></span><span class="dot" style="background:#78E6A0"></span>&nbsp; ${T.title}</div>
      <div class="out" role="log" aria-live="polite"></div>
      <div class="line"><span class="ps1"></span><input aria-label="${T.inputLabel}" autocomplete="off" spellcheck="false"></div>`;
    const out = root.querySelector(".out");
    const input = root.querySelector("input");
    const ps1 = root.querySelector(".ps1");

    const box = document.createElement("div");
    box.className = "card";
    box.innerHTML = `<b>🦴 ${T.missionsTitle}</b>`;
    const ol = document.createElement("ol");
    ol.className = "missions";
    texts.forEach((t) => { const li = document.createElement("li"); li.innerHTML = t; ol.append(li); });
    box.append(ol);
    const reset = document.createElement("button");
    reset.className = "btn";
    reset.style.marginTop = "8px";
    reset.textContent = "↺ " + T.reset;
    reset.onclick = () => {
      Object.assign(st, { fs: makeFs(T), cwd: HOME, mission: 0, flags: {}, installed: new Set(["bash", "fastfetch"]) });
      out.innerHTML = "";
      print(T.welcome, "c-dim");
      paint();
    };
    box.append(reset);

    const wrap = document.createElement("div");
    wrap.append(box, root);

    function esc(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
    function print(text, cls) {
      const d = document.createElement("div");
      if (cls) d.className = cls;
      d.innerHTML = cls === "html" ? text : esc(text);
      out.append(d);
      out.scrollTop = out.scrollHeight;
    }
    function prompt() {
      const p = st.cwd === HOME ? "~" : st.cwd.startsWith(HOME) ? "~" + st.cwd.slice(HOME.length) : st.cwd;
      return `🐾 furry@furros ${p} $`;
    }
    function paint() {
      ps1.textContent = st.pending ? T.sudoPrompt : prompt();
      input.type = st.pending ? "password" : "text";
      [...ol.children].forEach((li, i) => {
        li.classList.toggle("done", i < st.mission);
        li.classList.toggle("now", i === st.mission);
      });
    }

    function abs(p) {
      if (!p || p === "~") return HOME;
      if (p.startsWith("~/")) p = HOME + p.slice(1);
      if (!p.startsWith("/")) p = st.cwd + "/" + p;
      const parts = [];
      for (const seg of p.split("/")) {
        if (!seg || seg === ".") continue;
        if (seg === "..") parts.pop(); else parts.push(seg);
      }
      return "/" + parts.join("/");
    }
    const parent = (p) => p.slice(0, p.lastIndexOf("/")) || "/";
    const base = (p) => p.slice(p.lastIndexOf("/") + 1);
    const children = (dir) => Object.keys(st.fs).filter((k) => k !== dir && parent(k) === dir).sort();

    function parse(line) {
      const out = [];
      let cur = "", q = null, has = false;
      for (const ch of line) {
        if (q) { if (ch === q) q = null; else cur += ch; continue; }
        if (ch === '"' || ch === "'") { q = ch; has = true; continue; }
        if (ch === " ") { if (cur || has) { out.push(cur); cur = ""; has = false; } continue; }
        cur += ch;
      }
      if (cur || has) out.push(cur);
      return out;
    }

    const cmds = {
      help() { print(T.help, "c-dim"); },
      pwd() { print(st.cwd); },
      whoami() { print("furry"); },
      date() { print(new Date().toString()); },
      clear() { out.innerHTML = ""; },
      history() { st.hist.forEach((h, i) => print(`${String(i + 1).padStart(4)}  ${h}`)); },
      uname(a) { print(a.includes("-a") ? "Linux furros 6.16.8-arch1-1 #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux" : "Linux"); },
      bark() { print(T.bark, "c-acc"); },
      echo(a) { print(a.join(" ")); },
      ls(a) {
        const all = a.includes("-a") || a.includes("-la") || a.includes("-al");
        const long = a.some((x) => /^-\w*l/.test(x));
        const target = abs(a.find((x) => !x.startsWith("-")) || ".");
        const n = st.fs[target];
        if (!n) return print(T.noSuch.replace("{0}", a.find((x) => !x.startsWith("-"))), "c-err");
        if (!n.d) return print(base(target));
        const items = children(target).filter((k) => all || !base(k).startsWith("."));
        if (!items.length) return;
        if (long) items.forEach((k) => print(`${st.fs[k].d ? "drwxr-xr-x" : "-rw-r--r--"}  furry furry  ${st.fs[k].d ? "4096" : String((st.fs[k].c || "").length).padStart(4)}  ${base(k)}`));
        else print(items.map((k) => st.fs[k].d ? `<span class="c-dir">${esc(base(k))}/</span>` : esc(base(k))).join("   "), "html");
      },
      cd(a) {
        const t = abs(a[0] || "~");
        if (!st.fs[t]) return print(T.noSuch.replace("{0}", a[0]), "c-err");
        if (!st.fs[t].d) return print(T.notDir.replace("{0}", a[0]), "c-err");
        st.cwd = t;
        if (t === HOME + "/Documents") st.flags.wasDocs = true;
      },
      mkdir(a) {
        const names = a.filter((x) => !x.startsWith("-"));
        if (!names.length) return print(T.missing.replace("{0}", "mkdir"), "c-err");
        for (const n of names) {
          const p = abs(n);
          if (st.fs[p]) { print(T.exists.replace("{0}", n), "c-err"); continue; }
          if (!st.fs[parent(p)]) {
            if (!a.includes("-p")) { print(T.noSuch.replace("{0}", n), "c-err"); continue; }
            let acc = "";
            for (const seg of p.split("/").filter(Boolean)) { acc += "/" + seg; st.fs[acc] = st.fs[acc] || { d: 1 }; }
          }
          st.fs[p] = { d: 1 };
        }
      },
      touch(a) {
        for (const n of a) {
          const p = abs(n);
          if (!st.fs[parent(p)]) { print(T.noSuch.replace("{0}", n), "c-err"); continue; }
          if (!st.fs[p]) st.fs[p] = { c: "" };
        }
      },
      cat(a) {
        if (!a.length) return print(T.missing.replace("{0}", "cat"), "c-err");
        for (const n of a) {
          const p = abs(n), f = st.fs[p];
          if (!f) { print(T.noSuch.replace("{0}", n), "c-err"); continue; }
          if (f.d) { print(T.isDir.replace("{0}", n), "c-err"); continue; }
          print(f.c);
          if (p === HOME + "/kosti/lapa.txt" && f.c.trim()) st.flags.catLapa = true;
        }
      },
      rm(a) {
        const rec = a.some((x) => /^-\w*r/.test(x));
        for (const n of a.filter((x) => !x.startsWith("-"))) {
          const p = abs(n), f = st.fs[p];
          if (!f) { print(T.noSuch.replace("{0}", n), "c-err"); continue; }
          if (p === "/" || p === HOME) { print(T.rmNo, "c-err"); continue; }
          if (f.d && !rec) { print(T.isDir.replace("{0}", n) + " " + T.rmHint, "c-err"); continue; }
          Object.keys(st.fs).forEach((k) => { if (k === p || k.startsWith(p + "/")) delete st.fs[k]; });
          if (p === HOME + "/kosti/copy.txt") st.flags.copyRemoved = true;
        }
      },
      cp(a) { move(a, false); },
      mv(a) { move(a, true); },
      nano() { print(T.noNano, "c-dim"); },
      vim() { print(T.noNano, "c-dim"); },
      man(a) { print(T.man.replace("{0}", a[0] || "man"), "c-dim"); },
      fastfetch() {
        print(`<span class="c-acc">   ▄█▄ ▄█▄</span>      <b style="color:#7FF0F0">furry@furros</b>
<span class="c-acc"> ▄▄ ▀ ▄ ▀ ▄▄</span>    OS: FurrOS 1.0
<span class="c-acc"> ▀▀ ▄███▄ ▀▀</span>    Shell: bash 5.3
<span class="c-acc">   ███<span class="c-err">⚡</span>███</span>     Packages: ${st.installed.size + 1100} (pacman)
<span class="c-acc">    ▀▀▀▀▀</span>      💖 good dogs only 💖`, "html");
      },
      cowsay(a) {
        if (!st.installed.has("cowsay")) return print(T.notFound.replace("{0}", "cowsay"), "c-err");
        const msg = a.join(" ") || "Moo";
        const line = "-".repeat(msg.length + 2);
        print(` ${"_".repeat(msg.length + 2)}\n< ${msg} >\n ${line}\n        \\   ^__^\n         \\  (oo)\\_______\n            (__)\\       )\\/\\\n                ||----w |\n                ||     ||`);
      },
      sl() {
        if (!st.installed.has("sl")) return print(T.notFound.replace("{0}", "sl"), "c-err");
        print("      ====        ________                ___________\n  _D _|  |_______/        \\__I_I_____===__|_________|\n   |(_)---  |   H\\________/ |   |        =|___ ___|\n   /     |  |   H  |  |     |   |         ||_| |_||   🚂 choo choo", "c-ok");
      },
      treat() { cmds.sudo(["pacman", "-Syu"]); },
      pacman(a, sudo) {
        const op = a[0] || "";
        const pk = a.slice(1).filter((x) => !x.startsWith("-"));
        if (/^-S[sS]*s/.test(op) || op === "-Ss") {
          const term = pk[0] || "";
          Object.entries(REPO).filter(([n]) => n.includes(term)).forEach(([n, v]) =>
            print(`<span class="c-acc">extra/</span><b>${n}</b> <span class="c-ok">${v}</span>${st.installed.has(n) ? " <span class='c-dim'>[installed]</span>" : ""}\n    ${T.pkgDesc[n] || ""}`, "html"));
          return;
        }
        if (op === "-Q") { [...st.installed].sort().forEach((n) => print(`${n} ${REPO[n] || "1.0-1"}`)); return; }
        if (!sudo) return print(T.needRoot, "c-err");
        if (/^-Syu/.test(op)) {
          print(":: Synchronizing package databases...\n core is up to date\n extra is up to date\n:: Starting full system upgrade...", "c-dim");
          print(T.upgraded, "c-ok");
          st.flags.updated = true;
          return;
        }
        if (/^-S/.test(op)) {
          if (!pk.length) return print(T.missing.replace("{0}", "pacman -S"), "c-err");
          for (const n of pk) {
            if (!REPO[n]) { print(`error: target not found: ${n}`, "c-err"); continue; }
            print(`resolving dependencies...\nPackages (1) ${n}-${REPO[n]}\n:: Proceed with installation? [Y/n] y\n(1/1) installing ${n}  [##################] 100%`, "c-dim");
            // the first install: explain the [Y/n] question newcomers meet in a real terminal
            if (!st.flags.ynShown && T.ynHint) { st.flags.ynShown = true; print(T.ynHint, "c-acc"); }
            st.installed.add(n);
            print(T.installed.replace("{0}", n), "c-ok");
          }
          return;
        }
        if (/^-R/.test(op)) {
          for (const n of pk) {
            if (!st.installed.has(n)) { print(`error: target not found: ${n}`, "c-err"); continue; }
            st.installed.delete(n);
            print(`(1/1) removing ${n}  [##################] 100%`, "c-dim");
            if (n === "cowsay") st.flags.removedCowsay = true;
          }
          return;
        }
        print(T.pacmanHelp, "c-dim");
      },
      yay(a) { print(T.yaySandbox, "c-dim"); },
      sudo(a) {
        if (!a.length) return print(T.missing.replace("{0}", "sudo"), "c-err");
        st.pending = a;
      },
      exit() { print(T.noExit, "c-dim"); },
    };

    function move(a, isMove) {
      const [src, dst] = a.filter((x) => !x.startsWith("-"));
      if (!src || !dst) return print(T.missing.replace("{0}", isMove ? "mv" : "cp"), "c-err");
      const s = abs(src);
      let d = abs(dst);
      if (!st.fs[s]) return print(T.noSuch.replace("{0}", src), "c-err");
      if (st.fs[d]?.d) d = d + "/" + base(s);
      if (!st.fs[parent(d)]) return print(T.noSuch.replace("{0}", dst), "c-err");
      Object.keys(st.fs).forEach((k) => {
        if (k === s || k.startsWith(s + "/")) {
          st.fs[d + k.slice(s.length)] = { ...st.fs[k] };
          if (isMove) delete st.fs[k];
        }
      });
    }

    function run(raw) {
      if (st.pending) {
        const cmd = st.pending;
        st.pending = null;
        print(T.sudoPrompt);
        if (!raw) { print(T.sudoEmpty, "c-err"); return; }
        exec(cmd, true, raw);
        return;
      }
      print(`${prompt()} ${raw}`, "c-dim");
      if (!raw.trim()) return;
      st.hist.push(raw);
      // redirection: echo text > file
      const m = raw.match(/^(.*?)\s*(>>?)\s*(\S+)\s*$/);
      if (m && m[1].trim().startsWith("echo")) {
        const text = parse(m[1]).slice(1).join(" ") + "\n";
        const p = abs(m[3]);
        if (!st.fs[parent(p)]) return print(T.noSuch.replace("{0}", m[3]), "c-err");
        if (st.fs[p]?.d) return print(T.isDir.replace("{0}", m[3]), "c-err");
        st.fs[p] = { c: (m[2] === ">>" && st.fs[p] ? st.fs[p].c : "") + text };
        after(["echo"], raw);
        return;
      }
      exec(parse(raw), false, raw);
    }

    function exec(argv, sudo, raw) {
      const [name, ...args] = argv;
      if (sudo && name === "rm" && args.some((x) => x === "/" || x === "/*")) { print(T.rmNo, "c-err"); return; }
      const fn = cmds[name];
      if (!fn) print(T.notFound.replace("{0}", name), "c-err");
      else fn(args, sudo);
      if (!st.pending) after(argv, raw);
      paint();
    }

    function after(argv, raw) {
      const ck = checks[st.mission];
      if (ck && ck(st, argv, raw)) {
        st.mission++;
        if (st.mission >= checks.length) {
          print("🎉 " + T.allDone, "c-ok");
          toast(T.allDone);
        } else {
          toast("🦴 +1");
        }
      }
      paint();
    }

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const v = input.value;
        input.value = "";
        run(v);
        paint();
      } else if (e.key === "ArrowUp" && !st.pending) {
        st.hi = Math.max(0, (st.hi || st.hist.length) - 1);
        input.value = st.hist[st.hi] || "";
        e.preventDefault();
      } else if (e.key === "ArrowDown" && !st.pending) {
        st.hi = Math.min(st.hist.length, st.hi + 1);
        input.value = st.hist[st.hi] || "";
        e.preventDefault();
      } else if (e.key === "Tab") {
        e.preventDefault();
        const parts = input.value.split(" ");
        const last = parts.pop();
        const dir = last.includes("/") ? abs(last.slice(0, last.lastIndexOf("/")) || "/") : st.cwd;
        const pre = last.slice(last.lastIndexOf("/") + 1);
        const hits = children(dir).map(base).filter((n) => n.startsWith(pre));
        if (parts.length === 0) {
          const cmdHits = Object.keys(cmds).filter((c) => c.startsWith(last));
          if (cmdHits.length === 1) input.value = cmdHits[0] + " ";
          else if (cmdHits.length) print(cmdHits.join("  "), "c-dim");
        } else if (hits.length === 1) {
          const full = last.slice(0, last.lastIndexOf("/") + 1) + hits[0] + (st.fs[dir + "/" + hits[0]]?.d ? "/" : "");
          input.value = [...parts, full].join(" ");
        } else if (hits.length) print(hits.join("  "), "c-dim");
      } else if (e.key === "c" && e.ctrlKey) {
        print(`${prompt()} ${input.value}^C`, "c-dim");
        input.value = "";
        st.pending = null;
        paint();
      } else if (e.key === "l" && e.ctrlKey) {
        e.preventDefault();
        out.innerHTML = "";
      }
    });
    root.addEventListener("click", () => input.focus());
    print(T.welcome, "c-dim");
    paint();
    return wrap;
  }

  return { create };
})();
