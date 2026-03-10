"""
usage:
    python test.py <lang> <problem>   # e.g. python test.py java 1
    python test.py                    # interactive prompts
"""

import os
import shutil
import subprocess
import sys
import time

# ── configure runners here ──────────────────────────────────────────
# each entry is {compile: [...] | None, run: [...]}
# the source/class path is appended automatically at call time.
RUNNERS = {
    "java": {
        "compile": ["javac", "-d", "build"],
        "run":     ["java", "-cp", "build"],
    },
    "python": {
        "compile": None,
        "run":     ["python3"],
    },
}

# shorthand aliases → canonical runner key
ALIASES = {
    "j": "java", "java": "java",
    "p": "python", "py": "python", "python": "python",
}

SRC_DIR   = "src"
BUILD_DIR = "build"
DATA_DIR  = "student_datasets"
TEST_DIR  = "tests"

# ansi — bold, dim, and 8 colors are universally supported
BOLD   = "\x1b[1m"
DIM    = "\x1b[2m"
RESET  = "\x1b[0m"
RED    = "\x1b[31m"
GREEN  = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE   = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN   = "\x1b[36m"
WHITE  = "\x1b[37m"
BRED   = "\x1b[1;31m"
BGREEN = "\x1b[1;32m"
BYELLOW = "\x1b[1;33m"
BCYAN  = "\x1b[1;36m"

PASS, FAIL, ERR = 0, 1, 2

EXT = {"java": ".java", "python": ".py"}


def prob_name(problem):
    return f"prob{int(problem):02d}"


def discover_available():
    """scan src/ for source files, return {lang: sorted list of problem numbers}."""
    if not os.path.isdir(SRC_DIR):
        return {}
    available = {lang: [] for lang in RUNNERS}
    for f in os.listdir(SRC_DIR):
        for lang, ext in EXT.items():
            if f.endswith(ext) and f.startswith("prob"):
                try:
                    num = int(f.replace("prob", "").replace(ext, ""))
                    available[lang].append(num)
                except ValueError:
                    continue
    for lang in available:
        available[lang].sort()
    return available


def build_source(lang, problem):
    """compile (java) or copy (python) into build/, skipping if up to date."""
    name = prob_name(problem)
    runner = RUNNERS[lang]
    os.makedirs(BUILD_DIR, exist_ok=True)

    if lang == "java":
        src  = os.path.join(SRC_DIR, f"{name}.java")
        dest = os.path.join(BUILD_DIR, f"{name}.class")
    else:
        src  = os.path.join(SRC_DIR, f"{name}.py")
        dest = os.path.join(BUILD_DIR, f"{name}.py")

    if not os.path.exists(src):
        available = discover_available().get(lang, [])
        if available:
            nums = ", ".join(str(n) for n in available)
            print(f"{BRED}error:{RESET} {src} not found")
            print(f"{DIM}available {lang} problems: {nums}{RESET}")
        else:
            print(f"{BRED}error:{RESET} {src} not found (no {lang} files in {SRC_DIR}/)")
        sys.exit(1)

    t0 = time.perf_counter()

    if runner["compile"] is not None:
        result = subprocess.run(runner["compile"] + [src], capture_output=True)
        if result.returncode != 0:
            print(f"{BRED}build  ✗ compile error{RESET}")
            print(result.stderr.decode())
            sys.exit(1)
    else:
        shutil.copy2(src, dest)

    ms = (time.perf_counter() - t0) * 1000
    print(f"{DIM}build  {RESET}{GREEN}✓{RESET} {DIM}{ms:.0f}ms{RESET}")


def run_cmd(lang, problem):
    """construct the subprocess arg list for running the built artifact."""
    name = prob_name(problem)
    base = RUNNERS[lang]["run"]
    if lang == "java":
        return base + [name]
    return base + [os.path.join(BUILD_DIR, f"{name}.py")]


def discover_testcases(problem):
    """find paired input/output files, return sorted list of (idx, in_path, out_path)."""
    prefix = prob_name(problem)
    ins, outs = {}, {}

    if not os.path.isdir(DATA_DIR):
        print(f"{BRED}error:{RESET} data directory '{DATA_DIR}/' not found")
        sys.exit(1)

    for f in os.listdir(DATA_DIR):
        if not f.startswith(prefix):
            continue
        # format: prob01-2-in.txt / prob01-2-out.txt
        parts = f.replace(".txt", "").split("-")
        if len(parts) < 3:
            continue
        idx = parts[1]
        if parts[2] == "in":
            ins[idx] = os.path.join(DATA_DIR, f)
        elif parts[2] == "out":
            outs[idx] = os.path.join(DATA_DIR, f)

    if not ins:
        print(f"{RED}error:{RESET} no input files found for {prefix}")
        sys.exit(1)

    paired = []
    for idx in sorted(ins):
        if idx not in outs:
            print(f"{YELLOW}warning:{RESET} no matching output for {ins[idx]}, skipping")
            continue
        paired.append((idx, ins[idx], outs[idx]))

    if not paired:
        print(f"{RED}error:{RESET} no complete testcase pairs found")
        sys.exit(1)

    return paired


def run_tests(lang, problem):
    """build, then run all testcases and print results."""
    name = prob_name(problem)
    header = f" {lang} · {name} "
    print(f"\n{BOLD}{BLUE}{'─' * 3}{header}{'─' * (44 - len(header))}{RESET}\n")

    build_source(lang, problem)
    args = run_cmd(lang, problem)
    cases = discover_testcases(problem)

    print(f"{DIM}{len(cases)} testcase(s) found{RESET}\n")
    os.makedirs(TEST_DIR, exist_ok=True)

    summary = []
    times = []

    for idx, in_path, out_path in cases:
        # write input.txt AND pipe stdin — covers both input methods
        shutil.copy(in_path, "input.txt")

        t0 = time.perf_counter()

        with open(in_path) as fin:
            result = subprocess.run(args, stdin=fin, capture_output=True)

        ms = (time.perf_counter() - t0) * 1000
        times.append(ms)

        if result.returncode != 0:
            print(f"  {BRED}✗ tc {idx}{RESET}  {DIM}{ms:.0f}ms{RESET}  {RED}ERROR{RESET}")
            print(result.stderr.decode(), end="")
            summary.append(ERR)
            print(f"{DIM}{'·' * 40}{RESET}")
            continue

        actual = "\n".join(line.rstrip() for line in result.stdout.decode().splitlines()).rstrip()
        with open(out_path) as f:
            expected = "\n".join(line.rstrip() for line in f.read().splitlines()).rstrip()

        with open(os.path.join(TEST_DIR, f"{name}-{idx}.my.out"), "w") as f:
            f.write(actual)
        with open(os.path.join(TEST_DIR, f"{name}-{idx}.judge.out"), "w") as f:
            f.write(expected)

        if actual == expected:
            print(f"  {BGREEN}✓ tc {idx}{RESET}  {DIM}{ms:.0f}ms{RESET}")
            summary.append(PASS)
        else:
            print(f"  {BRED}✗ tc {idx}{RESET}  {DIM}{ms:.0f}ms{RESET}")
            summary.append(FAIL)

        print(f"{CYAN}got:{RESET}")
        print(actual)
        print(f"{MAGENTA}expected:{RESET}")
        print(expected)
        print(f"{DIM}{'·' * 40}{RESET}")

    # cleanup temp file
    if os.path.exists("input.txt"):
        os.remove("input.txt")

    # summary
    passed = summary.count(PASS)
    total = len(summary)
    color = BGREEN if passed == total else BRED if passed == 0 else BYELLOW

    print(f"\n{BOLD}{'═' * 47}{RESET}")
    print(f"  {color}{passed}/{total} passed{RESET}  {DIM}·  {sum(times):.0f}ms total{RESET}")

    maxw = max(len(str(total)), 1)
    print(f"  {DIM}TC{RESET}" + "".join(f" {i:>{maxw}}" for i in range(1, total + 1)))
    sym = {PASS: f"{GREEN}✓{RESET}", FAIL: f"{RED}✗{RESET}", ERR: f"{YELLOW}!{RESET}"}
    print(f"  {DIM}->{RESET}" + "".join(f" {sym[s]:>{maxw}}" for s in summary))

    # ms as vertical digits so wide numbers don't bloat columns
    ms_strs = [f"{int(t)}" for t in times]
    depth = max((len(s) for s in ms_strs), default=0)
    # read top-to-bottom = the number; short values have gap at bottom
    padded = [s.ljust(depth) for s in ms_strs]
    for row in range(depth):
        label = "ms" if row == 0 else "  "
        print(f"  {DIM}{label}{RESET}" + "".join(f" {DIM}{p[row]}{RESET}" for p in padded))
    print()


def resolve_lang(raw):
    """resolve alias (j, py, p, ...) to canonical runner key."""
    key = ALIASES.get(raw.lower())
    if key is None:
        aliases_by_lang = {}
        for alias, canonical in ALIASES.items():
            aliases_by_lang.setdefault(canonical, []).append(alias)
        opts = ", ".join(f"{k} ({'/'.join(v)})" for k, v in aliases_by_lang.items())
        print(f"{BRED}error:{RESET} unknown language '{raw}'. options: {opts}")
        sys.exit(1)
    return key


if __name__ == "__main__":
    if len(sys.argv) > 2:
        lang, problem = resolve_lang(sys.argv[1]), sys.argv[2]
    else:
        # interactive mode — show what's available
        print(f"{DIM}hint: python test.py <j|py> <problem#>{RESET}\n")

        available = discover_available()

        if len(sys.argv) <= 1:
            for ln, nums in available.items():
                if nums:
                    print(f"  {BOLD}{ln}{RESET}  {DIM}{', '.join(str(n) for n in nums)}{RESET}")
            print()
            lang = resolve_lang(input(f"{CYAN}language{RESET} (j/py): ").strip())
        else:
            lang = resolve_lang(sys.argv[1])

        nums = available.get(lang, [])
        if nums:
            print(f"  {DIM}available: {', '.join(str(n) for n in nums)}{RESET}")
        problem = input(f"{CYAN}problem #{RESET}: ").strip()

    try:
        int(problem)
    except ValueError:
        print(f"{BRED}error:{RESET} problem must be a number, got '{problem}'")
        sys.exit(1)

    run_tests(lang, problem)
