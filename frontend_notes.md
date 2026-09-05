# Frontend Notes — AskAnyDoc (Week 2)

> My reference for what each frontend tool/file does. Written while setting up the React + Vite page.

---

## The three tools (they get confused because the names overlap)

| Tool | Job | When it runs |
|---|---|---|
| **npm** | Downloads and manages JavaScript libraries. | Whenever I install something. |
| **create-vite** | Copied the React starter files into my folder. | ONCE, at setup. Already gone. |
| **vite** | Runs the dev server + builds for production. | Every time I develop or build. |

**Key point:** `create-vite` (the scaffolder) and `vite` (the build tool) are DIFFERENT programs that share a name.
Vite does NOT download anything — that's npm's job.

---

## The command I ran, decoded

```
npm create vite@latest . -- --template react
```

- `npm create vite@latest` → runs a TEMPORARY tool (`create-vite`) fetched from the npm registry. It contains starter templates for React, Vue, Svelte, etc.
- `.` → build in the current folder (not a new subfolder)
- `--` → divider: everything after this is passed to the tool, not consumed by npm
- `--template react` → picks the React starter template and copies it here

**One line:** it runs a temporary tool that holds starter templates, picks the React one, and copies those files into my folder.

The tool is temporary. The files it created are permanent (mine).

---

## Starter files ≠ the React library

- The template gave me **example files** + a shopping list (`package.json`).
- React itself was NOT downloaded at that point.
- `npm install` is what actually downloaded React and Vite into `node_modules/`.

Same pattern as Python: listing ≠ installing.

---

## What Vite actually does (its real role)

**1. Dev server** — `npm run dev`
Serves the app at `http://localhost:5173`. Watches my files: edit + save → browser updates instantly.
This is PRIVATE — only on my machine. Nobody else can reach it.

**2. Build for production** — `npm run build`
Translates my React into plain HTML/CSS/JS in a `dist/` folder.
Those plain files are what get uploaded to S3.

**Why the translation is needed:** browsers can't read React directly. React uses syntax browsers don't understand. Vite is the bridge.

```
I write React → Vite translates → plain HTML/CSS/JS → S3 serves → browser runs
```

---

## What React is (vs plain JS)

Plain JS: I manually find HTML elements and update them on every change. Gets messy fast.

React: I DESCRIBE what the page should look like for the current data. When data changes, React updates the page itself.

**Same idea as Terraform** — declare the end state, tool figures out how.
**Difference:** Terraform needs me to run `apply`. React re-applies automatically whenever data changes.

---

## The files Vite created, and what each does

| File / Folder | What it is | Do I edit it? |
|---|---|---|
| `src/` | **My code.** `App.jsx` lives here. | YES — this is where I work |
| `src/App.jsx` | The actual page component. Becomes my chatbot. | YES |
| `node_modules/` | Downloaded libraries (React, Vite). Thousands of files. | NO — never edit, never commit |
| `index.html` | The real HTML skeleton the browser loads. React plugs into it. | Rarely |
| `public/` | Static files (images, icons) served as-is. | Sometimes |
| `package.json` | The LIST of libraries this project needs. | Sometimes |
| `package-lock.json` | The EXACT versions actually installed. | NO — auto-managed, but DO commit it |
| `vite.config.js` | Vite's own settings. | Rarely |
| `eslint.config.js` | Linter settings (code style/mistake checker). | Rarely |
| `.gitignore` | Vite made its own — mainly excludes `node_modules/`. | Sometimes |

---

## Things I already know, renamed

| Python / Terraform (I know this) | JavaScript equivalent |
|---|---|
| `requirements.txt` — lists libraries | `package.json` |
| `pip install -r requirements.txt` | `npm install` |
| `.venv/` — downloaded libs, git-ignored | `node_modules/` |
| `.terraform.lock.hcl` — pins exact versions | `package-lock.json` (DO commit this one) |

---

## Commands I'll actually use

| Command | What it does |
|---|---|
| `npm install` | Download everything listed in `package.json` |
| `npm run dev` | Start the dev server (private, localhost:5173) |
| `npm run build` | Build plain files into `dist/` (for S3) |
| `Ctrl+C` | Stop the dev server (it holds the terminal open) |

---

## Two places, don't confuse them

- **`localhost:5173`** = dev server. Private. Only my machine. For building.
- **S3 site URL** = public. The real deployed site. Gets the `dist/` files after `npm run build`.

---

## Other things I learned along the way

- **Linter** = a spell-checker for code (catches mistakes/style issues). I chose **ESLint** — the industry standard. (Pylance was the Python equivalent VS Code offered me earlier.)
- **`.gitkeep`** = a 0-byte placeholder file. Git can't track empty folders, so this keeps an otherwise-empty folder visible in the repo.
- **Flag** = an extra option on a command (`--upgrade`, `--since 5m`, `--template react`). Starts with `-` or `--`.
- **VS Code Simple Browser** = VS Code auto-opens `localhost` URLs in a tab inside the editor. Not something I configured — it just does it.
- **npm registry** = the central public library for JavaScript packages. Same idea as HashiCorp's provider registry for Terraform.

---

*Last updated: Week 2, frontend setup (Vite + React scaffolded, dev server running). Next: edit `src/App.jsx` into the chatbot page, then `npm run build` and deploy `dist/` to S3.*
