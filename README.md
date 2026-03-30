# chatgpt-export

Export all ChatGPT conversations as markdown files, organized by project folders.

## Install

```bash
uv pip install -e .
```

## Get your access token

1. Open [chatgpt.com](https://chatgpt.com) in your browser and log in
2. Open DevTools (`F12` or `Cmd+Shift+I`)
3. In the **Console** tab, run:

```js
(await fetch('/api/auth/session')).json().then(d => console.log(d.accessToken))
```

4. Copy the printed token

## Usage

```bash
# Basic export
chatgpt-export --token "YOUR_TOKEN"

# Enterprise/team account
chatgpt-export --token "YOUR_TOKEN" --workspace-id "YOUR_WORKSPACE_ID"

# Custom output directory
chatgpt-export --token "YOUR_TOKEN" --output-dir ./my-export

# Resume an interrupted export
chatgpt-export --token "YOUR_TOKEN" --resume

# Only export project conversations (skip root)
chatgpt-export --token "YOUR_TOKEN" --skip-root

# Slower rate limit to avoid throttling
chatgpt-export --token "YOUR_TOKEN" --rate-limit 2.0
```

## Output structure

```
chatgpt-export-output/
├── _root/                              # Non-project conversations
│   └── Some Chat [a1b2c3d4].md
├── My Research Project/                # One folder per ChatGPT project
│   └── Chat About X [e5f6g7h8].md
└── .export-state.json                  # Resume checkpoint
```
