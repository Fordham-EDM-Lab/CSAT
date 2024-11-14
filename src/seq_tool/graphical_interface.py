import webbrowser
import threading
import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
from .gsp_algorithm import execute_tool
from .utils import ToolTip, validate_data_schema, get_timegroup_unit, create_event_order, save_dataset
from os import path, makedirs, getcwd

class SequencingAnalysisTool:
    def __init__(self, root):
        self.root = root
        self.file_df = None
        self.results = None
        self.is_course_data = True
        self.concurrent_var = tk.IntVar()  # Future option for toggling concurrency
        output_path = path.join(getcwd(), 'output')
        makedirs(path.dirname(output_path), exist_ok=True)
        self.output_directory = output_path
        self.input_file_name = tk.StringVar()
        self.min_supports = []
        self.categories = set()
        self.select_all_var = tk.IntVar()
        self.run_mode_var = tk.StringVar(value="together")
        self.root.title("Sequence Analysis Tool")
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.setup_gui()

    def setup_gui(self):
        tk.Label(self.root, text="Input File Name:").grid(row=1, column=0, sticky=tk.W)
        input_file_name_entry = tk.Entry(self.root, textvariable=self.input_file_name, width=40)
        input_file_name_entry.grid(row=1, column=1)
        tk.Button(self.root, text="Browse", command=self.browse_file).grid(row=1, column=2)
        self.bind_tooltip_events(input_file_name_entry, "Enter the path of the input file containing transaction data.")

        tk.Label(self.root, text="Minimum Support(s):").grid(row=2, column=0, sticky=tk.W)
        self.min_supports_entry = tk.Entry(self.root)
        self.min_supports_entry.grid(row=2, column=1)
        self.bind_tooltip_events(self.min_supports_entry, "Enter the minimum support(s) as comma-separated values.")

        # Concurrency checkbox
        self.concurrent_checkbox = tk.Checkbutton(self.root, text="Enable Concurrency", variable=self.concurrent_var, command=self.toggle_concurrency)
        self.concurrent_checkbox.grid(row=3, column=0, sticky=tk.W)

        # Dynamically set the label to "Departments" for course-related data or "Category" for general data
        self.category_label = tk.Label(self.root, text="Category(s):")
        self.category_label.grid(row=4, column=0, sticky=tk.W)

        # Adjusted layout for categories listbox and output directory
        self.categories_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, height=5)
        self.categories_listbox.grid(row=4, column=1, rowspan=3)  # Span multiple rows to create more space
        self.categories_listbox.bind('<<ListboxSelect>>', self.update_radio_buttons_state)
        self.bind_tooltip_events(self.categories_listbox, f"Select one or more category(s).")

        button_frame = tk.Frame(self.root)
        button_frame.grid(row=4, column=2, padx=10)

        # Switch to using grid() for the checkbutton and radio buttons
        self.select_all_checkbox = tk.Checkbutton(button_frame, text="Select All", variable=self.select_all_var, command=self.select_all_categories)
        self.select_all_checkbox.grid(row=0, column=0, pady=2, sticky=tk.W)

        self.run_mode_radio_together = tk.Radiobutton(button_frame, text="Together", variable=self.run_mode_var, value="together")
        self.run_mode_radio_together.grid(row=1, column=0, pady=2, sticky=tk.W)
        self.bind_tooltip_events(self.run_mode_radio_together, "Run the algorithm on selected categories together.")

        self.run_mode_radio_separate = tk.Radiobutton(button_frame, text="Separately", variable=self.run_mode_var, value="separate")
        self.run_mode_radio_separate.grid(row=2, column=0, pady=2, sticky=tk.W)
        self.bind_tooltip_events(self.run_mode_radio_together, "Run the algorithm on selected categories separately.")

        self.hide_category_widgets()

        # Moved output directory to a new row below the listbox
        tk.Label(self.root, text="Output Directory:").grid(row=7, column=0, sticky=tk.W)
        self.output_directory_label = tk.Label(self.root, text=self.output_directory, width=40, anchor="w")
        self.output_directory_label.grid(row=7, column=1, sticky=tk.W)
        self.bind_tooltip_events(self.output_directory_label, "Specify the output directory for the algorithm results.")

        tk.Button(self.root, text="Browse", command=self.set_output_directory).grid(row=7, column=2)
        
        # Place Run and Help buttons below everything
        tk.Button(self.root, text="Run Tool", command=self.run_gsp).grid(row=8, column=0, pady=10)
        tk.Button(self.root, text="Help", command=self.open_web).grid(row=8, column=2)

        self.run_status_label = tk.Label(self.root, text="")
        self.run_status_label.grid(row=9, column=1)

        self.root.mainloop()
    
    def hide_category_widgets(self):
        """Hide category/department-related widgets."""
        self.category_label.grid_remove()
        self.categories_listbox.grid_remove()
        self.select_all_checkbox.grid_remove()
        self.run_mode_radio_together.grid_remove()
        self.run_mode_radio_separate.grid_remove()

    def show_category_widgets(self):
        """Show category/department-related widgets."""
        self.category_label.grid()
        self.categories_listbox.grid()
        self.select_all_checkbox.grid()
        self.run_mode_radio_together.grid()
        self.run_mode_radio_separate.grid()

    def toggle_concurrency(self):
        if self.concurrent_var.get():
            if 'EventOrder' not in self.file_df.columns:
                self.prompt_timegroup()
        else:
            if 'EventOrder' in self.file_df.columns:
                self.file_df.drop(columns=['EventOrder'], inplace=True)
                df, new_path = save_dataset(self.file_df)
                self.file_df = df
                self.input_file_name.set(new_path)
                self.validate_categories
    
    def prompt_timegroup(self):
        """Prompt the user to create the EventOrder column if not already present."""
        unit = get_timegroup_unit(gui=True)

        if not unit:
            self.concurrent_checkbox.deselect()
            return

        # Call the utility function to create the EventOrder
        df, new_path = create_event_order(self.file_df, timegroup_unit=unit)
        self.file_df = df
        self.input_file_name.set(new_path)

    def bind_tooltip_events(self, widget, text):
        tooltip = ToolTip(widget, text)
        widget.bind("<Enter>", lambda event: tooltip.showtip())
        widget.bind("<Leave>", lambda event: tooltip.hidetip())

    def open_web(self):
        webbrowser.open('https://github.com/Fordham-EDM-Lab/course-sequencing-analysis-tool')

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        df = pd.read_csv(file_path, low_memory=False)

        # Validate and attempt to correct the dataframe schema
        df, file_path, is_valid = validate_data_schema(df, gui=True)
        self.input_file_name.set(file_path)
        
        if not is_valid:
            tk.messagebox.showerror("Invalid Data", "The dataset could not be corrected to meet the required schema. Please check your data.")
            return

        # Save the corrected dataframe
        self.file_df = df
        self.validate_categories()

    def validate_categories(self):
        """
        Validates and populates categories from the dataframe using pandas methods.
        """
        self.categories.clear()

        # Use the data dictionary to check for 'Category' column
        if 'Category' in self.file_df.columns:
            self.show_category_widgets()
            unique_categories = self.file_df['Category'].dropna().unique()
            self.categories.update(unique_categories)
        else:
            self.hide_category_widgets()

        # Populate the listbox with sorted categories
        sorted_categories = sorted(self.categories)
        self.categories_listbox.delete(0, tk.END)
        for category in sorted_categories:
            self.categories_listbox.insert(tk.END, category)

    def update_radio_buttons_state(self, event=None):
        selected_categories = self.categories_listbox.curselection()
        if len(selected_categories) > 1:
            # Enable the radio buttons if multiple categories are selected
            self.run_mode_radio_together.config(state=tk.NORMAL)
            self.run_mode_radio_separate.config(state=tk.NORMAL)
        else:
            # Disable the radio buttons if less than 2 categories are selected
            self.run_mode_radio_together.config(state=tk.DISABLED)
            self.run_mode_radio_separate.config(state=tk.DISABLED)

    def select_all_categories(self):
        if self.select_all_var.get():
            # Select all items in the listbox
            self.categories_listbox.select_set(0, tk.END)
        else:
            # Deselect all items in the listbox
            self.categories_listbox.selection_clear(0, tk.END)
        self.update_radio_buttons_state()

    def set_output_directory(self):
        self.output_directory = filedialog.askdirectory()
        if not self.output_directory:
            self.output_directory_label.config(text="Not specified.")
        else:
            self.output_directory_label.config(text=self.output_directory)

    def run_gsp(self):
        def target():
            self.run_status_label.config(text="Running tool ...")
            self.progress.grid(row=6, column=0, columnspan=3, sticky=tk.EW)
            self.progress.start()

            try:
                self.results = execute_tool(self.file_df, min_supports, selected_categories, run_mode_var, concurrency_var, self.output_directory)
            finally:
                self.progress.stop()
                self.progress.grid_forget()
                self.run_status_label.config(text="Tool finished running.\nVerify results in 'Output Directory'")

        selected_categories = [self.categories_listbox.get(i) for i in self.categories_listbox.curselection()]

        if not selected_categories and len(self.categories) != 0 and self.is_course_data:
            tk.messagebox.showwarning("No categories selected", "Please select at least one category to run the tool.")
        elif not self.min_supports_entry.get():
            tk.messagebox.showwarning("No minimum supports", "Please specify at least one minimum support value.")
        else:
            min_supports_str = self.min_supports_entry.get()
            min_supports = [int(s) for s in min_supports_str.split(",")]
            run_mode_var = self.run_mode_var.get()
            concurrency_var = self.concurrent_var.get()
            threading.Thread(target=target).start()

def main():
    root = tk.Tk()
    SequencingAnalysisTool(root)

if __name__ == "__main__":
    main()
