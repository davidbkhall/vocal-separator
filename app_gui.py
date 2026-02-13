#!/usr/bin/env python3
"""
Vocal Separator – macOS GUI
Main page: file selection, output dir, start/stop, progress.
Settings page: API key, Audioshake params, logging.
"""

import json
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Load .env before importing separator (so API key is in environment)
from dotenv import load_dotenv

# When bundled (py2app or PyInstaller), use Application Support so config is writable
if getattr(sys, "frozen", False):
    _app_support = Path.home() / "Library" / "Application Support" / "VocalSeparator"
    _app_support.mkdir(parents=True, exist_ok=True)
    SCRIPT_DIR = _app_support
else:
    SCRIPT_DIR = Path(__file__).parent.resolve()

load_dotenv(SCRIPT_DIR / ".env")

from separator import (  # noqa: E402 (load_dotenv must run first)
    VALID_EXTENSIONS,
    check_api_key,
    is_valid_audio_file,
    separate_file,
)

CONFIG_PATH = SCRIPT_DIR / "gui_config.json"
LOG_DIR = SCRIPT_DIR / "logs"


def ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def load_config() -> dict:
    """Load GUI config (API key stored in .env; rest in gui_config.json)."""
    api_key = os.getenv("AUDIOSHAKE_API_KEY", "")
    data: dict = {
        "api_key": api_key,
        "format": "vocals",
        "job_name": "vocal-separation",
        "log_enabled": False,
        "log_path": str(ensure_log_dir() / "vocal_separator.log"),
    }
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                saved = json.load(f)
            data.update({k: v for k, v in saved.items() if k != "api_key"})
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_config(
    api_key: str, format_val: str, job_name: str, log_enabled: bool, log_path: str
) -> None:
    """Save API key to .env and other settings to gui_config.json."""
    env_path = SCRIPT_DIR / ".env"
    lines: list[str] = []
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip().startswith("AUDIOSHAKE_API_KEY="):
                    lines.append(line.rstrip())
    lines.append(f"AUDIOSHAKE_API_KEY={api_key}")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.environ["AUDIOSHAKE_API_KEY"] = api_key

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "format": format_val,
                "job_name": job_name,
                "log_enabled": log_enabled,
                "log_path": log_path,
            },
            f,
            indent=2,
        )


def find_audio_files(path: Path, recursive: bool = True) -> list[Path]:
    """Collect audio files from a file or directory."""
    if path.is_file():
        return [path] if is_valid_audio_file(path) else []
    files: list[Path] = []
    for ext in VALID_EXTENSIONS:
        if recursive:
            files.extend(path.rglob(f"*{ext}"))
            files.extend(path.rglob(f"*{ext.upper()}"))
        else:
            files.extend(path.glob(f"*{ext}"))
            files.extend(path.glob(f"*{ext.upper()}"))
    return sorted(set(files))


class ProgressQueue:
    """Thread-safe queue for progress updates from worker to GUI."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()

    def put(self, kind: str, **kwargs: object) -> None:
        self._queue.put((kind, kwargs))

    def get_nowait(self) -> tuple[str, dict] | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None


def run_batch(
    files: list[Path],
    output_dir: Path,
    cancel_event: threading.Event,
    progress_queue: ProgressQueue,
    format_val: str,
    job_name: str,
    log_path: str | None,
    log_enabled: bool,
) -> None:
    """Worker: process files one by one, post progress, respect cancel."""
    total = len(files)
    for i, path in enumerate(files):
        if cancel_event.is_set():
            progress_queue.put("cancelled", index=i, total=total)
            return
        progress_queue.put("start_file", index=i, total=total, filename=path.name)
        try:
            success = separate_file(
                path,
                output_dir,
                quiet=True,
                cancel_check=cancel_event.is_set,
                format=format_val,
                name=job_name,
            )
            if cancel_event.is_set():
                progress_queue.put("cancelled", index=i, total=total)
                return
            status = "Success" if success else "Failed"
            progress_queue.put("done_file", index=i, total=total, filename=path.name, status=status)
            if log_enabled and log_path:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"{path.name}\t{status}\n")
        except Exception as e:
            progress_queue.put(
                "done_file",
                index=i,
                total=total,
                filename=path.name,
                status=f"Error: {e!s}",
            )
            if log_enabled and log_path:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"{path.name}\tError: {e}\n")
    progress_queue.put("finished", total=total)


class VocalSeparatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Vocal Separator")
        self.root.minsize(640, 480)
        self.root.geometry("800x560")

        self.config = load_config()
        self.file_list: list[Path] = []
        self.cancel_event = threading.Event()
        self.progress_queue = ProgressQueue()
        self.worker_thread: threading.Thread | None = None
        self.poll_id: str | None = None

        self._build_ui()
        self._poll_progress()
        self.root.after(100, self._add_pending_paths)

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._build_main_tab()
        self._build_settings_tab()

    def _build_main_tab(self):
        main = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(main, text="Main")

        # Input files
        ttk.Label(main, text="Input files").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        list_frame = ttk.Frame(main)
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 4))
        self.file_listbox = tk.Listbox(list_frame, height=8, selectmode=tk.EXTENDED, font=("", 11))
        scroll = ttk.Scrollbar(list_frame)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scroll.set)
        scroll.config(command=self.file_listbox.yview)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))
        ttk.Button(btn_frame, text="Add files…", command=self._add_files).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Add folder…", command=self._add_folder).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Remove selected", command=self._remove_selected).pack(
            side=tk.LEFT
        )

        # Output directory
        ttk.Label(main, text="Output directory").grid(row=3, column=0, sticky=tk.W)
        out_frame = ttk.Frame(main)
        out_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 12))
        self.output_var = tk.StringVar(value=str(SCRIPT_DIR / "output"))
        ttk.Entry(out_frame, textvariable=self.output_var, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6)
        )
        ttk.Button(out_frame, text="Browse…", command=self._browse_output).pack(side=tk.LEFT)

        # Progress
        ttk.Label(main, text="Progress").grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(8, 0)
        )
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            main, variable=self.progress_var, maximum=100, length=400
        )
        self.progress_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=4)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main, textvariable=self.status_var).grid(
            row=7, column=0, columnspan=2, sticky=tk.W
        )

        # Per-file status
        ttk.Label(main, text="File status").grid(
            row=8, column=0, columnspan=2, sticky=tk.W, pady=(12, 0)
        )
        tree_frame = ttk.Frame(main)
        tree_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=4)
        self.tree = ttk.Treeview(tree_frame, columns=("status",), show="tree headings", height=6)
        self.tree.heading("#0", text="File")
        self.tree.heading("status", text="Status")
        self.tree.column("#0", width=320)
        self.tree.column("status", width=120)
        tree_scroll = ttk.Scrollbar(tree_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.config(yscrollcommand=tree_scroll.set)
        tree_scroll.config(command=self.tree.yview)

        main.rowconfigure(9, weight=1)
        main.columnconfigure(0, weight=1)

        # Start / Stop
        action_frame = ttk.Frame(main)
        action_frame.grid(row=10, column=0, columnspan=2, pady=12)
        self.start_btn = ttk.Button(action_frame, text="Start", command=self._start)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.stop_btn = ttk.Button(action_frame, text="Stop", command=self._stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

    def _build_settings_tab(self):
        sett = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(sett, text="Settings")

        row = 0
        ttk.Label(sett, text="API key").grid(row=row, column=0, sticky=tk.W)
        self.api_key_var = tk.StringVar(value=self.config.get("api_key", ""))
        ttk.Entry(sett, textvariable=self.api_key_var, show="•", width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(8, 0), pady=4
        )
        row += 1

        ttk.Label(sett, text="Format").grid(row=row, column=0, sticky=tk.W)
        self.format_var = tk.StringVar(value=self.config.get("format", "vocals"))
        ttk.Entry(sett, textvariable=self.format_var, width=30).grid(
            row=row, column=1, sticky=tk.W, padx=(8, 0), pady=4
        )
        ttk.Label(sett, text="(e.g. vocals)").grid(row=row, column=2, sticky=tk.W, padx=(8, 0))
        row += 1

        ttk.Label(sett, text="Job name").grid(row=row, column=0, sticky=tk.W)
        self.job_name_var = tk.StringVar(value=self.config.get("job_name", "vocal-separation"))
        ttk.Entry(sett, textvariable=self.job_name_var, width=30).grid(
            row=row, column=1, sticky=tk.W, padx=(8, 0), pady=4
        )
        row += 1

        self.log_enabled_var = tk.BooleanVar(value=self.config.get("log_enabled", False))
        ttk.Checkbutton(sett, text="Enable log file", variable=self.log_enabled_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=8
        )
        row += 1

        ttk.Label(sett, text="Log file path").grid(row=row, column=0, sticky=tk.W)
        self.log_path_var = tk.StringVar(value=self.config.get("log_path", ""))
        log_frame = ttk.Frame(sett)
        log_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=4)
        ttk.Entry(log_frame, textvariable=self.log_path_var, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6)
        )
        ttk.Button(log_frame, text="Browse…", command=self._browse_log_path).pack(side=tk.LEFT)
        row += 1

        sett.columnconfigure(1, weight=1)
        ttk.Button(sett, text="Save settings", command=self._save_settings).grid(
            row=row, column=0, columnspan=2, pady=16
        )

    def _add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select audio files",
            filetypes=[("Audio", "*.mp3 *.wav *.flac *.m4a *.ogg *.aac *.wma"), ("All", "*.*")],
        )
        for p in paths:
            path = Path(p)
            if path not in self.file_list and is_valid_audio_file(path):
                self.file_list.append(path)
                self.file_listbox.insert(tk.END, path.name)

    def _add_pending_paths(self) -> None:
        """Add paths passed via argv (e.g. when files are dropped onto the app)."""
        for arg in sys.argv[1:]:
            p = Path(arg)
            if not p.exists():
                continue
            if p.is_file() and is_valid_audio_file(p):
                if p not in self.file_list:
                    self.file_list.append(p)
                    self.file_listbox.insert(tk.END, p.name)
            elif p.is_dir():
                for f in find_audio_files(p):
                    if f not in self.file_list:
                        self.file_list.append(f)
                        self.file_listbox.insert(tk.END, f.name)

    def _add_folder(self) -> None:
        path = filedialog.askdirectory(title="Select folder")
        if not path:
            return
        root_path = Path(path)
        added = 0
        for p in find_audio_files(root_path):
            if p not in self.file_list:
                self.file_list.append(p)
                self.file_listbox.insert(tk.END, p.name)
                added += 1
        if added:
            self.status_var.set(f"Added {added} file(s) from folder")

    def _remove_selected(self) -> None:
        sel = list(self.file_listbox.curselection())
        for i in reversed(sel):
            self.file_listbox.delete(i)
            self.file_list.pop(i)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Output directory")
        if path:
            self.output_var.set(path)

    def _browse_log_path(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Log file",
            defaultextension=".log",
            initialdir=ensure_log_dir(),
        )
        if path:
            self.log_path_var.set(path)

    def _save_settings(self) -> None:
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Settings", "API key is required.")
            return
        save_config(
            api_key,
            self.format_var.get().strip() or "vocals",
            self.job_name_var.get().strip() or "vocal-separation",
            self.log_enabled_var.get(),
            self.log_path_var.get().strip() or str(ensure_log_dir() / "vocal_separator.log"),
        )
        self.config = load_config()
        messagebox.showinfo("Settings", "Settings saved.")

    def _start(self) -> None:
        if not self.file_list:
            messagebox.showwarning("Main", "Add at least one file or folder.")
            return
        output_str = self.output_var.get().strip()
        if not output_str:
            messagebox.showwarning("Main", "Choose an output directory.")
            return
        output_dir = Path(output_str)
        if not check_api_key():
            messagebox.showerror("Main", "API key not set. Open Settings and save your API key.")
            return
        output_dir.mkdir(parents=True, exist_ok=True)

        self.cancel_event.clear()
        self.progress_var.set(0.0)
        self.status_var.set("Starting…")
        for item in self.tree.get_children():
            self.tree.delete(item)
        for f in self.file_list:
            self.tree.insert("", tk.END, text=f.name, values=("—",))

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        log_path = self.log_path_var.get().strip() if self.log_enabled_var.get() else None
        if log_path and self.log_enabled_var.get():
            ensure_log_dir()
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n--- Session ---\n")

        self.worker_thread = threading.Thread(
            target=run_batch,
            args=(
                list(self.file_list),
                output_dir,
                self.cancel_event,
                self.progress_queue,
                self.format_var.get().strip() or "vocals",
                self.job_name_var.get().strip() or "vocal-separation",
                log_path,
                self.log_enabled_var.get(),
            ),
            daemon=True,
        )
        self.worker_thread.start()

    def _stop(self) -> None:
        self.cancel_event.set()
        self.status_var.set("Stopping…")

    def _poll_progress(self) -> None:
        done = False
        while True:
            msg = self.progress_queue.get_nowait()
            if msg is None:
                break
            kind, data = msg
            if kind == "start_file":
                idx = data["index"]
                total = data["total"]
                self.progress_var.set(100.0 * idx / total if total else 0)
                self.status_var.set(f"Processing {data['filename']}…")
            elif kind == "done_file":
                idx = data["index"]
                total = data["total"]
                status = data.get("status", "Done")
                children = self.tree.get_children()
                if idx < len(children):
                    self.tree.item(children[idx], values=(status,))
                self.progress_var.set(100.0 * (idx + 1) / total if total else 100)
                self.status_var.set(f"Completed {idx + 1} / {total}")
            elif kind == "cancelled":
                self.status_var.set("Cancelled")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                done = True
                break
            elif kind == "finished":
                self.status_var.set(f"Finished — {data['total']} file(s) processed")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                done = True
                break
        if not done:
            self.poll_id = self.root.after(200, self._poll_progress)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = VocalSeparatorApp()
    app.run()


if __name__ == "__main__":
    main()
