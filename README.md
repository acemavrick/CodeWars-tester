# CodeWars Tester

A local test script for running and verifying CodeWars-style problem solutions. Supports **Java** and **Python**, auto-discovers test cases, and prints colorized pass/fail results with timing.

## Setup

Copy `test.py` into your project directory alongside the expected folder structure:

```
your-project/
├── test.py
├── src/
│   ├── prob01.java
│   ├── prob01.py
│   └── ...
└── student_datasets/
    ├── prob01-1-in.txt
    ├── prob01-1-out.txt
    ├── prob01-2-in.txt
    ├── prob01-2-out.txt
    └── ...
```

You may want to add the generated directories to your `.gitignore` (see `.gitignore.example`):

```
tests/
build/
```

### Requirements

- Python 3.x (for running the script itself)
- `javac` / `java` on `PATH` (if testing Java solutions)

No external dependencies — only the Python standard library.

## Usage

```bash
# direct invocation
python test.py <language> <problem#>

# examples
python test.py java 1
python test.py py 3

# interactive mode — shows available problems and prompts
python test.py
```

### Language aliases

| Alias       | Language |
|-------------|----------|
| `j`, `java` | Java     |
| `p`, `py`, `python` | Python |

## How It Works

1. **Build** — Java files are compiled (`javac`) into `build/`. Python files are copied there. The build always runs fresh to ensure the latest source is used.
2. **Discover test cases** — Scans `student_datasets/` for paired input/output files matching the naming convention `prob<NN>-<idx>-in.txt` / `prob<NN>-<idx>-out.txt`.
3. **Run & compare** — Each test case is fed to the solution via stdin. The actual output is compared against the expected output (trailing whitespace on each line is ignored).
4. **Report** — Prints per-case pass/fail with timing, then a summary grid showing all results at a glance.

## Directory Layout

| Directory | Purpose |
|-----------|---------|
| `src/` | Your solution source files (`prob01.java`, `prob05.py`, etc.) |
| `student_datasets/` | Paired input/output `.txt` files for each problem |
| `build/` | Generated — compiled `.class` files (Java) or copied `.py` files |
| `tests/` | Generated — saved actual vs. expected output for each test case |

## Naming Conventions

- **Source files**: `prob<NN>.<ext>` where `NN` is zero-padded to 2 digits (e.g. `prob01.java`, `prob12.py`)
- **Test data**: `prob<NN>-<idx>-in.txt` and `prob<NN>-<idx>-out.txt` (e.g. `prob01-1-in.txt`, `prob01-1-out.txt`)

## Features

- **Always-fresh builds** — recompiles/copies on every run so you never test stale code
- **Auto-discovery** — interactive mode scans `src/` and lists available problems per language
- **Dual input delivery** — copies input to `input.txt` *and* pipes via stdin, so solutions using either method work
- **Colorized output** — ANSI-colored pass/fail/error indicators with per-case and total timing
- **Vertical timing grid** — summary table renders millisecond timings vertically to stay compact
- **Saved outputs** — actual and expected outputs are written to `tests/` for easy diffing

## Extending

To add a new language, edit the `RUNNERS` dict at the top of `test.py`:

```python
RUNNERS = {
    "java":   {"compile": ["javac", "-d", "build"], "run": ["java", "-cp", "build"]},
    "python": {"compile": None,                     "run": ["python3"]},
    # add your own:
    "cpp":    {"compile": ["g++", "-o", "build/prob"],  "run": ["./build/prob"]},
}
```

Then add an entry to `ALIASES` and `EXT` to match.
