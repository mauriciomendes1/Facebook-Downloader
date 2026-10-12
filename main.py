import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse

#biblioteca para usar o yt-dlp para baixar vídeos do facebook
import yt_dlp


#programa principal para baixar vídeos do facebook
class FacebookVideoDownloader:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Facebook Video Downloader")
		self.root.geometry("620x500")
		self.root.minsize(560, 480)
		self.root.configure(background="#F3F7F4")

		self.url = tk.StringVar()
		self.destination = tk.StringVar(value=str(Path.home() / "Downloads"))
		self.status = tk.StringVar(value="Pronto para baixar")
		self.progress = tk.DoubleVar(value=0)
		self._configure_styles()

		self._build_ui()

	def _configure_styles(self) -> None:
		style = ttk.Style(self.root)
		style.theme_use("clam")
		style.configure("App.TFrame", background="#F3F7F4")
		style.configure("Panel.TFrame", background="#FFFFFF")
		style.configure("Title.TLabel", background="#FFFFFF", foreground="#20382F", font=("Segoe UI", 19, "bold"))
		style.configure("Subtitle.TLabel", background="#FFFFFF", foreground="#718078", font=("Segoe UI", 10))
		style.configure("Field.TLabel", background="#FFFFFF", foreground="#34483F", font=("Segoe UI", 10, "bold"))
		style.configure("Status.TLabel", background="#FFFFFF", foreground="#718078", font=("Segoe UI", 10))
		style.configure("Success.TLabel", background="#FFFFFF", foreground="#28734F", font=("Segoe UI", 10, "bold"))
		style.configure("Error.TLabel", background="#FFFFFF", foreground="#B54747", font=("Segoe UI", 10, "bold"))
		style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#20382F", padding=8)
		style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
		style.configure("Accent.TButton", background="#477C66", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=(16, 9))
		style.map("Accent.TButton", background=[("active", "#386950"), ("disabled", "#A9BDB1")])
		style.configure("Download.Horizontal.TProgressbar", troughcolor="#DCE9DF", background="#4C9270", thickness=14)

	def _build_ui(self) -> None:
		frame = ttk.Frame(self.root, style="App.TFrame", padding=24)
		frame.pack(fill="both", expand=True)

		panel = ttk.Frame(frame, style="Panel.TFrame", padding=22)
		panel.pack(fill="both", expand=True)
		ttk.Label(panel, text="FACEBOOK DOWNLOADER", style="Title.TLabel").pack(anchor="w")
		
		ttk.Label(panel, text="Link do vídeo", style="Field.TLabel").pack(anchor="w")
		ttk.Entry(panel, textvariable=self.url).pack(fill="x", pady=(6, 14))

		ttk.Label(panel, text="Salvar em", style="Field.TLabel").pack(anchor="w")
		destination_row = ttk.Frame(panel, style="Panel.TFrame")
		destination_row.pack(fill="x", pady=(6, 18))
		ttk.Entry(destination_row, textvariable=self.destination).pack(side="left", fill="x", expand=True)
		ttk.Button(destination_row, text="Escolher...", command=self._choose_destination).pack(side="left", padx=(8, 0))

		self.download_button = ttk.Button(panel, text="Baixar vídeo", style="Accent.TButton", command=self._start_download)
		self.download_button.pack(anchor="e")

		ttk.Separator(panel).pack(fill="x", pady=(20, 14))
		ttk.Label(panel, text="Progresso", style="Field.TLabel").pack(anchor="w", pady=(0, 7))
		self.progressbar = ttk.Progressbar(panel, variable=self.progress, maximum=100, mode="determinate", style="Download.Horizontal.TProgressbar")
		self.progressbar.pack(fill="x", pady=(0, 9))
		self.status_label = ttk.Label(panel, textvariable=self.status, style="Status.TLabel", wraplength=500)
		self.status_label.pack(anchor="w")

	def _choose_destination(self) -> None:
		folder = filedialog.askdirectory(initialdir=self.destination.get())
		if folder:
			self.destination.set(folder)

	def _start_download(self) -> None:
		video_url = self.url.get().strip()
		host = (urlparse(video_url).hostname or "").lower()
		if urlparse(video_url).scheme not in {"http", "https"} or not (
			host == "facebook.com" or host.endswith(".facebook.com")
		):
			messagebox.showerror("Link inválido", "Informe um link válido do Facebook.")
			return

		destination = Path(self.destination.get()).expanduser()
		if not destination.is_dir():
			messagebox.showerror("Pasta inválida", "Escolha uma pasta de destino existente.")
			return

		self.download_button.configure(state="disabled")
		self.status.set("Iniciando download...")
		self.status_label.configure(style="Status.TLabel")
		self._set_progress(0, "Iniciando download...")
		threading.Thread(target=self._download, args=(video_url, destination), daemon=True).start()

	def _download(self, video_url: str, destination: Path) -> None:
		def progress_hook(data: dict) -> None:
			if data.get("status") == "downloading":
				percent = data.get("_percent")
				if percent is None:
					total = data.get("total_bytes") or data.get("total_bytes_estimate")
					if total:
						percent = data.get("downloaded_bytes", 0) * 100 / total
				label = data.get("_percent_str", "Baixando...").strip()
				self.root.after(0, self._set_progress, percent, f"Baixando... {label}")
			elif data.get("status") == "finished":
				self.root.after(0, self._set_progress, 100, "Download concluído. Finalizando arquivo...")

		options = {
			"outtmpl": str(destination / "%(title)s [%(id)s].%(ext)s"),
			"format": "best[ext=mp4]/best",
			"noplaylist": True,
			"progress_hooks": [progress_hook],
			"quiet": True,
			"no_warnings": True,
		}

		try:
			with yt_dlp.YoutubeDL(options) as downloader:
				downloader.download([video_url])
		except Exception as error:
			self.root.after(0, self._finish, f"Falha no download:\n{error}", False)
		else:
			self.root.after(0, self._finish, "Download concluído com sucesso.", True)

	def _set_progress(self, percent: float | None, message: str) -> None:
		self.status.set(message)
		if percent is None:
			if self.progressbar.cget("mode") != "indeterminate":
				self.progressbar.configure(mode="indeterminate")
				self.progressbar.start(12)
			return
		if self.progressbar.cget("mode") == "indeterminate":
			self.progressbar.stop()
			self.progressbar.configure(mode="determinate")
		self.progress.set(max(0, min(100, float(percent))))

	def _finish(self, message: str, success: bool) -> None:
		self._set_progress(100 if success else self.progress.get(), message)
		self.status_label.configure(style="Success.TLabel" if success else "Error.TLabel")
		self.download_button.configure(state="normal")
		if success:
			messagebox.showinfo("Concluído", message)
		else:
			messagebox.showerror("Erro no download", message)


def main() -> None:
	root = tk.Tk()
	FacebookVideoDownloader(root)
	root.mainloop()


if __name__ == "__main__":
	main()
