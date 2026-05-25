import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import requests
import csv
import os
from datetime import datetime
import difflib  # 🔥 NEW: Built-in library for Spell Checking!

try:
    from fpdf import FPDF

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class WeatherAppPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather App Pro")
        self.root.geometry("480x750")
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.api_key = "4956441210f8dd49dbd3c56236a172d5"
        self.history_file = "weather_history.csv"
        self.setup_file()

        # 🔥 NEW: Database of popular cities for Autocomplete & Spell Check
        self.popular_cities = [
            "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata",
            "Surat", "Pune", "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal",
            "London", "New York", "Tokyo", "Paris", "Dubai", "Singapore", "Sydney", "Toronto",
            "Berlin", "Madrid", "Rome", "Chicago", "Los Angeles", "Seoul", "Beijing", "Moscow"
        ]

        # --- Top Header ---
        top_bar = ctk.CTkFrame(root, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(15, 5))

        header_label = ctk.CTkLabel(top_bar, text="Weather Pro", font=("Roboto", 24, "bold"))
        header_label.pack(side="left")

        self.theme_switch = ctk.CTkSwitch(top_bar, text="Dark Mode", command=self.toggle_theme)
        self.theme_switch.pack(side="right")
        self.theme_switch.select()

        # --- Tabbed Interface ---
        self.tabview = ctk.CTkTabview(root, width=440, height=600, corner_radius=10)
        self.tabview.pack(padx=20, pady=5, fill="both", expand=True)

        self.tab1 = self.tabview.add("Current Weather")
        self.tab2 = self.tabview.add("5-Day Forecast")
        self.tab3 = self.tabview.add("History")

        # ==========================================
        #        TAB 1: CURRENT WEATHER
        # ==========================================

        search_frame = ctk.CTkFrame(self.tab1, fg_color="transparent")
        search_frame.pack(pady=(10, 5), fill="x", padx=10)

        self.city_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter city (e.g., Mumbai)", width=220, height=40,
                                       font=("Roboto", 14))
        self.city_entry.grid(row=0, column=0, padx=(0, 10))

        # 🔥 Bind key typing to the autocomplete function
        self.city_entry.bind("<KeyRelease>", self.update_suggestions)

        self.search_btn = ctk.CTkButton(search_frame, text="🔍 Search", width=100, height=40,
                                        font=("Roboto", 14, "bold"), command=self.fetch_weather)
        self.search_btn.grid(row=0, column=1)

        self.unit_var = ctk.StringVar(value="Metric (°C)")
        self.unit_switch = ctk.CTkSegmentedButton(self.tab1, values=["Metric (°C)", "Imperial (°F)"],
                                                  variable=self.unit_var, command=lambda
                _: self.fetch_weather() if self.city_entry.get() else None)
        self.unit_switch.pack(pady=(10, 15))

        # 🔥 NEW: Floating Autocomplete Frame (Hidden by default)
        self.suggestion_frame = ctk.CTkFrame(self.tab1, width=220, corner_radius=5, fg_color=("gray90", "gray25"))

        # Weather Display Frame
        self.result_frame = ctk.CTkFrame(self.tab1, corner_radius=15, fg_color=("gray85", "gray20"))
        self.result_frame.pack(pady=5, padx=20, fill="both", expand=True)

        self.icon_label = ctk.CTkLabel(self.result_frame, text="🌍", font=("Segoe UI Emoji", 70))
        self.icon_label.pack(pady=(15, 0))

        self.location_label = ctk.CTkLabel(self.result_frame, text="Search for a city", font=("Roboto", 22, "bold"))
        self.location_label.pack()

        self.temp_label = ctk.CTkLabel(self.result_frame, text="--°", font=("Roboto", 48, "bold"), text_color="#3498DB")
        self.temp_label.pack(pady=(5, 5))

        self.desc_label = ctk.CTkLabel(self.result_frame, text="--", font=("Roboto", 16, "italic"))
        self.desc_label.pack()

        stats_frame = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        stats_frame.pack(pady=20)

        self.feels_label = ctk.CTkLabel(stats_frame, text="Feels Like: --", font=("Roboto", 14))
        self.feels_label.grid(row=0, column=0, padx=15, pady=5)

        self.humidity_label = ctk.CTkLabel(stats_frame, text="Humidity: --", font=("Roboto", 14))
        self.humidity_label.grid(row=0, column=1, padx=15, pady=5)

        self.wind_label = ctk.CTkLabel(stats_frame, text="Wind: --", font=("Roboto", 14))
        self.wind_label.grid(row=1, column=0, columnspan=2, pady=(5, 0))

        self.update_time_label = ctk.CTkLabel(self.result_frame, text="Last Updated: --", font=("Roboto", 11),
                                              text_color="gray")
        self.update_time_label.pack(side="bottom", pady=10)

        # ==========================================
        #        TAB 2: 5-DAY FORECAST
        # ==========================================

        self.forecast_title = ctk.CTkLabel(self.tab2, text="Upcoming Weather", font=("Roboto", 20, "bold"))
        self.forecast_title.pack(pady=(10, 15))

        self.forecast_frames = []
        for i in range(5):
            f_frame = ctk.CTkFrame(self.tab2, height=60, corner_radius=8, fg_color=("gray85", "gray20"))
            f_frame.pack(fill="x", padx=20, pady=5)
            f_frame.pack_propagate(False)

            day_lbl = ctk.CTkLabel(f_frame, text="--", font=("Roboto", 16, "bold"), width=80, anchor="w")
            day_lbl.pack(side="left", padx=15)

            icon_lbl = ctk.CTkLabel(f_frame, text="➖", font=("Segoe UI Emoji", 24))
            icon_lbl.pack(side="left", padx=10)

            desc_lbl = ctk.CTkLabel(f_frame, text="--", font=("Roboto", 14), width=100)
            desc_lbl.pack(side="left", padx=10)

            temp_lbl = ctk.CTkLabel(f_frame, text="--°", font=("Roboto", 18, "bold"), text_color="#F39C12")
            temp_lbl.pack(side="right", padx=15)

            self.forecast_frames.append({"day": day_lbl, "icon": icon_lbl, "desc": desc_lbl, "temp": temp_lbl})

        # ==========================================
        #           TAB 3: HISTORY
        # ==========================================

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=25, font=("Roboto", 11))
        style.configure("Treeview.Heading", font=("Roboto", 12, "bold"))

        columns = ("Date", "City", "Temperature")
        self.tree = ttk.Treeview(self.tab3, columns=columns, show="headings", height=12)
        self.tree.heading("Date", text="Date/Time")
        self.tree.heading("City", text="City")
        self.tree.heading("Temperature", text="Temp")

        self.tree.column("Date", width=120, anchor="center")
        self.tree.column("City", width=140, anchor="center")
        self.tree.column("Temperature", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(15, 10))

        self.load_history()

        hist_btn_frame = ctk.CTkFrame(self.tab3, fg_color="transparent")
        hist_btn_frame.pack(pady=(5, 15))

        delete_btn = ctk.CTkButton(hist_btn_frame, text="Delete Selected", width=140, fg_color="#DC3545",
                                   hover_color="#C82333", command=self.delete_selected)
        delete_btn.grid(row=0, column=0, padx=10)

        export_btn = ctk.CTkButton(hist_btn_frame, text="📄 Export to PDF", width=140, fg_color="#6C757D",
                                   hover_color="#5A6268", command=self.export_pdf)
        export_btn.grid(row=0, column=1, padx=10)

        footer_label = ctk.CTkLabel(root, text="Developed by Durvesh Jadhav\nPython Programming Internship Project",
                                    font=("Roboto", 11), text_color="gray")
        footer_label.pack(side="bottom", pady=10)

    # --- AUTOCOMPLETE LOGIC ---
    def update_suggestions(self, event):
        # Hide dropdown if box is empty or special key pressed
        typed = self.city_entry.get().strip().title()
        if len(typed) < 1 or event.keysym in ["Return", "Tab", "Shift_L", "Shift_R"]:
            self.suggestion_frame.place_forget()
            return

        # Find matching cities
        matches = [city for city in self.popular_cities if city.startswith(typed)]

        # Clear old suggestions
        for widget in self.suggestion_frame.winfo_children():
            widget.destroy()

        # Show new suggestions
        if matches:
            # Place the frame exactly below the search entry
            self.suggestion_frame.place(x=10, y=55)
            self.suggestion_frame.lift()  # Keep it on top of other elements

            for city in matches[:4]:  # Show up to 4 suggestions
                btn = ctk.CTkButton(self.suggestion_frame, text=city, width=220, fg_color="transparent",
                                    text_color=("black", "white"), anchor="w",
                                    command=lambda c=city: self.select_suggestion(c))
                btn.pack(fill="x", pady=2, padx=2)
        else:
            self.suggestion_frame.place_forget()

    def select_suggestion(self, city):
        self.city_entry.delete(0, ctk.END)
        self.city_entry.insert(0, city)
        self.suggestion_frame.place_forget()
        self.fetch_weather()  # Automatically search when clicked!

    # --- Setup & Utilities ---
    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def setup_file(self):
        if not os.path.exists(self.history_file):
            with open(self.history_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "City", "Temperature"])

    def get_weather_emoji(self, icon_code):
        emoji_map = {
            "01d": "☀️", "01n": "🌙",
            "02d": "⛅", "02n": "☁️",
            "03d": "☁️", "03n": "☁️",
            "04d": "☁️", "04n": "☁️",
            "09d": "🌧️", "09n": "🌧️",
            "10d": "🌦️", "10n": "🌧️",
            "11d": "⛈️", "11n": "⛈️",
            "13d": "❄️", "13n": "❄️",
            "50d": "🌫️", "50n": "🌫️"
        }
        return emoji_map.get(icon_code, "🌍")

    # --- Core API Logic ---
    def fetch_weather(self):
        self.suggestion_frame.place_forget()  # Hide autocomplete if open

        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name.")
            return

        unit_choice = self.unit_var.get()
        api_units = "metric" if "Metric" in unit_choice else "imperial"
        temp_symbol = "°C" if api_units == "metric" else "°F"
        speed_symbol = "km/h" if api_units == "metric" else "mph"

        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units={api_units}"

        try:
            response = requests.get(current_url)
            data = response.json()

            # 🔥 UPDATED: Smart Error Handling based on API Status Codes
            api_code = str(data.get("cod", ""))

            if api_code != "200":
                if api_code == "401":
                    # API Key is invalid or pending activation
                    messagebox.showerror("API Pending",
                                         "Your API key is currently invalid or still activating. Please wait 1-2 hours for OpenWeatherMap to enable it.")

                elif api_code == "404":
                    # City not found - run the spell checker
                    close_matches = difflib.get_close_matches(city.title(), self.popular_cities, n=1, cutoff=0.6)

                    if close_matches:
                        suggestion = close_matches[0]
                        # Prevent infinite loop if the spelling is already exactly the same!
                        if city.title() == suggestion:
                            messagebox.showerror("Error", f"City '{city}' not found in the weather database.")
                            return

                        if messagebox.askyesno("City Not Found",
                                               f"Could not find '{city}'.\n\nDid you mean '{suggestion}'?"):
                            self.city_entry.delete(0, ctk.END)
                            self.city_entry.insert(0, suggestion)
                            self.fetch_weather()
                    else:
                        messagebox.showerror("Error", f"City not found: {data.get('message', 'Unknown error')}")
                else:
                    # Catch-all for any other weird errors
                    messagebox.showerror("Error", f"API Error {api_code}: {data.get('message', 'Unknown error')}")
                return

            self.location_label.configure(text=f"{data['name']}, {data['sys']['country']}")

            current_temp = int(data['main']['temp'])
            self.temp_label.configure(text=f"{current_temp}{temp_symbol}")

            desc = data['weather'][0]['description'].title()
            self.desc_label.configure(text=desc)

            icon_code = data['weather'][0]['icon']
            self.icon_label.configure(text=self.get_weather_emoji(icon_code))

            feels_like = int(data['main']['feels_like'])
            self.feels_label.configure(text=f"Feels Like: {feels_like}{temp_symbol}")

            humidity = data['main']['humidity']
            self.humidity_label.configure(text=f"Humidity: {humidity}%")

            wind_speed = data['wind']['speed']
            if api_units == "metric":
                wind_speed = round(wind_speed * 3.6, 1)
            self.wind_label.configure(text=f"Wind: {wind_speed} {speed_symbol}")

            update_time = datetime.now().strftime("%H:%M")
            self.update_time_label.configure(text=f"Last Updated: {update_time}")

            history_temp_string = f"{current_temp}{temp_symbol}"
            self.save_record(f"{data['name']}, {data['sys']['country']}", history_temp_string)

            self.fetch_forecast(data['name'], api_units, temp_symbol)  # Use exact API city name

        except requests.exceptions.RequestException:
            messagebox.showerror("Connection Error", "Please check your internet connection.")

    def fetch_forecast(self, city, api_units, temp_symbol):
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.api_key}&units={api_units}"
        try:
            response = requests.get(forecast_url)
            data = response.json()

            if data["cod"] != "200": return

            daily_forecasts = []
            seen_dates = set()

            for item in data['list']:
                dt_txt = item['dt_txt']
                date_obj = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%Y-%m-%d")

                if date_str not in seen_dates and ("12:00:00" in dt_txt or len(seen_dates) == 0):
                    seen_dates.add(date_str)

                    day_name = date_obj.strftime("%a")
                    temp = int(item['main']['temp'])
                    desc = item['weather'][0]['main']
                    icon = self.get_weather_emoji(item['weather'][0]['icon'])

                    daily_forecasts.append((day_name, icon, desc, f"{temp}{temp_symbol}"))

                    if len(daily_forecasts) == 5: break

            for i, forecast in enumerate(daily_forecasts):
                self.forecast_frames[i]["day"].configure(text=forecast[0])
                self.forecast_frames[i]["icon"].configure(text=forecast[1])
                self.forecast_frames[i]["desc"].configure(text=forecast[2])
                self.forecast_frames[i]["temp"].configure(text=forecast[3])

        except Exception as e:
            print("Forecast Error:", e)

    # --- Data Management ---
    def save_record(self, city, temperature):
        date_str = datetime.now().strftime("%d-%m-%Y %H:%M")
        with open(self.history_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([date_str, city, temperature])
        self.load_history()

    def load_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            with open(self.history_file, mode='r', encoding='utf-8') as file:
                reader = list(csv.reader(file))
                for row in reversed(reader[1:]):
                    if row:
                        self.tree.insert("", ctk.END, values=(row[0], row[1], row[2]))
        except FileNotFoundError:
            pass

    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please click on a record to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
        if not confirm: return

        selected_values = self.tree.item(selected_item[0])['values']

        with open(self.history_file, 'r', encoding='utf-8') as f:
            lines = list(csv.reader(f))

        for i in range(1, len(lines)):
            if lines[i][0] == str(selected_values[0]) and lines[i][1] == str(selected_values[1]):
                del lines[i]
                break

        with open(self.history_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lines)

        self.load_history()

    def export_pdf(self):
        if not PDF_AVAILABLE:
            messagebox.showerror("Missing Library", "Please run: pip install fpdf")
            return
        try:
            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Weather Search History", ln=True, align='C')
            pdf.ln(5)

            pdf.set_font("Arial", 'B', 12)
            pdf.cell(50, 10, "Date & Time", border=1, align='C')
            pdf.cell(90, 10, "City", border=1, align='C')
            pdf.cell(40, 10, "Temperature", border=1, ln=True, align='C')

            pdf.set_font("Arial", size=11)
            with open(self.history_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reversed(list(reader)):
                    if row:
                        pdf.cell(50, 10, row[0], border=1, align='C')
                        pdf.cell(90, 10, row[1], border=1, align='C')
                        pdf.cell(40, 10, row[2].encode('latin-1', 'replace').decode('latin-1'), border=1, ln=True,
                                 align='C')

            export_name = f"Weather_History_{datetime.now().strftime('%d_%m_%Y')}.pdf"
            pdf.output(export_name)
            messagebox.showinfo("Export Successful", f"Your report has been saved as:\n{export_name}")

        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred:\n{e}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = WeatherAppPro(root)
    root.mainloop()