import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import random
import string
import csv
import os
from datetime import datetime

try:
    from fpdf import FPDF

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class PasswordGeneratorPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Generator Pro")
        self.root.geometry("500x700")
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.history_file = "password_history.csv"
        self.setup_file()

       
        top_bar = ctk.CTkFrame(root, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(15, 5))

        header_label = ctk.CTkLabel(top_bar, text="Password Pro", font=("Roboto", 24, "bold"))
        header_label.pack(side="left")

        self.theme_switch = ctk.CTkSwitch(top_bar, text="Dark Mode", command=self.toggle_theme)
        self.theme_switch.pack(side="right")
        self.theme_switch.select()

        
        self.tabview = ctk.CTkTabview(root, width=460, height=550, corner_radius=10)
        self.tabview.pack(padx=20, pady=5, fill="both", expand=True)

        self.tab1 = self.tabview.add("Generator")
        self.tab2 = self.tabview.add("History")


        length_frame = ctk.CTkFrame(self.tab1, fg_color="transparent")
        length_frame.pack(pady=(10, 5), fill="x", padx=20)

        self.len_label = ctk.CTkLabel(length_frame, text="Password Length: 16", font=("Roboto", 16, "bold"))
        self.len_label.pack(pady=(0, 5))

        self.length_slider = ctk.CTkSlider(length_frame, from_=8, to=50, number_of_steps=42,
                                           command=self.update_length_label)
        self.length_slider.set(16)
        self.length_slider.pack(fill="x")

        toggles_frame = ctk.CTkFrame(self.tab1, corner_radius=10)
        toggles_frame.pack(pady=15, padx=20, fill="x")

        self.var_upper = ctk.BooleanVar(value=True)
        self.var_lower = ctk.BooleanVar(value=True)
        self.var_nums = ctk.BooleanVar(value=True)
        self.var_syms = ctk.BooleanVar(value=True)
        self.var_exclude = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(toggles_frame, text="Uppercase (A-Z)", variable=self.var_upper).grid(row=0, column=0, padx=20,
                                                                                             pady=10, sticky="w")
        ctk.CTkCheckBox(toggles_frame, text="Lowercase (a-z)", variable=self.var_lower).grid(row=0, column=1, padx=20,
                                                                                             pady=10, sticky="w")
        ctk.CTkCheckBox(toggles_frame, text="Numbers (0-9)", variable=self.var_nums).grid(row=1, column=0, padx=20,
                                                                                          pady=10, sticky="w")
        ctk.CTkCheckBox(toggles_frame, text="Symbols (@#$%)", variable=self.var_syms).grid(row=1, column=1, padx=20,
                                                                                           pady=10, sticky="w")

        ctk.CTkCheckBox(toggles_frame, text="Exclude Similar Characters (i, l, 1, L, o, 0, O)",
                        variable=self.var_exclude, text_color="#F39C12").grid(row=2, column=0, columnspan=2, padx=20,
                                                                              pady=(10, 15), sticky="w")

        self.gen_btn = ctk.CTkButton(self.tab1, text="⚡ Generate Password", font=("Roboto", 16, "bold"), height=45,
                                     command=self.generate_password)
        self.gen_btn.pack(pady=10)

        result_frame = ctk.CTkFrame(self.tab1, corner_radius=10, fg_color=("gray85", "gray20"))
        result_frame.pack(pady=10, padx=20, fill="x")

        pw_input_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        pw_input_frame.pack(pady=(15, 5))

        self.pw_entry = ctk.CTkEntry(pw_input_frame, width=240, height=40, font=("Consolas", 16), justify="center")
        self.pw_entry.grid(row=0, column=0, padx=(0, 10))

        self.show_btn = ctk.CTkButton(pw_input_frame, text="👁", width=40, height=40, fg_color="gray",
                                      command=self.toggle_visibility)
        self.show_btn.grid(row=0, column=1)

        self.strength_label = ctk.CTkLabel(result_frame, text="Strength: --", font=("Roboto", 16, "bold"))
        self.strength_label.pack(pady=(5, 5))

        self.copy_btn = ctk.CTkButton(result_frame, text="📋 Copy to Clipboard", fg_color="#28A745",
                                      hover_color="#218838", command=self.copy_to_clipboard)
        self.copy_btn.pack(pady=(5, 15))

       
        hist_top_frame = ctk.CTkFrame(self.tab2, fg_color="transparent")
        hist_top_frame.pack(fill="x", padx=10, pady=(5, 0))

        self.reveal_switch = ctk.CTkSwitch(hist_top_frame, text="Reveal Passwords", font=("Roboto", 12, "bold"),
                                           text_color="#F39C12", command=self.load_history)
        self.reveal_switch.pack(side="right")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=25, font=("Roboto", 11))
        style.configure("Treeview.Heading", font=("Roboto", 12, "bold"))

        columns = ("Date", "Password", "Strength")
        self.tree = ttk.Treeview(self.tab2, columns=columns, show="headings",
                                 height=11)  # Slightly shorter to fit switch
        self.tree.heading("Date", text="Date")
        self.tree.heading("Password", text="Password")
        self.tree.heading("Strength", text="Strength")

        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("Password", width=180, anchor="center")
        self.tree.column("Strength", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.load_history()

        hist_btn_frame = ctk.CTkFrame(self.tab2, fg_color="transparent")
        hist_btn_frame.pack(pady=(5, 10))

        delete_btn = ctk.CTkButton(hist_btn_frame, text="Delete Selected", width=140, fg_color="#DC3545",
                                   hover_color="#C82333", command=self.delete_selected)
        delete_btn.grid(row=0, column=0, padx=10)

        export_btn = ctk.CTkButton(hist_btn_frame, text="📄 Export to PDF", width=140, fg_color="#6C757D",
                                   hover_color="#5A6268", command=self.export_pdf)
        export_btn.grid(row=0, column=1, padx=10)

        footer_label = ctk.CTkLabel(root, text="Developed by Durvesh Jadhav\nPython Programming Internship Project",
                                    font=("Roboto", 11), text_color="gray")
        footer_label.pack(side="bottom", pady=10)

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def update_length_label(self, value):
        self.len_label.configure(text=f"Password Length: {int(value)}")

    def toggle_visibility(self):
        if self.pw_entry.cget("show") == "":
            self.pw_entry.configure(show="*")
            self.show_btn.configure(text="👁")
        else:
            self.pw_entry.configure(show="")
            self.show_btn.configure(text="🙈")

    def copy_to_clipboard(self):
        password = self.pw_entry.get()
        if password:
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            self.root.update()
            messagebox.showinfo("Copied", "Password copied to clipboard!")
        else:
            messagebox.showwarning("Empty", "No password generated yet.")

    def setup_file(self):
        if not os.path.exists(self.history_file):
            with open(self.history_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Password", "Strength"])

    def generate_password(self):
        length = int(self.length_slider.get())

        use_upper = self.var_upper.get()
        use_lower = self.var_lower.get()
        use_nums = self.var_nums.get()
        use_syms = self.var_syms.get()
        exclude_sim = self.var_exclude.get()

        if not any([use_upper, use_lower, use_nums, use_syms]):
            messagebox.showerror("Error", "Please select at least one character type.")
            return

        upper_chars = string.ascii_uppercase
        lower_chars = string.ascii_lowercase
        num_chars = string.digits
        sym_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if exclude_sim:
            similar = "il1Lo0O"
            upper_chars = "".join(c for c in upper_chars if c not in similar)
            lower_chars = "".join(c for c in lower_chars if c not in similar)
            num_chars = "".join(c for c in num_chars if c not in similar)

        password_chars = []
        available_pools = []

        if use_upper:
            password_chars.append(random.choice(upper_chars))
            available_pools.append(upper_chars)
        if use_lower:
            password_chars.append(random.choice(lower_chars))
            available_pools.append(lower_chars)
        if use_nums:
            password_chars.append(random.choice(num_chars))
            available_pools.append(num_chars)
        if use_syms:
            password_chars.append(random.choice(sym_chars))
            available_pools.append(sym_chars)

        combined_pool = "".join(available_pools)
        while len(password_chars) < length:
            password_chars.append(random.choice(combined_pool))

        random.shuffle(password_chars)
        final_password = "".join(password_chars)

        strength, color = self.evaluate_strength(length, len(available_pools))

        self.pw_entry.delete(0, ctk.END)
        self.pw_entry.insert(0, final_password)
        self.pw_entry.configure(show="*")
        self.show_btn.configure(text="👁")

        self.strength_label.configure(text=f"Strength: {strength}", text_color=color)

        self.save_record(final_password, strength)

    def evaluate_strength(self, length, pool_count):
        if length < 10 or pool_count <= 2:
            return "🔴 Weak", "#E74C3C"
        elif 10 <= length < 14 and pool_count >= 3:
            return "🟡 Medium", "#F39C12"
        elif length >= 14 and pool_count == 4:
            return "🟢 Very Strong", "#2ECC71"
        else:
            return "🟢 Strong", "#2ECC71"

    # --- Data Management ---
    def save_record(self, password, strength):
        date_str = datetime.now().strftime("%d-%m-%Y %H:%M")
        with open(self.history_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([date_str, password, strength])
        self.load_history()

  
    def load_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Check if switch is ON or OFF 
            show_passwords = hasattr(self, 'reveal_switch') and self.reveal_switch.get() == 1

            with open(self.history_file, mode='r', encoding='utf-8') as file:
                reader = list(csv.reader(file))
                for row in reader[1:]:
                    if row:
                        if show_passwords:
                            display_pw = row[1]  # Show completely
                        else:
                            display_pw = ("*" * (len(row[1]) - 3)) + row[1][-3:] if len(row[1]) > 3 else "***"  # Mask

                        self.tree.insert("", ctk.END, values=(row[0], display_pw, row[2]))
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

        self.load_history()

   
    def export_pdf(self):
        if not PDF_AVAILABLE:
            messagebox.showerror("Missing Library", "Please run: pip install fpdf")
            return

        # Ask user how they want their PDF
        mask_pdf = messagebox.askyesno("Security Check",
                                       "Do you want to MASK the passwords (hide them) in the PDF report for security?\n\nClick 'Yes' to hide them.\nClick 'No' to show full passwords.")

        try:
            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Password Generation History", ln=True, align='C')
            pdf.ln(5)

            pdf.set_font("Arial", 'B', 12)
            pdf.cell(50, 10, "Date", border=1, align='C')
            pdf.cell(80, 10, "Password", border=1, align='C')
            pdf.cell(50, 10, "Strength", border=1, ln=True, align='C')

            pdf.set_font("Arial", size=11)
            with open(self.history_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    if row:
                        # Apply masking or unmasking based on user choice
                        if mask_pdf:
                            display_pw = ("*" * (len(row[1]) - 3)) + row[1][-3:] if len(row[1]) > 3 else "***"
                        else:
                            display_pw = row[1]

                        clean_strength = row[2].split(" ", 1)[-1]

                        pdf.cell(50, 10, row[0], border=1, align='C')
                        pdf.cell(80, 10, display_pw, border=1, align='C')
                        pdf.cell(50, 10, clean_strength, border=1, ln=True, align='C')

            export_name = f"Password_History_{datetime.now().strftime('%d_%m_%Y')}.pdf"
            pdf.output(export_name)
            messagebox.showinfo("Export Successful", f"Your report has been saved as:\n{export_name}")

        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred:\n{e}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = PasswordGeneratorPro(root)
    root.mainloop()
