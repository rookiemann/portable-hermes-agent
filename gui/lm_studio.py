"""
Hermes Agent - LM Studio Integration
SDK for model loading (GPU/context control), OpenAI endpoint for chat.
Pattern from AgentNate.
"""
import os
import sys
import json
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Dict, Optional

from gui.theme import C, FONTS, set_dark_title_bar, Tooltip

try:
    import lmstudio
    from lmstudio import LlmLoadModelConfig
    from lmstudio._sdk_models import GpuSetting
    HAS_SDK = True
except ImportError:
    lmstudio = None
    HAS_SDK = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

PROJECT_ROOT = Path(__file__).parent.parent

# ============================================================================
# GPU Detection
# ============================================================================

def get_available_gpus() -> List[str]:
    """Detect GPUs via nvidia-smi."""
    gpus = ["CPU"]
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True, timeout=10
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split(", ")
            if len(parts) >= 3:
                idx, name, mem = parts[0].strip(), parts[1].strip(), parts[2].strip()
                gpus.append(f"GPU {idx}: {name} ({mem} MiB)")
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass
    return gpus


# ============================================================================
# LM Studio Client
# ============================================================================

class LMStudioClient:
    """Manages LM Studio SDK connection, model loading, and OpenAI endpoint."""

    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.base_url = base_url
        self._sdk_client = None
        self._sdk_api_host = None

    def is_running(self) -> bool:
        """Check if LM Studio is reachable."""
        if not HAS_HTTPX:
            return False
        try:
            r = httpx.get(f"{self.base_url}/models", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def connect_sdk(self) -> bool:
        """Initialize SDK client."""
        if not HAS_SDK:
            return False
        try:
            self._sdk_api_host = lmstudio.Client.find_default_local_api_host()
            if self._sdk_api_host:
                self._sdk_client = lmstudio.Client(api_host=self._sdk_api_host)
                return True
        except Exception:
            pass
        return False

    def list_downloaded_models(self) -> List[Dict]:
        """List all downloaded models via SDK."""
        if not self._sdk_client:
            return []
        try:
            models = list(self._sdk_client.llm.list_downloaded())
            return [{"path": str(m)} for m in models]
        except Exception:
            return []

    def list_loaded_models(self) -> List[Dict]:
        """List currently loaded models via SDK."""
        if not self._sdk_client:
            return []
        try:
            models = list(self._sdk_client.llm.list_loaded())
            return [{"id": str(m)} for m in models]
        except Exception:
            return []

    def list_models_api(self) -> List[Dict]:
        """List models via OpenAI-compatible API."""
        if not HAS_HTTPX:
            return []
        try:
            # Try native API first (has context_length)
            native_url = self.base_url.replace("/v1", "") + "/api/v0/models"
            r = httpx.get(native_url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                models_list = data if isinstance(data, list) else data.get("data", [])
                return [
                    {
                        "id": m.get("id", m.get("path", "unknown")),
                        "context_length": m.get("max_context_length"),
                        "quantization": m.get("quantization"),
                        "state": m.get("state", "unknown"),
                    }
                    for m in models_list
                ]
        except Exception:
            pass

        try:
            # Fallback to OpenAI API
            r = httpx.get(f"{self.base_url}/models", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return [
                    {"id": m.get("id", "unknown"), "context_length": None, "state": "unknown"}
                    for m in data.get("data", [])
                ]
        except Exception:
            pass
        return []

    def load_model(self, model_path: str, gpu_index: Optional[int] = None,
                   context_length: int = 4096) -> bool:
        """Load a model via SDK with GPU and context control."""
        if not self._sdk_client:
            return False
        try:
            gpu_config = None
            if gpu_index is not None:
                gpus = get_available_gpus()
                num_gpus = len([g for g in gpus if g.startswith("GPU")])
                disabled = [i for i in range(num_gpus) if i != gpu_index]
                gpu_config = GpuSetting(
                    main_gpu=gpu_index,
                    disabled_gpus=disabled if disabled else None,
                    ratio=1.0,
                )

            config = LlmLoadModelConfig(
                gpu=gpu_config,
                context_length=context_length,
            )

            instance_id = f"hermes-{int(time.time())}"
            self._sdk_client.llm.load_new_instance(
                model_path, instance_id, config=config, ttl=3600
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def unload_model(self, model_id: str) -> bool:
        """Unload a model via SDK."""
        if not self._sdk_client:
            return False
        try:
            loaded = list(self._sdk_client.llm.list_loaded())
            for m in loaded:
                if model_id in str(m):
                    m.unload()
                    return True
        except Exception:
            pass
        return False


def estimate_context_length(model_id: str) -> int:
    """Estimate context length from model name."""
    m = model_id.lower()
    if "128k" in m: return 131072
    if "64k" in m: return 65536
    if "32k" in m: return 32768
    if "16k" in m: return 16384
    if "8k" in m: return 8192
    if "llama-3" in m or "llama3" in m: return 8192
    if "llama-2" in m: return 4096
    if "mistral" in m or "mixtral" in m: return 32768
    if "qwen" in m: return 32768
    if "phi" in m: return 16384
    if "gemma" in m: return 8192
    if "deepseek" in m: return 32768
    if "command-r" in m: return 128000
    return 4096


# ============================================================================
# LM Studio Panel (GUI)
# ============================================================================

class LMStudioPanel(tk.Toplevel):
    """Full LM Studio management panel — model browser, GPU selector, context slider."""

    def __init__(self, parent, on_model_ready=None):
        super().__init__(parent)
        self.on_model_ready = on_model_ready
        self.title("LM Studio - Local Models")
        self.geometry("650x580")
        self.configure(bg=C["bg_main"])
        self.transient(parent)
        set_dark_title_bar(self)
        from gui.theme import center_window
        center_window(self, 650, 580, parent)

        self.client = LMStudioClient()
        self.gpus = get_available_gpus()
        self.models = []

        self._build_ui()
        self.after(100, self._connect)

    def _build_ui(self):
        # Title
        hdr = tk.Frame(self, bg=C["bg_main"], padx=20, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="LM Studio", font=FONTS["title"],
                fg=C["accent"], bg=C["bg_main"]).pack(side="left")

        self.status_dot = tk.Label(hdr, text="\u25CF", font=("Segoe UI", 12),
                                  fg=C["text_disabled"], bg=C["bg_main"])
        self.status_dot.pack(side="left", padx=(8, 4))
        self.status_lbl = tk.Label(hdr, text="Connecting...", font=FONTS["small"],
                                  fg=C["text_hint"], bg=C["bg_main"])
        self.status_lbl.pack(side="left")

        if not HAS_SDK:
            tk.Label(hdr, text="(SDK not installed)", font=FONTS["small"],
                    fg=C["danger"], bg=C["bg_main"]).pack(side="right")

        # Model list
        model_frame = tk.LabelFrame(self, text="  Available Models  ",
                                    bg=C["bg_main"], fg=C["text_secondary"],
                                    font=FONTS["subheading"], padx=12, pady=8)
        model_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self.model_list = tk.Listbox(model_frame, bg=C["bg_input"], fg=C["text_primary"],
                                     font=FONTS["mono_small"], relief="flat",
                                     selectbackground=C["accent"],
                                     selectforeground="white",
                                     highlightthickness=0, borderwidth=0)
        sb = ttk.Scrollbar(model_frame, command=self.model_list.yview)
        self.model_list.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.model_list.pack(fill="both", expand=True)
        self.model_list.bind("<<ListboxSelect>>", self._on_model_select)

        # Controls frame
        ctrl = tk.Frame(self, bg=C["bg_main"], padx=20)
        ctrl.pack(fill="x")

        # GPU selector
        gpu_row = tk.Frame(ctrl, bg=C["bg_main"])
        gpu_row.pack(fill="x", pady=4)
        tk.Label(gpu_row, text="GPU:", font=FONTS["body"],
                fg=C["text_secondary"], bg=C["bg_main"], width=12,
                anchor="w").pack(side="left")
        self.gpu_var = tk.StringVar()
        self.gpu_combo = ttk.Combobox(gpu_row, textvariable=self.gpu_var,
                                      values=self.gpus, font=FONTS["small"],
                                      state="readonly")
        if len(self.gpus) > 1:
            self.gpu_combo.current(1)  # Default to first GPU
        else:
            self.gpu_combo.current(0)
        self.gpu_combo.pack(side="left", fill="x", expand=True)

        # Context length slider
        ctx_row = tk.Frame(ctrl, bg=C["bg_main"])
        ctx_row.pack(fill="x", pady=4)
        tk.Label(ctx_row, text="Context:", font=FONTS["body"],
                fg=C["text_secondary"], bg=C["bg_main"], width=12,
                anchor="w").pack(side="left")

        self.ctx_var = tk.IntVar(value=4096)
        self.ctx_slider = ttk.Scale(ctx_row, from_=512, to=131072,
                                    variable=self.ctx_var, orient="horizontal",
                                    command=self._on_ctx_change)
        self.ctx_slider.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.ctx_label = tk.Label(ctx_row, text="4,096", font=FONTS["mono_small"],
                                 fg=C["accent"], bg=C["bg_main"], width=10)
        self.ctx_label.pack(side="right")

        # Buttons
        btn_row = tk.Frame(self, bg=C["bg_main"], padx=20, pady=12)
        btn_row.pack(fill="x")

        self.load_btn = ttk.Button(btn_row, text="Load Model", style="Primary.TButton",
                                   command=self._load_model)
        self.load_btn.pack(side="left", padx=(0, 8))

        self.unload_btn = ttk.Button(btn_row, text="Unload", style="Danger.TButton",
                                     command=self._unload_model)
        self.unload_btn.pack(side="left", padx=(0, 8))

        ttk.Button(btn_row, text="Refresh", style="TButton",
                   command=self._refresh_models).pack(side="left", padx=(0, 8))

        self.use_btn = ttk.Button(btn_row, text="Use for Chat", style="Primary.TButton",
                                  command=self._use_model)
        self.use_btn.pack(side="right")

    def _connect(self):
        """Connect to LM Studio in background."""
        def _do():
            running = self.client.is_running()
            sdk_ok = False
            if running and HAS_SDK:
                sdk_ok = self.client.connect_sdk()
            self.after(0, lambda: self._on_connected(running, sdk_ok))

        threading.Thread(target=_do, daemon=True).start()

    def _on_connected(self, running, sdk_ok):
        if running:
            self.status_dot.configure(fg=C["success"])
            status = "Connected"
            if sdk_ok:
                status += " (SDK active)"
            self.status_lbl.configure(text=status)
            self._refresh_models()
        else:
            self.status_dot.configure(fg=C["danger"])
            self.status_lbl.configure(text="Not running — start LM Studio first")

    def _refresh_models(self):
        """Refresh model list."""
        def _do():
            models = self.client.list_models_api()
            if HAS_SDK and self.client._sdk_client:
                try:
                    downloaded = self.client.list_downloaded_models()
                    # Merge downloaded models not in API list
                    api_ids = {m["id"] for m in models}
                    for d in downloaded:
                        if d["path"] not in api_ids:
                            models.append({
                                "id": d["path"],
                                "context_length": None,
                                "state": "not-loaded",
                            })
                except Exception:
                    pass
            self.after(0, lambda: self._display_models(models))

        threading.Thread(target=_do, daemon=True).start()

    def _display_models(self, models):
        self.models = models
        self.model_list.delete(0, "end")
        for m in models:
            mid = m["id"]
            state = m.get("state", "")
            ctx = m.get("context_length")
            label = mid
            if state == "loaded":
                label = f"[LOADED] {mid}"
            if ctx:
                label += f"  ({ctx:,} ctx)"
            self.model_list.insert("end", label)

    def _on_model_select(self, event):
        sel = self.model_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.models):
            m = self.models[idx]
            ctx = m.get("context_length") or estimate_context_length(m["id"])
            self.ctx_var.set(ctx)
            self.ctx_label.configure(text=f"{ctx:,}")
            self.ctx_slider.configure(to=max(ctx, 131072))

    def _on_ctx_change(self, val):
        v = int(float(val))
        # Snap to nearest 512
        v = max(512, (v // 512) * 512)
        self.ctx_label.configure(text=f"{v:,}")

    def _load_model(self):
        sel = self.model_list.curselection()
        if not sel:
            messagebox.showwarning("No Model", "Select a model first.", parent=self)
            return

        idx = sel[0]
        model = self.models[idx]
        model_id = model["id"]
        ctx = int(self.ctx_var.get())
        ctx = max(512, (ctx // 512) * 512)

        # Parse GPU selection
        gpu_str = self.gpu_var.get()
        gpu_index = None
        if gpu_str.startswith("GPU"):
            try:
                gpu_index = int(gpu_str.split(":")[0].replace("GPU ", ""))
            except ValueError:
                pass

        self.status_lbl.configure(text=f"Loading {model_id.split('/')[-1]}...")
        self.status_dot.configure(fg=C["warning_dark"])

        def _do():
            try:
                self.client.load_model(model_id, gpu_index=gpu_index,
                                       context_length=ctx)
                self.after(0, lambda: self._on_load_success(model_id))
            except Exception as e:
                self.after(0, lambda: self._on_load_error(str(e)))

        threading.Thread(target=_do, daemon=True).start()

    def _on_load_success(self, model_id):
        short = model_id.split("/")[-1] if "/" in model_id else model_id
        self.status_dot.configure(fg=C["success"])
        self.status_lbl.configure(text=f"Loaded: {short}")
        self._refresh_models()

    def _on_load_error(self, error):
        self.status_dot.configure(fg=C["danger"])
        self.status_lbl.configure(text="Load failed")
        messagebox.showerror("Load Error", error, parent=self)

    def _unload_model(self):
        sel = self.model_list.curselection()
        if not sel:
            return
        model = self.models[sel[0]]
        self.client.unload_model(model["id"])
        self.after(500, self._refresh_models)

    def _use_model(self):
        """Set LM Studio as the active provider for Hermes chat."""
        if self.on_model_ready:
            sel = self.model_list.curselection()
            model_id = self.models[sel[0]]["id"] if sel and sel[0] < len(self.models) else None
            self.on_model_ready(self.client.base_url, model_id)
        self.destroy()
