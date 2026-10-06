"""Interfaccia grafica (Tkinter) per cercare bandi TED su calzature per
vigili del fuoco, polizia e soccorso, e generare un report.

Pensata per essere compilata in un .exe standalone con PyInstaller
(vedi build_windows.bat / .github/workflows/build-windows.yml).
"""

from __future__ import annotations

import datetime as dt
import os
import platform
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk

from ted_tenders import config
from ted_tenders.classify import categorize
from ted_tenders.client import TedApiError, TedClient
from ted_tenders.models import Notice
from ted_tenders.query_builder import build_query
from ted_tenders.report import write_report
from ted_tenders.storage import append_notices

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "notices.csv"
REPORT_PATH = DATA_DIR / "report.md"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bandi TED — Calzature Vigili del Fuoco / Polizia / Soccorso")
        self.geometry("780x560")
        self.minsize(640, 420)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self._build_widgets()
        self.after(100, self._drain_log_queue)

    # --- interfaccia -----------------------------------------------------

    def _build_widgets(self):
        pad = {"padx": 8, "pady": 6}

        params = ttk.LabelFrame(self, text="Parametri di ricerca")
        params.pack(fill="x", **pad)

        ttk.Label(params, text="Giorni indietro:").grid(row=0, column=0, sticky="w", **pad)
        self.days_var = tk.StringVar(value=str(config.DEFAULTS.days_back))
        ttk.Entry(params, textvariable=self.days_var, width=8).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(params, text="Paesi (es. IT,FR,DE — vuoto = tutti):").grid(
            row=0, column=2, sticky="w", **pad
        )
        self.countries_var = tk.StringVar(value="")
        ttk.Entry(params, textvariable=self.countries_var, width=24).grid(
            row=0, column=3, sticky="w", **pad
        )

        ttk.Label(params, text="Modalità:").grid(row=1, column=0, sticky="w", **pad)
        self.mode_var = tk.StringVar(value=config.DEFAULTS.mode)
        ttk.Radiobutton(params, text="Ampia (più risultati)", value="broad", variable=self.mode_var).grid(
            row=1, column=1, sticky="w", **pad
        )
        ttk.Radiobutton(
            params, text="Stretta (meno falsi positivi)", value="strict", variable=self.mode_var
        ).grid(row=1, column=2, sticky="w", **pad)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", **pad)

        self.search_btn = ttk.Button(buttons, text="Cerca su TED", command=self.on_search)
        self.search_btn.pack(side="left", padx=4)

        self.report_btn = ttk.Button(buttons, text="Genera report", command=self.on_report)
        self.report_btn.pack(side="left", padx=4)

        self.open_folder_btn = ttk.Button(buttons, text="Apri cartella dati", command=self.on_open_folder)
        self.open_folder_btn.pack(side="left", padx=4)

        self.log = scrolledtext.ScrolledText(self, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, **pad)

        self.status_var = tk.StringVar(value="Pronto.")
        ttk.Label(self, textvariable=self.status_var, anchor="w").pack(fill="x", padx=8, pady=(0, 6))

        self._log(
            "Benvenuto. Imposta i parametri e premi 'Cerca su TED' per scaricare i bandi, "
            "oppure 'Genera report' per aggiornare il riepilogo da quelli già salvati."
        )

    # --- utilità log / thread --------------------------------------------

    def _log(self, message: str):
        self.log_queue.put(message)

    def _drain_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log.configure(state="normal")
                self.log.insert("end", message + "\n")
                self.log.see("end")
                self.log.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _set_busy(self, busy: bool, status: str = ""):
        state = "disabled" if busy else "normal"
        self.search_btn.configure(state=state)
        self.report_btn.configure(state=state)
        if status:
            self.status_var.set(status)

    # --- azioni ------------------------------------------------------------

    def on_search(self):
        try:
            days_back = int(self.days_var.get())
        except ValueError:
            self._log("Errore: 'Giorni indietro' deve essere un numero intero.")
            return
        countries = [c.strip().upper() for c in self.countries_var.get().split(",") if c.strip()]
        mode = self.mode_var.get()

        self._set_busy(True, "Ricerca su TED in corso…")
        threading.Thread(target=self._run_search, args=(days_back, countries, mode), daemon=True).start()

    def _run_search(self, days_back: int, countries: list[str], mode: str):
        try:
            date_to = dt.date.today()
            date_from = date_to - dt.timedelta(days=days_back)
            query = build_query(mode=mode, date_from=date_from, date_to=date_to, countries=countries)
            self._log(f"Query TED ({mode}):\n  {query}\n")

            client = TedClient()
            notices = []
            for raw in client.search_all(query):
                n = Notice.from_raw(raw)
                n.category = categorize(n.title)
                notices.append(n)
                if len(notices) % 25 == 0:
                    self._log(f"  ...{len(notices)} bandi scaricati finora")

            added = append_notices(CSV_PATH, notices)
            self._log(
                f"\nFatto. Bandi trovati: {len(notices)} — nuovi salvati in {CSV_PATH}: {added}"
            )
            self._set_busy(False, f"Ricerca completata: {added} nuovi bandi.")
        except TedApiError as exc:
            self._log(f"\nErrore nella ricerca TED: {exc}")
            self._set_busy(False, "Errore nella ricerca. Vedi il log sopra.")
        except Exception as exc:  # noqa: BLE001 - mostra qualunque errore nell'interfaccia
            self._log(f"\nErrore inatteso: {exc}")
            self._set_busy(False, "Errore inatteso. Vedi il log sopra.")

    def on_report(self):
        self._set_busy(True, "Generazione report…")
        threading.Thread(target=self._run_report, daemon=True).start()

    def _run_report(self):
        try:
            report = write_report(CSV_PATH, REPORT_PATH)
            self._log(report)
            self._log(f"Report salvato in {REPORT_PATH}")
            self._set_busy(False, "Report generato.")
        except Exception as exc:  # noqa: BLE001
            self._log(f"Errore nella generazione del report: {exc}")
            self._set_busy(False, "Errore nella generazione del report.")

    def on_open_folder(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path = str(DATA_DIR.resolve())
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(path)  # type: ignore[attr-defined]
            elif system == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as exc:  # noqa: BLE001
            self._log(f"Non riesco ad aprire la cartella automaticamente ({exc}). Percorso: {path}")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
