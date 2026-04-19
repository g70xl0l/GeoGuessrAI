import tkinter as tk
from tkinter import messagebox, scrolledtext
import io
import base64
import json
import requests
from PIL import ImageGrab

# Константы API
API_KEY = "" # Сюда вставь ключ от Google AI Studio (Gemini)
MODEL_NAME = "gemini-1.5-flash-8b" # Самая дешевая и быстрая модель с поддержкой зрения

class GeoGuessrHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GeoGuessr AI Helper")
        self.root.geometry("480x620")
        self.root.attributes("-topmost", True) # Окно поверх игры
        
        # Основной цвет фона
        self.bg_color = "#f4f6f8"
        self.root.configure(bg=self.bg_color)

        self.capture_area = None # (x, y, x2, y2)

        # Главный контейнер с отступами
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=25, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        header_label = tk.Label(main_frame, text="🌍 GeoGuessr AI", font=("Segoe UI", 20, "bold"), 
                                bg=self.bg_color, fg="#2c3e50")
        header_label.pack(pady=(0, 20))

        # Интерфейс: Ключ API
        api_frame = tk.Frame(main_frame, bg=self.bg_color)
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.api_label = tk.Label(api_frame, text="Ключ Gemini API:", font=("Segoe UI", 10, "bold"), 
                                  bg=self.bg_color, fg="#34495e")
        self.api_label.pack(anchor="w")
        
        # Стилизованное поле ввода
        self.api_entry = tk.Entry(api_frame, font=("Segoe UI", 10), width=45, show="*", 
                                  relief="solid", bd=1, highlightthickness=1, 
                                  highlightcolor="#3498db", highlightbackground="#bdc3c7")
        self.api_entry.pack(fill=tk.X, pady=(5, 0), ipady=4)
        self.api_entry.insert(0, API_KEY)

        # Интерфейс: Кнопки
        btn_frame = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_select = tk.Button(btn_frame, text="📸 1. Выделить область (Street View)", 
                                    command=self.start_selection, 
                                    bg="#e2e8f0", fg="#1e293b", font=("Segoe UI", 11, "bold"),
                                    relief="flat", cursor="hand2", pady=10, activebackground="#cbd5e1")
        self.btn_select.pack(fill=tk.X, pady=(0, 10))

        self.btn_analyze = tk.Button(btn_frame, text="🔍 2. ГДЕ Я? (Анализ)", 
                                     command=self.analyze_screen, state=tk.DISABLED, 
                                     bg="#95a5a6", fg="white", font=("Segoe UI", 12, "bold"),
                                     relief="flat", cursor="hand2", pady=12, activebackground="#27ae60")
        self.btn_analyze.pack(fill=tk.X)

        # Интерфейс: Текстовое поле для результата
        result_frame = tk.Frame(main_frame, bg=self.bg_color)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        self.result_label = tk.Label(result_frame, text="Вердикт ИИ:", font=("Segoe UI", 10, "bold"), 
                                     bg=self.bg_color, fg="#34495e")
        self.result_label.pack(anchor="w", pady=(0, 5))

        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Consolas", 10),
                                                     bg="#ffffff", fg="#2c3e50", relief="solid", bd=1,
                                                     padx=10, pady=10)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.insert(tk.END, "Ожидание...\n\n1. Нажмите первую кнопку и выделите игру.\n2. Нажмите кнопку 'ГДЕ Я?', чтобы получить ответ.")
        self.result_text.config(state=tk.DISABLED)

    def start_selection(self):
        """Открывает прозрачное окно для выделения области на экране"""
        self.root.withdraw()
        self.selector = tk.Toplevel()
        self.selector.attributes("-fullscreen", True)
        self.selector.attributes("-alpha", 0.3)
        self.selector.config(cursor="cross")
        
        self.canvas = tk.Canvas(self.selector, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.selector.bind("<Escape>", lambda e: self.cancel_selection())

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="#e74c3c", width=3)

    def on_move_press(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        if (x2 - x1) > 50 and (y2 - y1) > 50:
            self.capture_area = (x1, y1, x2, y2)
            # Включаем кнопку анализа и делаем её зеленой
            self.btn_analyze.config(state=tk.NORMAL, bg="#2ecc71")
            self.update_result_ui(f"✅ Область игры успешно захвачена!\nРазмер: {x2-x1}x{y2-y1} пикселей.\n\nНажмите '🔍 ГДЕ Я?' для анализа локации.")
        
        self.selector.destroy()
        self.root.deiconify()

    def cancel_selection(self):
        self.selector.destroy()
        self.root.deiconify()

    def update_result_ui(self, text):
        """Обновляет текст в окне результатов"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
        self.root.update()

    def analyze_screen(self):
        """Делает скриншот и отправляет его в API"""
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showerror("Ошибка", "Введите API ключ Gemini!")
            return

        self.update_result_ui("📸 Делаю скриншот...\n🤖 Отправляю нейросети на анализ, подождите пару секунд...")

        # 1. Делаем скриншот выделенной области
        try:
            # bbox=(left, top, right, bottom)
            screenshot = ImageGrab.grab(bbox=self.capture_area)
            
            # Сохраняем в буфер памяти
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            self.update_result_ui(f"❌ Ошибка при захвате экрана:\n{e}")
            return

        # 2. Отправляем в Gemini
        self.ask_gemini_vision(api_key, img_base64)

    def ask_gemini_vision(self, api_key, img_base64):
        """Отправляет картинку и промпт в Google Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
        
        # Специальный промпт для GeoGuessr
        prompt = (
            "Ты — грандмастер игры GeoGuessr. Внимательно изучи этот скриншот со Street View. "
            "Твоя задача — определить страну, а также максимально точно угадать город, поселок или конкретный регион. "
            "Ищи меты GeoGuessr: названия на вывесках, разметку на дороге, столбы, знаки (язык), сторону движения, "
            "растительность, цвет почвы, особенности архитектуры, или даже багажник Google-мобиля. "
            "Отвечай четко и структурированно на русском языке:\n"
            "🌍 СТРАНА: [Твой ответ]\n"
            "🏙 ГОРОД/ПОСЕЛОК: [Приблизительный или точный город, поселок, штат или регион]\n"
            "🎯 УВЕРЕННОСТЬ: [1-100%]\n"
            "🔎 ОБЪЯСНЕНИЕ: [Кратко перечисли 2-3 главные улики, которые ты заметил на фото]"
        )

        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": img_base64
                        }
                    }
                ]
            }]
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                self.update_result_ui(text)
            else:
                self.update_result_ui(f"❌ Ошибка API: {response.status_code}\n{response.text}")
        except Exception as e:
            self.update_result_ui(f"🌐 Сетевая ошибка:\n{e}")

if __name__ == "__main__":
    # Для работы требуются библиотеки: pip install pillow requests
    root = tk.Tk()
    app = GeoGuessrHelperApp(root)
    root.mainloop()
