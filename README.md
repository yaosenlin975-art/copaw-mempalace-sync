# CoPaw Mempalace Sync Plugin

A CoPaw plugin that automatically syncs conversations to [MemPalace](https://github.com/milla-jovovich/mempalace) for persistent memory across sessions.

## Features

- **Automatic Sync**: Conversations are synced to MemPalace after each reply
- **Background Processing**: Non-blocking async operation
- **Full-text Search**: Search your entire conversation history with semantic matching
- **Palace Structure**: Organized memory with wings, rooms, and drawers

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

### Option 1: Automatic Installation (Recommended)

```bash
cd copaw-mempalace-sync
python install.py
```

The installer will:
1. Copy the hook to CoPaw's hooks directory
2. Update `hooks/__init__.py` to export the hook
3. Patch `react_agent.py` to register the hook
4. Install the sync script

### Option 2: Manual Installation

1. **Copy the hook file:**
   ```bash
   copy hooks\mempalace_sync.py "D:\Program Files\CoPaw\Lib\site-packages\copaw\agents\hooks\"
   ```

2. **Update `hooks/__init__.py`:**
   ```python
   # Add import
   from .mempalace_sync import MempalaceSyncHook
   
   # Add to __all__
   __all__ = [
       "BootstrapHook",
       "MemoryCompactionHook",
       "MempalaceSyncHook",  # Add this line
   ]
   ```

3. **Patch `react_agent.py`:**
   ```python
   # Add import (around line 30)
   from .hooks import BootstrapHook, MemoryCompactionHook, MempalaceSyncHook
   
   # Add hook registration (after memory compaction hook, around line 445)
   mempalace_sync_hook = MempalaceSyncHook(
       workspace_dir=working_dir,
   )
   self.register_instance_hook(
       hook_type="post_reply",
       hook_name="mempalace_sync_hook",
       hook=mempalace_sync_hook.__call__,
   )
   logger.debug("Registered mempalace sync hook")
   ```

4. **Copy the sync script:**
   ```bash
   copy scripts\sync_mempalace.py "D:\Program Files\CoPaw\scripts\"
   ```

## Configuration

### Environment Variables (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_DIR` | `~/.copaw/workspaces/default` | CoPaw workspace directory |
| `PALACE_DIR` | `~/.mempalace/palace` | MemPalace palace directory |
| `MEMPALACE_VENV` | Auto-detected | Path to mempalace venv python |

### Custom Palace Directory

To use a custom palace directory, set the `PALACE_DIR` environment variable:

```bash
set PALACE_DIR=C:\path\to\your\palace
```

## Usage

### Automatic Operation

Once installed, the plugin works automatically. Just have conversations with your CoPaw agent, and they'll be synced to MemPalace.

### Manual Search

Search your conversation history:

```bash
# Activate your Python environment
cd C:\Users\Administrator\.copaw\workspaces\default
.venv\Scripts\activate

# Set palace directory
set PALACE_DIR=%USERPROFILE%\.mempalace\palace

# Search
mempalace search "what we discussed about project X"
mempalace search "error messages from last week"
mempalace search "user preferences"
```

### Check Status

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

### Hook Not Triggering

1. Check if CoPaw daemon was restarted after installation:
   ```bash
   copaw daemon restart
   ```

2. Check CoPaw logs for hook registration:
   ```
   INFO: Registered mempalace sync hook
   ```

### Sync Script Not Found

Ensure the sync script is in the correct location:
```
D:\Program Files\CoPaw\scripts\sync_mempalace.py
```

### MemPalace Not Found

Install MemPalace in your CoPaw virtual environment:
```bash
cd C:\Users\Administrator\.copaw\workspaces\default
.venv\Scripts\activate
pip install mempalace
```

### Encoding Errors

The script uses UTF-8 encoding. If you see encoding errors, ensure your environment supports UTF-8:
```bash
set PYTHONIOENCODING=utf-8
```

## File Structure

```
copaw-mempalace-sync/
├── README.md                 # This file
├── install.py                # Automatic installer
├── hooks/
│   └── mempalace_sync.py     # The post_reply hook
└── scripts/
    └── sync_mempalace.py     # Session sync script
```

## How the Hook Works

The `MempalaceSyncHook` is a `post_reply` hook that:

1. Triggers after each assistant reply
2. Runs asynchronously (non-blocking)
3. Calls `sync_mempalace.py` to:
   - Find the latest session file
   - Convert it to conversation format
   - Import it into MemPalace using `mempalace mine --mode convos`

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
