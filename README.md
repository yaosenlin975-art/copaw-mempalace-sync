# CoPaw Mempalace Sync Plugin

A CoPaw plugin that automatically syncs conversations to [MemPalace](https://github.com/milla-jovovich/mempalace) for persistent memory across sessions.

## Features

- **Automatic Sync**: Conversations are synced to MemPalace after each reply
- **Background Processing**: Non-blocking async operation
- **Full-text Search**: Search your entire conversation history with semantic matching
- **Palace Structure**: Organized memory with wings, rooms, and drawers
- **Auto-Discovery**: Automatically finds your MemPalace installation
- **Persistent**: Survives CoPaw updates

## How It Works

```
User Conversation → CoPaw Agent → post_reply Hook → Sync Script → MemPalace
                                                              ↓
                                              Searchable Memory Palace
```

1. You have a conversation with your CoPaw agent
2. After each reply, the `post_reply` hook triggers
3. The hook exports the latest session and imports it into MemPalace
4. Future conversations can search this memory

## Prerequisites

- **Python 3.10+**
- **CoPaw** installed and configured
- **MemPalace** installed:
  ```bash
  pip install mempalace
  ```

## Installation

### Quick Install (Recommended)

```bash
git clone https://github.com/yaosenlin975-art/copaw-mempalace-sync.git
cd copaw-mempalace-sync
python install_persistent.py
```

The installer will:
1. Install the discovery module to Python's site-packages
2. Install the hook module to CoPaw
3. Create a `.pth` file for auto-loading
4. Optionally configure your MemPalace location

**To uninstall:**
```bash
python install_persistent.py --uninstall
```

## Palace Discovery

The plugin automatically finds your MemPalace palace directory using this priority:

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | `MEMPALACE_HOME` env var | System environment variable |
| 2 | `.mempalace.json` | Workspace config file |
| 3 | Auto-discovery | Via `pip show mempalace` |
| 4 | Common locations | `~/.mempalace/palace`, etc. |
| 5 | Default | `~/.mempalace/palace` |

### Option 1: Environment Variable (System-wide)

Set `MEMPALACE_HOME` to your mempalace directory:

**Windows:**
```cmd
# Set as system environment variable via System Properties
# Variable: MEMPALACE_HOME
# Value: C:\Users\YourName\.mempalace
```

**Linux/Mac:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export MEMPALACE_HOME="$HOME/.mempalace"
```

### Option 2: Workspace Config (Per-workspace)

Create `.mempalace.json` in your workspace directory:

```json
{
  "palace_dir": "C:\\Users\\YourName\\.mempalace\\palace"
}
```

### Option 3: Auto-Discovery (No Configuration)

If you installed mempalace in a standard location, the plugin will find it automatically. No configuration needed!

## Usage

### Automatic Operation

Once installed, the plugin works automatically. Just have conversations with your CoPaw agent, and they'll be synced to MemPalace.

### Manual Search

Search your conversation history:

```bash
# Activate your Python environment
cd WORKING_DIR
.venv\Scripts\activate

# Search (palace location is auto-discovered)
mempalace search "what we discussed about project X"
mempalace search "error messages from last week"
mempalace search "user preferences"
```

### Check Discovery Status

```bash
python -m palace_discovery
```

Output:
```
Palace directory: C:\Users\YourName\.mempalace\palace
Exists: True
Has drawers: True
MEMPALACE_HOME: C:\Users\YourName\.mempalace
Config file: C:\Users\YourName\.copaw\workspaces\default\.mempalace.json (exists: False)
```

### Check MemPalace Status

```bash
mempalace status
```

Output:
```
=======================================================
  MemPalace Status — 675 drawers
=======================================================

  WING: copaw_sessions
    ROOM: planning               167 drawers

  WING: mempalace
    ROOM: benchmarks             435 drawers
    ...
```

## Troubleshooting

### Palace Not Found

1. Check discovery status:
   ```bash
   python -m palace_discovery
   ```

2. Set explicit configuration:
   ```bash
   # Option A: Environment variable
   set MEMPALACE_HOME=C:\path\to\your\.mempalace

   # Option B: Workspace config
   echo {"palace_dir":"C:\\path\\to\\palace"} > .mempalace.json
   ```

### Hook Not Triggering

1. Restart CoPaw daemon:
   ```bash
   copaw daemon restart
   ```

2. Check CoPaw logs for hook registration:
   ```
   Registered mempalace sync hook (via monkey patch)
   ```

### MemPalace Not Installed

Install MemPalace in your Python environment:
```bash
pip install mempalace
```

### Encoding Errors

The script uses UTF-8 encoding. If you see encoding errors:
```bash
set PYTHONIOENCODING=utf-8
```

## File Structure

```
copaw-mempalace-sync/
├── README.md                     # This file
├── LICENSE
├── .gitignore
├── install.py                    # Direct patch installer (legacy)
├── install_persistent.py         # Persistent installer (recommended)
├── palace_discovery.py           # Palace discovery module
├── hooks/
│   └── mempalace_sync.py         # The post_reply hook
└── scripts/
    └── sync_mempalace.py         # Session sync script
```

## Persistence Explained

### Why `.pth` Files Survive Updates

Python's `.pth` file mechanism is a **Python feature**, not a CoPaw feature:

1. `.pth` files live in `site-packages/` (Python's module directory)
2. When you `pip install --upgrade copaw`, only the `copaw/` directory is replaced
3. `.pth` files in `site-packages/` are **not touched** by pip updates

### How It Works

```
Python starts
    ↓
.pth file imports palace_discovery.py
    ↓
Discovery module finds your MemPalace palace
    ↓
Hook monkey-patches CoPawAgent._register_hooks
    ↓
CoPaw starts with mempalace sync enabled
```

## Memory Retrieval Priority

When answering questions about past work, decisions, or context:

1. **First**: Search MemPalace (full conversation history)
   ```bash
   mempalace search "keyword"
   ```

2. **Second**: Use `memory_search` (curated long-term memory)
   - MEMORY.md and memory/*.md files

3. **Third**: Read daily notes
   - memory/YYYY-MM-DD.md files

**Principle**: MemPalace is full memory, MEMORY.md is curated memory. Full first, curated second.

## License

MIT

## Contributing

Pull requests welcome! Please ensure:
- Code follows existing style
- Tested on Windows 10/11
- No breaking changes to existing CoPaw functionality

## Credits

- [MemPalace](https://github.com/milla-jovovich/mempalace) - The memory system
- [CoPaw](https://copaw.agentscope.io/) - The AI agent platform
