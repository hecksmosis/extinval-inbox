from __future__ import annotations

import importlib
import threading

from app.services.pipeline import ProcessingPipeline


def _ctk():
    if importlib.util.find_spec('customtkinter') is None:
        raise RuntimeError('customtkinter is required to launch the desktop UI.')
    return importlib.import_module('customtkinter')


class Dashboard:
    def __init__(self) -> None:
        ctk = _ctk()
        self._ctk = ctk
        self.root = ctk.CTk()
        self.root.title("Extinval Inbox Automation")
        self.root.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.pipeline = ProcessingPipeline()

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(self.root, text="Extinval Inbox Automation", font=ctk.CTkFont(size=28, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, padx=24, pady=(24, 8), sticky="w")

        controls = ctk.CTkFrame(self.root, corner_radius=14)
        controls.grid(row=1, column=0, padx=(24, 12), pady=16, sticky="ns")
        controls.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(controls, text="Operations", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")
        ctk.CTkButton(controls, text="Run inbox sync", command=self.run_sync).grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        ctk.CTkButton(controls, text="Open failure folder", command=lambda: self.log("Failures are stored in runtime/failures")).grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        ctk.CTkLabel(controls, text="Low-confidence or incomplete emails appear in the reporting store for manual review.", wraplength=240, justify="left").grid(row=3, column=0, padx=16, pady=8, sticky="w")

        summary = ctk.CTkTextbox(self.root, corner_radius=14)
        summary.grid(row=1, column=1, padx=(12, 24), pady=16, sticky="nsew")
        summary.insert("1.0", "System ready. Configure credentials and template assets, then run a sync.\n")
        summary.configure(state="disabled")
        self.summary = summary

    def log(self, message: str) -> None:
        self.summary.configure(state="normal")
        self.summary.insert("end", message + "\n")
        self.summary.see("end")
        self.summary.configure(state="disabled")

    def run_sync(self) -> None:
        thread = threading.Thread(target=self._run_sync_impl, daemon=True)
        thread.start()

    def _run_sync_impl(self) -> None:
        self.log("Starting inbox synchronization...")
        try:
            results = self.pipeline.run_once()
            self.log(f"Processed {len(results)} new emails.")
            for result in results:
                self.log(f"- {result.message_id}: request={result.is_product_request} lines={len(result.requested_lines)} confidence={result.confidence:.2f}")
        except Exception as exc:
            self.log(f"Error: {exc}")

    def mainloop(self) -> None:
        self.root.mainloop()


def launch_app() -> None:
    app = Dashboard()
    app.mainloop()
