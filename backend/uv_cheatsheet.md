# ⚡ Daily `uv` Cheat Sheet

`uv` is an extremely fast Python package installer and resolver written in Rust. It acts as a drop-in replacement for `pip` and `virtualenv`, but runs 10x-100x faster.

Here is exactly how you should use it in your day-to-day workflow.

## 1. Setting up a new project

Whenever you start a new Python project, the first thing you want to do is create a virtual environment to keep your packages isolated.

```bash
# Create a virtual environment (replaces `python -m venv .venv`)
uv venv
```

**Don't forget to activate it!**
- **Windows (PowerShell):** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

> [!TIP]
> You only need to run `uv venv` once per project!

## 2. Installing Packages

`uv pip` is designed to be a direct replacement for standard `pip`. You can use all the same flags you already know.

### Installing a single package
```bash
# Replaces `pip install requests`
uv pip install requests
```

### Installing from a requirements file
```bash
# Replaces `pip install -r requirements.txt`
uv pip install -r requirements.txt
```

### Upgrading a package
```bash
uv pip install --upgrade requests
```

## 3. Saving Your Packages (Freezing)

When you install new packages, you should save them so other people (or your deployment server) know what your project needs.

```bash
# Replaces `pip freeze > requirements.txt`
uv pip freeze > requirements.txt
```

> [!NOTE]
> Alternatively, `uv pip compile` is a powerful tool to lock dependencies from a `pyproject.toml` or `requirements.in` file, similar to `pip-tools`.

## 4. Running Scripts Easily (`uv run`)

One of the coolest features of `uv` is `uv run`. It automatically runs your script **inside** the virtual environment, even if you forgot to activate it!

```bash
# Instead of activating the env and typing `python script.py`
uv run script.py

# You can even use it for modules:
uv run -m pytest
```

## 5. Other Handy Commands

- **See what's installed:** 
  `uv pip list`
- **Uninstall a package:** 
  `uv pip uninstall <package-name>`
- **Check your uv version:** 
  `uv --version`
- **Update uv itself:**
  `uv self update`

---

### 🚀 Summary Workflow for Today
1. Open terminal in project.
2. Activate env: `.venv\Scripts\activate`
3. Install a new tool if you need it: `uv pip install <tool>`
4. Run your code: `python my_code.py` (or use `uv run my_code.py`!)
