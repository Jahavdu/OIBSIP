import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt


try:
    from fpdf import FPDF

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Set initial theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class BMICalculatorPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced BMI Tracker")
        
        self.root.geometry("450x680")
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.history_file = "bmi_history.csv"
        self.setup_file()

        # --- Top Header (Stays visible across all tabs) ---
        top_bar = ctk.CTkFrame(root, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(15, 5))

        header_label = ctk.CTkLabel(top_bar, text="BMI Tracker", font=("Roboto", 24, "bold"))
        header_label.pack(side="left")

        self.theme_switch = ctk.CTkSwitch(top_bar, text="Dark Mode", command=self.toggle_theme)
        self.theme_switch.pack(side="right")
        self.theme_switch.select()

       -
        self.tabview = ctk.CTkTabview(root, width=410, height=520, corner_radius=10)
        self.tabview.pack(padx=20, pady=5, fill="both", expand=True)

        self.tab1 = self.tabview.add("Calculator")
        self.tab2 = self.tabview.add("History & Export")

      
        

        self.unit_var = ctk.StringVar(value="Metric")
        self.unit_switch = ctk.CTkSegmentedButton(self.tab1, values=["Metric", "Imperial"],
                                                  variable=self.unit_var, command=self.change_units)
        self.unit_switch.pack(pady=(10, 15))

        # Inputs
        self.weight_entry = ctk.CTkEntry(self.tab1, placeholder_text="Current Weight (kg)", width=250, height=40,
                                         font=("Roboto", 14), justify="center")
        self.weight_entry.pack(pady=6)

        self.height_entry = ctk.CTkEntry(self.tab1, placeholder_text="Height (m or cm)", width=250, height=40,
                                         font=("Roboto", 14), justify="center")
        self.height_entry.pack(pady=6)

        self.goal_entry = ctk.CTkEntry(self.tab1, placeholder_text="Goal Weight (kg) - Optional", width=250, height=40,
                                       font=("Roboto", 14), justify="center")
        self.goal_entry.pack(pady=6)

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.tab1, fg_color="transparent")
        btn_frame.pack(pady=10)

        calc_btn = ctk.CTkButton(btn_frame, text="Calculate", font=("Roboto", 14, "bold"), width=120, height=40,
                                 corner_radius=8, command=self.calculate_bmi)
        calc_btn.grid(row=0, column=0, padx=10)

        clear_btn = ctk.CTkButton(btn_frame, text="Clear", font=("Roboto", 14), width=80, height=40, corner_radius=8,
                                  fg_color="gray", hover_color="#555555", command=self.clear_inputs)
        clear_btn.grid(row=0, column=1, padx=10)

        # Results Display
        self.result_frame = ctk.CTkFrame(self.tab1, corner_radius=10, fg_color=("gray85", "gray20"))
        self.result_frame.pack(pady=5, padx=20, fill="x")

        self.bmi_result_label = ctk.CTkLabel(self.result_frame, text="BMI: --", font=("Roboto", 24, "bold"))
        self.bmi_result_label.pack(pady=(15, 5))

        self.category_label = ctk.CTkLabel(self.result_frame, text="Category: --", font=("Roboto", 16))
        self.category_label.pack()

        self.ideal_label = ctk.CTkLabel(self.result_frame, text="", font=("Roboto", 13))
        self.ideal_label.pack(pady=(5, 0))

        self.goal_label = ctk.CTkLabel(self.result_frame, text="", font=("Roboto", 14, "italic"))
        self.goal_label.pack(pady=(5, 5))

        self.gauge = ctk.CTkProgressBar(self.result_frame, width=250, height=12, corner_radius=10)
        self.gauge.pack(pady=(5, 15))
        self.gauge.set(0)


        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=25, font=("Roboto", 11))
        style.configure("Treeview.Heading", font=("Roboto", 12, "bold"))

        columns = ("Date", "BMI", "Category")
        self.tree = ttk.Treeview(self.tab2, columns=columns, show="headings", height=8)
        self.tree.heading("Date", text="Date")
        self.tree.heading("BMI", text="BMI")
        self.tree.heading("Category", text="Category")

        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("BMI", width=80, anchor="center")
        self.tree.column("Category", width=150, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_history()  # Load data into treeview

        # History Buttons
        hist_btn_frame1 = ctk.CTkFrame(self.tab2, fg_color="transparent")
        hist_btn_frame1.pack(pady=(5, 5))

        delete_btn = ctk.CTkButton(hist_btn_frame1, text="Delete Selected", width=130, fg_color="#DC3545",
                                   hover_color="#C82333", command=self.delete_selected)
        delete_btn.grid(row=0, column=0, padx=5)

        chart_btn = ctk.CTkButton(hist_btn_frame1, text="📈 Show Chart", width=130, fg_color="#28A745",
                                  hover_color="#218838", command=self.show_chart)
        chart_btn.grid(row=0, column=1, padx=5)

        hist_btn_frame2 = ctk.CTkFrame(self.tab2, fg_color="transparent")
        hist_btn_frame2.pack(pady=(5, 15))

        export_pdf_btn = ctk.CTkButton(hist_btn_frame2, text="📄 Export to PDF", width=270, fg_color="#6C757D",
                                       hover_color="#5A6268", command=self.export_pdf)
        export_pdf_btn.grid(row=0, column=0)

        footer_label = ctk.CTkLabel(root, text="Developed by Durvesh Jadhav\nPython Programming Internship Project",
                                    font=("Roboto", 11), text_color="gray")
        footer_label.pack(side="bottom", pady=10)

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def setup_file(self):
        if not os.path.exists(self.history_file):
            with open(self.history_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Weight", "Height", "BMI", "Category"])

    def change_units(self, choice):
        self.clear_inputs()
        if choice == "Metric":
            self.weight_entry.configure(placeholder_text="Current Weight (kg)")
            self.height_entry.configure(placeholder_text="Height (m or cm)")
            self.goal_entry.configure(placeholder_text="Goal Weight (kg) - Optional")
        else:
            self.weight_entry.configure(placeholder_text="Current Weight (lbs)")
            self.height_entry.configure(placeholder_text="Height (inches)")
            self.goal_entry.configure(placeholder_text="Goal Weight (lbs) - Optional")

    def calculate_bmi(self):
        try:
            weight = float(self.weight_entry.get())
            height = float(self.height_entry.get())

            if weight <= 0 or height <= 0:
                raise ValueError("Values must be greater than zero.")

            if self.unit_var.get() == "Metric":
                if height > 3.0:
                    height = height / 100

                bmi = round(weight / (height ** 2), 2)
                weight_save, height_save = weight, height
                unit_label = "kg"

                min_weight = round(18.5 * (height ** 2), 1)
                max_weight = round(24.9 * (height ** 2), 1)
            else:
                bmi = round((weight / (height ** 2)) * 703, 2)
                weight_save = round(weight * 0.453592, 2)
                height_save = round(height * 0.0254, 2)
                unit_label = "lbs"

                min_weight = round((18.5 * (height ** 2)) / 703, 1)
                max_weight = round((24.9 * (height ** 2)) / 703, 1)

            if bmi < 18.5:
                category, emoji, color = "Underweight", "🔵", "#3498DB"
            elif 18.5 <= bmi <= 24.9:
                category, emoji, color = "Normal Weight", "🟢", "#2ECC71"
            elif 25.0 <= bmi <= 29.9:
                category, emoji, color = "Overweight", "🟠", "#F39C12"
            else:
                category, emoji, color = "Obese", "🔴", "#E74C3C"

            goal_input = self.goal_entry.get()
            if goal_input.strip():
                goal = float(goal_input)
                diff = abs(weight - goal)
                if weight > goal:
                    self.goal_label.configure(text=f"🎯 Target: Lose {diff:.1f} {unit_label}")
                elif weight < goal:
                    self.goal_label.configure(text=f"🎯 Target: Gain {diff:.1f} {unit_label}")
                else:
                    self.goal_label.configure(text="🎯 You hit your goal weight!")
            else:
                self.goal_label.configure(text="")

            self.bmi_result_label.configure(text=f"BMI: {bmi}")
            self.category_label.configure(text=f"{emoji} {category}", text_color=color)
            self.ideal_label.configure(text=f"Healthy Range: {min_weight} - {max_weight} {unit_label}",
                                       text_color="gray")

            progress = (bmi - 15) / 25
            progress = max(0.0, min(1.0, progress))
            self.gauge.set(progress)
            self.gauge.configure(progress_color=color)

            self.save_record(weight_save, height_save, bmi, category)

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")

    def save_record(self, weight, height, bmi, category):
        date_str = datetime.now().strftime("%d-%m-%Y")
        with open(self.history_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([date_str, weight, height, bmi, category])

        self.load_history()  

    def clear_inputs(self):
        self.weight_entry.delete(0, ctk.END)
        self.height_entry.delete(0, ctk.END)
        self.goal_entry.delete(0, ctk.END)
        self.bmi_result_label.configure(text="BMI: --", text_color=("black", "white"))
        self.category_label.configure(text="Category: --", text_color=("black", "white"))
        self.goal_label.configure(text="")
        self.ideal_label.configure(text="")
        self.gauge.set(0)

       

    def load_history(self):
        # Clear existing data in treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with open(self.history_file, mode='r', encoding='utf-8') as file:
                reader = list(csv.reader(file))
                for row in reader[1:]:
                    if row:
                        self.tree.insert("", ctk.END, values=(row[0], row[3], row[4]))
        except FileNotFoundError:
            pass

    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please click on a record to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
        if not confirm: return

        index_to_delete = self.tree.index(selected_item[0])
        with open(self.history_file, 'r', encoding='utf-8') as f:
            lines = list(csv.reader(f))

        del lines[index_to_delete + 1]

        with open(self.history_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lines)

        self.load_history()  # Refresh UI

    def export_pdf(self):
        if not PDF_AVAILABLE:
            messagebox.showerror("Missing Library",
                                 "Please open your terminal and run:\n\npip install fpdf\n\nto enable PDF exports.")
            return

        try:
            pdf = FPDF()
            pdf.add_page()

            # Title
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Personal BMI Tracker Report", ln=True, align='C')
            pdf.ln(5)

            # Table Header
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(40, 10, "Date", border=1, align='C')
            pdf.cell(30, 10, "Weight", border=1, align='C')
            pdf.cell(30, 10, "Height", border=1, align='C')
            pdf.cell(30, 10, "BMI", border=1, align='C')
            pdf.cell(50, 10, "Category", border=1, ln=True, align='C')

            # Read CSV Data
            pdf.set_font("Arial", size=11)
            with open(self.history_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip CSV header
                for row in reader:
                    if row:
                        pdf.cell(40, 10, row[0], border=1, align='C')
                        pdf.cell(30, 10, f"{row[1]}kg", border=1, align='C')
                        pdf.cell(30, 10, f"{row[2]}m", border=1, align='C')
                        pdf.cell(30, 10, row[3], border=1, align='C')
                        pdf.cell(50, 10, row[4], border=1, ln=True, align='C')

            # Save file
            export_name = f"BMI_Report_{datetime.now().strftime('%d_%m_%Y')}.pdf"
            pdf.output(export_name)
            messagebox.showinfo("Export Successful", f"Your report has been saved as:\n\n{export_name}")

        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred:\n{e}")

    def show_chart(self):
        dates, bmis = [], []
        try:
            with open(self.history_file, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    if row:
                        dates.append(row[0])
                        bmis.append(float(row[3]))
        except FileNotFoundError:
            messagebox.showinfo("No Data", "No history available to graph.")
            return

        if not dates:
            messagebox.showinfo("No Data", "Not enough data to plot a chart.")
            return

        plt.style.use('ggplot')
        plt.figure(figsize=(8, 5))
        plt.plot(dates, bmis, marker='o', linestyle='-', color='#3498DB', linewidth=2, markersize=8, label='Your BMI')
        plt.axhspan(18.5, 24.9, color='#2ECC71', alpha=0.2, label='Normal Weight Zone')
        plt.title("Your BMI Trend", fontsize=14, fontweight='bold')
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("BMI Score", fontsize=12)
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = ctk.CTk()
    app = BMICalculatorPro(root)
    root.mainloop()
