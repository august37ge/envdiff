# envdiff

A CLI tool to compare `.env` files across environments and surface missing or mismatched keys.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/youruser/envdiff.git
cd envdiff && pip install -e .
```

---

## Usage

Compare two `.env` files and see what's different:

```bash
envdiff .env.development .env.production
```

**Example output:**

```
Missing in .env.production:
  - DEBUG
  - LOCAL_DB_URL

Mismatched keys:
  - APP_ENV: "development" vs "production"
  - LOG_LEVEL: "debug" vs "info"

✔ 12 keys match across both files.
```

You can also compare multiple files at once:

```bash
envdiff .env.development .env.staging .env.production
```

Use `--keys-only` to suppress values and show only key differences:

```bash
envdiff .env.development .env.production --keys-only
```

---

## Options

| Flag | Description |
|-------------|--------------------------------------|
| `--keys-only` | Show key differences without values |
| `--quiet` | Only exit with a non-zero code on diff |
| `--json` | Output results as JSON |

---

## License

[MIT](LICENSE)