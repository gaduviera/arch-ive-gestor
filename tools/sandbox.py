"""Simulation sandbox for Arch-Ive. Builds sandbox/origen + sandbox/destino with fake files,
applies source changes, and runs analyze/sync with the real engine (no UI, no APPDATA).

  python tools/sandbox.py build            # recreate sandbox/ and first sync
  python tools/sandbox.py mutate <1|2|3>   # apply change scenario to origen
  python tools/sandbox.py analyze          # show plan (no changes)
  python tools/sandbox.py sync             # apply plan
  python tools/sandbox.py tree [origen|destino]
"""
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core.executor import execute  # noqa: E402
from core.mirrors import new_mirror  # noqa: E402
from core.sync import analyze  # noqa: E402

SB = os.path.join(ROOT, "sandbox")
SRC, DST = os.path.join(SB, "origen"), os.path.join(SB, "destino")
BASE_T = time.time() - 86400 * 30  # files "created" 30 days ago


def put(rel, size, seed, folder=SRC):
    """Write a file with unique, deterministic content (size bytes) and a fixed mtime."""
    p = os.path.join(folder, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write((f"{seed}|".encode() * (size // len(seed) + 2))[:size])
    t = BASE_T + (hash_(seed) % 86400 * 20)  # distinct mtime per file
    os.utime(p, (t, t))


def hash_(s):
    return sum((i + 1) * ord(c) for i, c in enumerate(s))


# CDE-like tree: (relative path, size in bytes)
FILES = [
    ("01_WIP/ARQ/Planta_N1.dwg", 4_000_000), ("01_WIP/ARQ/Planta_N2.dwg", 3_500_000),
    ("01_WIP/ARQ/Cortes.dwg", 2_200_000), ("01_WIP/EST/Fundaciones.rvt", 9_000_000),
    ("01_WIP/EST/Calculo.xlsx", 150_000), ("02_COMPARTIDO/Coordinacion/Clash_v1.nwd", 5_100_000),
    ("02_COMPARTIDO/Coordinacion/Notas.docx", 40_000), ("03_PUBLICADO/Planos/A-101.pdf", 800_000),
    ("03_PUBLICADO/Planos/A-102.pdf", 810_000), ("03_PUBLICADO/Informes/Memoria.pdf", 1_200_000),
    ("04_ARCHIVO/Fotos/obra_001.jpg", 300_000), ("04_ARCHIVO/Fotos/obra_002.jpg", 310_000),
    ("04_ARCHIVO/Fotos/obra_003.jpg", 320_000), ("LEEME.txt", 1_000),
]


def build():
    shutil.rmtree(SB, ignore_errors=True)
    for rel, size in FILES:
        put(rel, size, rel)
    # noise that must be ignored by the default excludes
    put("01_WIP/ARQ/~$Planta_N1.dwg", 100, "lock")
    put("desktop.ini", 80, "ini")
    sync(first=True)


def mirror():
    return new_mirror("sandbox", SRC, DST, mode="mirror")


def show(plan):
    print("counts:", plan.counts(), "| copiar: %.1f MB" % (plan.bytes_to_copy / 1e6))
    for k in ("new", "modified", "moved", "deleted", "kept"):
        for item in getattr(plan, k):
            print(f"  {k:9}", item)
    if plan.scan_errors:
        print("  scan_errors:", plan.scan_errors)


def sync(first=False):
    os.makedirs(DST, exist_ok=True)
    plan = analyze(mirror())
    show(plan)
    r = execute(plan, SRC, DST)
    print("RESULT:", r)


def mutate(n):
    mv = lambda a, b: (os.makedirs(os.path.dirname(os.path.join(SRC, b)), exist_ok=True),
                       shutil.move(os.path.join(SRC, a), os.path.join(SRC, b)))
    if n == 1:  # simple: rename + move + delete + new + modify
        mv("03_PUBLICADO/Planos/A-101.pdf", "03_PUBLICADO/Planos/A-101_rev.pdf")        # rename
        mv("04_ARCHIVO/Fotos/obra_001.jpg", "04_ARCHIVO/Fotos/2026/obra_001.jpg")       # move
        os.remove(os.path.join(SRC, "01_WIP/ARQ/Cortes.dwg"))                           # delete
        put("01_WIP/ARQ/Planta_N3.dwg", 3_900_000, "nueva N3")                          # new
        put("01_WIP/EST/Calculo.xlsx", 160_000, "calculo v2")                           # modified
        os.utime(os.path.join(SRC, "01_WIP/EST/Calculo.xlsx"), None)
    elif n == 2:  # rename whole folders to similar names (files keep size+mtime)
        os.rename(os.path.join(SRC, "01_WIP"), os.path.join(SRC, "01_WIP_2026"))
        os.rename(os.path.join(SRC, "03_PUBLICADO/Planos"), os.path.join(SRC, "03_PUBLICADO/Planos_Emitidos"))
    elif n == 3:  # ambiguity + case-only rename
        put("04_ARCHIVO/Fotos/dup_a.jpg", 500_000, "gemelo")   # two identical size+mtime files
        shutil.copy2(os.path.join(SRC, "04_ARCHIVO/Fotos/dup_a.jpg"), os.path.join(SRC, "04_ARCHIVO/Fotos/dup_b.jpg"))
        os.rename(os.path.join(SRC, "LEEME.txt"), os.path.join(SRC, "leeme.TXT"))


def tree(which):
    root = DST if which == "destino" else SRC
    for d, dirs, fs in os.walk(root):
        dirs.sort()
        for f in sorted(fs):
            print(os.path.relpath(os.path.join(d, f), root))


if __name__ == "__main__":
    c = sys.argv[1:] or ["-h"]
    {"build": build, "analyze": lambda: show(analyze(mirror())), "sync": sync,
     "mutate": lambda: mutate(int(c[1])), "tree": lambda: tree(c[1] if len(c) > 1 else "origen")
     }.get(c[0], lambda: print(__doc__))()
