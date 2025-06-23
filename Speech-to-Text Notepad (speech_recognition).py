import tkinter as tk
from tkinter import filedialog, messagebox
import speech_recognition as sr
import threading
import pyaudio
import numpy as np
import time

class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎙️ Speech-to-Text Notepad with Decibel Meter")
        self.root.geometry("600x550")
        self.root.resizable(False, False)

        tk.Label(root, text="Click below to record your voice:", font=("Arial", 12)).pack(pady=10)

        tk.Button(root, text="🎤 Start Listening", font=("Arial", 12), command=self.start_listening_thread).pack(pady=10)

        # Decibel meter
        self.db_label = tk.Label(root, text="Mic Level: 0 dB", font=("Arial", 10))
        self.db_label.pack()
        self.db_bar = tk.Canvas(root, width=300, height=20, bg="white", highlightthickness=1, highlightbackground="black")
        self.db_bar.pack(pady=5)
        self.db_rect = self.db_bar.create_rectangle(0, 0, 0, 20, fill="green")

        # Notepad
        self.text_area = tk.Text(root, wrap="word", font=("Consolas", 11))
        self.text_area.pack(expand=True, fill="both", padx=10, pady=10)

        # Menu
        menu = tk.Menu(root)
        root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="💾 Save As", command=self.save_text)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)

    def save_text(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.text_area.get("1.0", tk.END))
            messagebox.showinfo("Saved", "Note saved successfully.")

    def start_listening_thread(self):
        threading.Thread(target=self.record_and_transcribe, daemon=True).start()

    def record_and_transcribe(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        try:
            with mic as source:
                self.text_area.insert(tk.END, "\n🎧 Listening...\n")
                self.root.update()

                recognizer.adjust_for_ambient_noise(source)

                # Start decibel thread
                self.listening = True
                decibel_thread = threading.Thread(target=self.monitor_decibel_level, daemon=True)
                decibel_thread.start()

                audio = recognizer.listen(source, timeout=8)

                self.listening = False

            text = recognizer.recognize_google(audio)
            self.text_area.insert(tk.END, f"📝 {text}\n")

        except sr.UnknownValueError:
            self.text_area.insert(tk.END, "❌ Could not understand audio.\n")
        except sr.RequestError as e:
            self.text_area.insert(tk.END, f"❌ Could not request results; {e}\n")
        except Exception as e:
            self.text_area.insert(tk.END, f"❌ Error: {e}\n")
        finally:
            self.listening = False
            self.db_label.config(text="Mic Level: 0 dB")
            self.db_bar.coords(self.db_rect, 0, 0, 0, 20)

    def monitor_decibel_level(self):
        chunk = 1024
        rate = 44100
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, frames_per_buffer=chunk)
        try:
            while self.listening:
                data = np.frombuffer(stream.read(chunk, exception_on_overflow=False), dtype=np.int16)
                rms = np.sqrt(np.mean(np.square(data)))
                db = 20 * np.log10(rms + 1e-6)
                self.db_label.config(text=f"Mic Level: {int(db)} dB")
                bar_length = min(300, max(0, int((db + 60) * 3)))  # normalize from -60 to 40
                self.db_bar.coords(self.db_rect, 0, 0, bar_length, 20)
                self.db_bar.update()
                time.sleep(0.05)
        except Exception:
            pass
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    SpeechToTextApp(root)
    root.mainloop()
