import customtkinter as ctk
import webbrowser
import threading
from tkinter import filedialog
import pandas as pd
from os import path, makedirs, getcwd
from customtkinter import CTkInputDialog, CTkToplevel

from .gsp_algorithm import execute_tool
from .utils import ToolTip, validate_data_schema, create_event_order, save_dataset

class SequencingAnalysisTool:
    def __init__(self, root):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme(path.join(getcwd(), "themes/fordham-theme.json"))

        self.root = root
        self.root.title("Sequence Analysis Tool")

        self.file_df = None
        self.results = None
        self.is_course_data = True
        self.concurrent_var = ctk.IntVar()
        self.input_file_name = ctk.StringVar()
        self.run_mode_var = ctk.StringVar(value="together")
        self.select_all_var = ctk.IntVar()
        self.output_directory = path.join(getcwd(), 'output')
        self.selected_granularity = ""
        makedirs(self.output_directory, exist_ok=True)

        self.categories = set()
        self.category_vars = []

        self.progress = ctk.CTkProgressBar(self.root, mode='indeterminate')
        self.setup_gui()

        self.root.after(100, self.adjust_window_to_fit)

    def adjust_window_to_fit(self):
        self.root.update_idletasks()
        self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def bind_tooltip(self, widget, text):
        tooltip = ToolTip(widget, text)
        widget.bind("<Enter>", lambda e: tooltip.showtip())
        widget.bind("<Leave>", lambda e: tooltip.hidetip())

    def setup_gui(self):
        padding = {'padx': 10, 'pady': 5}

        ctk.CTkLabel(self.root, text="Input File Name:").grid(row=0, column=0, sticky='w', **padding)
        input_entry = ctk.CTkEntry(self.root, textvariable=self.input_file_name, width=350)
        input_entry.grid(row=0, column=1, sticky='ew', **padding)
        ctk.CTkButton(self.root, text="Browse", command=self.browse_file).grid(row=0, column=2, **padding)

        ctk.CTkLabel(self.root, text="Minimum Support(s):").grid(row=1, column=0, sticky='w', **padding)
        self.min_supports_entry = ctk.CTkEntry(self.root)
        self.min_supports_entry.grid(row=1, column=1, columnspan=2, sticky='ew', **padding)

        self.concurrent_checkbox = ctk.CTkCheckBox(self.root, text="Enable Concurrency", variable=self.concurrent_var, command=self.toggle_concurrency)
        self.concurrent_checkbox.grid(row=2, column=0, sticky='w', **padding)
        self.granularity_button = ctk.CTkButton(self.root, text="Change Granularity", command=self.prompt_timegroup)
        self.granularity_button.grid(row=2, column=1, sticky='w', **padding)
        self.granularity_button.grid_remove()

        self.granularity_label = ctk.CTkLabel(self.root, text="")
        self.granularity_label.grid(row=2, column=2, sticky='w', **padding)

        self.category_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.category_frame.grid(row=3, column=0, columnspan=3, sticky='nsew', padx=10, pady=0)
        self.category_frame.grid_remove()

        self.category_label = ctk.CTkLabel(self.category_frame, text="Categories:")
        self.category_label.grid(row=0, column=0, sticky="nw")

        self.scrollable_categories = ctk.CTkScrollableFrame(self.category_frame, width=260, height=60, fg_color="transparent")
        self.scrollable_categories.grid(row=0, column=1, sticky="nw", padx=(10, 0))

        self.side_button_frame = ctk.CTkFrame(self.category_frame, fg_color="transparent")
        self.side_button_frame.grid(row=0, column=2, padx=10, sticky="n")

        self.select_all_checkbox = ctk.CTkCheckBox(self.side_button_frame, text="Select All", variable=self.select_all_var, command=self.select_all_categories)
        self.select_all_checkbox.pack(anchor='w', pady=(0, 5))

        self.run_mode_radio_together = ctk.CTkRadioButton(self.side_button_frame, text="Together", variable=self.run_mode_var, value="together")
        self.run_mode_radio_separate = ctk.CTkRadioButton(self.side_button_frame, text="Separately", variable=self.run_mode_var, value="separate")
        self.run_mode_radio_together.pack(anchor='w')
        self.run_mode_radio_separate.pack(anchor='w')

        ctk.CTkLabel(self.root, text="Output Directory:").grid(row=4, column=0, sticky='w', **padding)
        self.output_directory_label = ctk.CTkLabel(self.root, text=self.output_directory, anchor='w')
        self.output_directory_label.grid(row=4, column=1, sticky='ew', **padding)
        ctk.CTkButton(self.root, text="Browse", command=self.set_output_directory).grid(row=4, column=2, **padding)

        ctk.CTkButton(self.root, text="Run Tool", command=self.run_gsp).grid(row=5, column=0, **padding)
        ctk.CTkButton(self.root, text="Help", command=self.open_web).grid(row=5, column=2, **padding)

        self.progress.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.progress.grid_remove()

        self.run_status_label = ctk.CTkLabel(self.root, text="")
        self.run_status_label.grid(row=7, column=1, **padding)

        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.bind_tooltip(input_entry, "Select the preprocessed input CSV file.")
        self.bind_tooltip(self.min_supports_entry, "Enter minimum support values as comma-separated integers.")
        self.bind_tooltip(self.concurrent_checkbox, "Enable analysis of concurrent sequences.")
        self.bind_tooltip(self.granularity_button, "Change the time granularity for concurrency.")
        self.bind_tooltip(self.select_all_checkbox, "Select or deselect all categories.")
        self.bind_tooltip(self.run_mode_radio_together, "Run algorithm with categories treated as one group.")
        self.bind_tooltip(self.run_mode_radio_separate, "Run algorithm separately for each category.")
        self.bind_tooltip(self.output_directory_label, "Output folder for saving results.")


    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        df = pd.read_csv(file_path, low_memory=False)
        df, file_path, is_valid = validate_data_schema(df, gui=True)
        self.input_file_name.set(file_path)

        if not is_valid:
            self.themed_popup("Invalid Data", "The dataset could not be corrected. Please check your data.")
            return

        self.reset_gui_state()
        self.file_df = df
        self.validate_categories()
        self.adjust_window_to_fit()

    def reset_gui_state(self):
        self.concurrent_var.set(0)
        self.select_all_var.set(0)
        self.run_mode_var.set("together")
        self.granularity_label.configure(text="")
        self.granularity_button.grid_remove()
        self.selected_granularity = ""
        for widget in self.scrollable_categories.winfo_children():
            widget.destroy()
        self.category_vars.clear()
        self.category_frame.grid_remove()

    def validate_categories(self):
        self.categories.clear()
        for widget in self.scrollable_categories.winfo_children():
            widget.destroy()
        self.category_vars.clear()

        if "Category" in self.file_df.columns:
            unique_categories = sorted(self.file_df["Category"].dropna().unique())
            self.categories.update(unique_categories)

            for cat in unique_categories:
                var = ctk.IntVar()
                chk = ctk.CTkCheckBox(self.scrollable_categories, text=cat, variable=var)
                chk.pack(anchor='w', padx=5, pady=0)
                self.category_vars.append((cat, var))

            self.category_frame.grid()

    def toggle_concurrency(self):
        if self.concurrent_var.get():
            self.prompt_timegroup()
        else:
            self.granularity_button.grid_remove()
            self.granularity_label.configure(text="")
            self.selected_granularity = ""
            if "EventOrder" in self.file_df.columns:
                self.file_df.drop(columns=["EventOrder"], inplace=True)
                df, new_path = save_dataset(self.file_df)
                self.file_df = df
                self.input_file_name.set(new_path)

    def prompt_timegroup(self):
        dialog = CTkInputDialog(
            text="Please specify the time grouping unit (e.g., 'Y' for Year, 'M' for Month, 'W' for Week, 'Q' for Quarter, 'S' for Semester).",
            title="Specify Time Group Unit"
        )
        unit = dialog.get_input()

        if not unit:
            self.concurrent_checkbox.deselect()
            self.granularity_button.grid_remove()
            self.granularity_label.configure(text="")
            self.selected_granularity = ""
            return

        df, new_path = create_event_order(self.file_df, timegroup_unit=unit)
        self.file_df = df
        self.input_file_name.set(new_path)
        self.selected_granularity = unit.upper()
        self.granularity_button.grid()
        self.granularity_label.configure(text=f"Current: {self.selected_granularity}")
        self.adjust_window_to_fit()

    def select_all_categories(self):
        select_all = bool(self.select_all_var.get())
        for _, var in self.category_vars:
            var.set(select_all)

    def set_output_directory(self):
        selected = filedialog.askdirectory()
        if selected:
            self.output_directory = selected
            self.output_directory_label.configure(text=self.output_directory)

    def run_gsp(self):
        selected_categories = [cat for cat, var in self.category_vars if var.get() == 1]
        if self.categories and not selected_categories:
            self.themed_popup("Warning", "Please select at least one category.")
            return

        if not self.min_supports_entry.get():
            self.themed_popup("Warning", "Please specify at least one minimum support value.")
            return

        try:
            min_supports = [int(s) for s in self.min_supports_entry.get().split(",")]
        except ValueError:
            self.themed_popup("Error", "Please enter integer values for minimum support(s).")
            return

        def target():
            self.run_status_label.configure(text="Running tool ...")
            self.adjust_window_to_fit()
            self.progress.grid()
            self.progress.start()

            try:
                self.results = execute_tool(
                    self.file_df,
                    min_supports,
                    selected_categories,
                    self.run_mode_var.get(),
                    self.concurrent_var.get(),
                    self.output_directory
                )
            finally:
                self.progress.stop()
                self.progress.grid_remove()
                self.run_status_label.configure(text="Tool finished. Check output directory.")

        threading.Thread(target=target).start()

    def themed_popup(self, title, message):
        top = CTkToplevel(self.root)
        top.title(title)
        top.geometry("300x120")
        top.grab_set()

        label = ctk.CTkLabel(top, text=message, wraplength=260)
        label.pack(pady=(20, 10))

        ok_button = ctk.CTkButton(top, text="OK", command=top.destroy)
        ok_button.pack(pady=(0, 10))

    def open_web(self):
        webbrowser.open('https://github.com/Fordham-EDM-Lab/course-sequencing-analysis-tool')

def main():
    app = ctk.CTk()
    SequencingAnalysisTool(app)
    app.mainloop()

if __name__ == "__main__":
    main()
