"""
Hermes CLI - Unified command-line interface for Hermes Agent.

Provides subcommands for:
- hermes chat          - Interactive chat (same as ./hermes)
- hermes gateway       - Run gateway in foreground
- hermes gateway start - Start gateway service
- hermes gateway stop  - Stop gateway service  
- hermes setup         - Interactive setup wizard
- hermes status        - Show status of all components
- hermes cron          - Manage cron jobs
"""

__version__ = "0.2.0"
__release_date__ = "2026.3.12"

# Enable ANSI escape codes on Windows cmd.exe (Windows 10+)
# Without this, color codes render as raw text like [35m [0m
import sys as _sys
if _sys.platform == "win32":
    try:
        import ctypes as _ct
        _k32 = _ct.windll.kernel32
        _h = _k32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        _m = _ct.c_ulong()
        _k32.GetConsoleMode(_h, _ct.byref(_m))
        _k32.SetConsoleMode(_h, _m.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass
