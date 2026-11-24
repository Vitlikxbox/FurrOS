"""Russian strings in the installer that have no English/Polish/Spanish translation in i18n.STRINGS.
tr("…") in the GUI, T("…")/progress(…, "…") in the backend; class-level title/subtitle/tip/step_name and lists.
    python tools/check-i18n.py"""
import ast
import re
import sys
from pathlib import Path

INST = Path(__file__).resolve().parents[1] / "src/installer"
sys.path.insert(0, str(INST))
from i18n import STRINGS  # noqa: E402

CYR = re.compile("[А-Яа-яЁё]")
missing = {}
seen = set()


def need(s, where):
    if not isinstance(s, str) or not CYR.search(s):
        return
    seen.add(s)
    tr = STRINGS.get(s)
    lacks = [l for l in ("en", "pl", "es") if not tr or not tr.get(l)]
    if lacks:
        missing.setdefault(s, (where, lacks))


for f in ("furros_installer.py", "backend.py"):
    tree = ast.parse((INST / f).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", getattr(node.func, "attr", ""))
            if name in ("tr", "T") and node.args and isinstance(node.args[0], ast.Constant):
                need(node.args[0].value, f"{f}:{node.lineno} {name}()")
            if name == "progress" and len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                need(node.args[1].value, f"{f}:{node.lineno} progress()")
            if name == "InstallError" and node.args and isinstance(node.args[0], ast.Call):
                pass  # T(...) inside, handled above
        # class attributes shown through tr(): title, subtitle, step_name, tip
        if isinstance(node, ast.ClassDef):
            for st in node.body:
                if isinstance(st, ast.Assign) and isinstance(st.value, ast.Constant):
                    for t in st.targets:
                        if getattr(t, "id", "") in ("title", "subtitle", "step_name", "tip"):
                            need(st.value.value, f"{f}:{st.lineno} {node.name}.{t.id}")
        # module-level lists of tuples shown through tr(): TIPS, SLIDES, STEPS
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") in ("TIPS", "SLIDES", "STEPS") for t in node.targets):
            for el in ast.walk(node.value):
                if isinstance(el, ast.Constant):
                    need(el.value, f"{f}:{node.lineno} list")

# keyboard layout variant descriptions, shown through tr() on the Region page
import catalog  # noqa: E402
for _code, _name, _variant in catalog.KEYBOARDS:
    need(_variant, f"catalog.py KEYBOARDS {_code}")

for s, (where, lacks) in sorted(missing.items(), key=lambda kv: kv[1][0]):
    print(f"MISSING {','.join(lacks)}  {where}  {s[:90]!r}")
print(f"I18N CHECK: {len(seen)} Russian strings checked, {len(missing)} untranslated")
