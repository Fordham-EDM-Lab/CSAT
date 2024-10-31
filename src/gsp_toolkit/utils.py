import tkinter as tk
import json
import pandas as pd
import numpy as np
import dateparser
from hashlib import md5
from os import path, makedirs

# A class to create ToolTips
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

    def showtip(self):
        # Method to show tooltip on hover
        self.tooltip_window = tk.Toplevel(self.widget)
        tooltip_label = tk.Label(self.tooltip_window, text=self.text)
        tooltip_label.pack()

        self.tooltip_window.overrideredirect(True)

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window.geometry(f"+{x}+{y}")

    def hidetip(self):
        # Method to hide tooltip when not hovering
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def save_to_folder(df, folder_path, file_name):
    makedirs(folder_path, exist_ok=True)
    df.to_csv(path.join(folder_path, file_name), index=False)
    return df

def save_dataset(df, file_name='preprocessed_data.csv'):
    save_path = path.join(path.dirname(__file__), '..', '..', 'data')
    df = save_to_folder(df, save_path, file_name)
    return df, save_path + '/preprocessed_data.csv'

def filter_and_export_to_csv(data_dict, min_support, total_transactions, file_name):
    """
    Filters and exports the provided data to a CSV file.

    Args:
        data_dict (dict): Dictionary containing the data to be exported.
        min_support (float): Minimum support threshold.
        total_transactions (int): Total number of transactions in the data.
        file_name (str): Name of the CSV file to which data will be exported.

    Returns:
        dict: A dictionary containing the counts of itemsets.
    """
    data_df = pd.DataFrame(data_dict)
   
    for column in data_df:
        data_df.drop(data_df[data_df[column] < min_support].index, inplace=True)
    
    itemset_counts = data_df.count().to_dict()
    data_df['Count %'] = (data_df.sum(axis=1) / total_transactions) * 100
    data_df.to_csv(file_name)
    
    return itemset_counts

def export_summary_to_file(single_item_count, itemset_count, total_transactions, elapsed_time, file_path):
    """
    Exports a summary of the results to a text file.

    Args:
        single_item_count (dict): Dictionary containing the count of single items.
        itemset_count (dict): Dictionary containing the count of itemsets of different sizes.
        total_transactions (int): Total number of transactions in the data.
        elapsed_time (float): Time taken to run the algorithm.
        file_path (str): Path to the text file where the summary will be written.

    Returns:
        None
    """
    with open(file_path, 'a') as file:
        file.write("===" * 20 + "\n")
        file.write(json.dumps(single_item_count))
        file.write("\n\n")
        file.write(json.dumps(itemset_count))
        file.write("\n\n")
        file.write(f"Transaction #: {total_transactions}")
        file.write("\n\n")
        file.write(f"--- {elapsed_time} seconds ---\n\n")

def get_data_dictionary():
    """
    Returns a dictionary of the expected data schema, including data types
    and whether each column is required.
    
    Returns:
        dict: Dictionary with data schema information.
    """
    return {
        'Item': {'dtype': str, 'required': True},
        'ID': {'dtype': str, 'required': True},
        'EventTime': {'dtype': int, 'required': True},
        'Category': {'dtype': str, 'required': False},
        'Year': {'dtype': int, 'required': False},
        'Semester': {'dtype': str, 'required': False},
        'CreditHours': {'dtype': int, 'required': False},
        'FinalGrade': {'dtype': str, 'required': False},
        'FinalGradeN': {'dtype': int, 'required': False}
    }

def generate_hash(input_string):
    """Generate a unique hash from an input string."""
    return md5(input_string.encode()).hexdigest()

def create_event_time_for_course(df, gui):
    """
    Create 'EventTime' column based on 'Semester' and 'Year' columns, using user-specified order for semesters.

    Args:
        df (pd.DataFrame): The dataframe containing course data with 'Year' and 'Semester' columns.
        gui (bool): Whether to prompt the user in the tkinter GUI for semester order.

    Returns:
        pd.DataFrame: The dataframe with the new 'EventTime' column.
    """
    # Prompt user for semester ordering (e.g., ['Spring', 'Summer', 'Fall'])
    unique_semesters = df['Semester'].unique()
    semester_order = get_ordering(unique_semesters, gui)
    
    # Map semesters to quarter numbers based on order
    semester_to_quarter = {val: i+1 for i, val in enumerate(semester_order)}
    
    # Create 'EventTime' based on Year and quarter mapping (using quarter start dates)
    df['EventTime'] = df.apply(
        lambda row: pd.Timestamp(f"{row['Year']}-Q{semester_to_quarter.get(row['Semester'], 1)}"),
        axis=1
    )
    return df

def create_event_order(df, time_column='EventTime', timegroup_unit='Y'):
    """
    Creates 'EventOrder' column based on specified timegroup unit and event time column.
    
    Args:
        df (pd.DataFrame): The dataframe containing 'EventTime'.
        time_column (str): Column with datetime values.
        timegroup_unit (str): Time granularity for grouping ('Y', 'M', 'Q', 'W').
        
    Returns:
        pd.DataFrame: The dataframe with the new 'EventOrder' column.
    """
    if timegroup_unit == 'Y':
        df['EventOrder'] = df[time_column].dt.year.astype(str)
    elif timegroup_unit == 'M':
        df['EventOrder'] = df[time_column].dt.strftime('%Y%m')
    elif timegroup_unit == 'Q':
        df['EventOrder'] = df[time_column].dt.year.astype(str) + df[time_column].dt.quarter.astype(str)
    elif timegroup_unit == 'W':
        df['EventOrder'] = df[time_column].dt.strftime('%Y%W')
    else:
        raise ValueError(f"Unsupported time group unit: {timegroup_unit}")
    
    return save_dataset(df)

def detect_date_columns(df):
    """
    Use `dateparser` to detect columns that contain date-like values.
    """
    exclude_columns = ['ID', 'id', 'Item']
    date_columns = []

    df_copy = df.copy()
    
    for col in df_copy.columns:
        if col not in exclude_columns:
            # Try parsing the first 10 non-null values in each column using `dateparser`
            if df_copy[col].dropna().head(10).apply(lambda x: dateparser.parse(str(x)) is not None).any():
                date_columns.append(col)
    
    return date_columns

def parse_dates(df, column_name):
    """
    Parses dates in the specified column using dateparser.

    Args:
        df (pd.DataFrame): The dataframe to parse.
        column_name (str): The name of the column to parse.

    Returns:
        pd.DataFrame: The dataframe with the 'EventTime' column added or corrected.
    """
    df[column_name] = df[column_name].replace('', np.nan)
    df['EventTime'] = pd.to_datetime(df[column_name].apply(lambda x: dateparser.parse(x) if pd.notna(x) else np.nan), errors='coerce')
    if df['EventTime'].isna().sum() > 0:
        print(f"Warning: Some dates could not be parsed in the column {column_name}.")
    return df

def get_ordering(unique_values, gui=False):
    """
    Prompt the user to specify the order of the unique values in the column.

    Args:
        unique_values (list): List of unique values in the column.
        gui (bool): Whether to prompt the user in the tkinter GUI.

    Returns:
        list: A list of ordered values (e.g., ['Spring', 'Fall']).
    """
    if gui:
        from tkinter import Tk
        root = Tk()
        root.withdraw()  # Hide the root window
        
        # Popup message to explain what the user should do
        message = f"Please enter the order of the following values, separated by commas, from earliest to latest:\n{unique_values}"
        
        # Ask the user to provide the order
        ordering_input = tk.simpledialog.askstring("Specify Order", message)
        
        # Convert input into a list of ordered values
        ordered_values = [val.strip() for val in ordering_input.split(',')]
    else:
        # Prompt in CLI
        print(message)
        ordering_input = input("Enter the order: ")
        
        # Convert input into a list of ordered values
        ordered_values = [val.strip() for val in ordering_input.split(',')]

    return ordered_values

def get_timegroup_unit(gui=False):
    if gui:
        from tkinter import Tk
        root = Tk()
        root.withdraw()
        message = "Please specify the time grouping unit (e.g., 'Y' for Year, 'M' for Month, 'W' for Week, 'Q' for Quarter)."
        timegroup_unit = tk.simpledialog.askstring("Specify Time Group Unit", message)
    else:
        print("Please specify the time grouping unit (e.g., 'Y', 'M', 'W', 'Q').")
        timegroup_unit = input("Enter the time unit: ")
    return timegroup_unit.strip().upper()

def prompt_user_column_selection(potential_date_columns, columns, gui):
    if gui:
        from tkinter import Tk
        root = Tk()
        root.withdraw()

        message = (f"Multiple columns were detected that may represent time-based information: {potential_date_columns}.\n\n"
                   "Please select the column that represents the time or date you want to use for ordering events.")
        
        column_name = tk.simpledialog.askstring("Select Time Column", message)
        
        if column_name not in columns:
            raise ValueError(f"Column '{column_name}' is not in the dataset.")
    else:
        print(f"Multiple columns were detected that may represent time-based information: {potential_date_columns}")
        column_name = input("Type the column name: ")
        
        if column_name not in columns:
            raise ValueError(f"Column '{column_name}' is not in the dataset.")
    
    return column_name

def validate_data_schema(df, gui=False):
    """
    Validates and corrects the dataframe to meet the expected schema using the data dictionary.
    Attempts to parse and create 'EventTime' if necessary.

    Args:
        df (pd.DataFrame): The dataframe to validate and correct.
        gui (bool): Whether to prompt the user in the tkinter GUI.

    Returns:
        pd.DataFrame: The corrected dataframe.
        bool: True if the dataframe meets the schema, False if it still doesn't meet requirements.
    """
    data_dict = get_data_dictionary()
    missing_required_columns = []
    incorrect_dtype_columns = []

    # Check for missing required columns and incorrect data types
    for col_name, properties in data_dict.items():
        if properties['required'] and col_name not in df.columns:
            missing_required_columns.append(col_name)
        elif col_name in df.columns and not pd.api.types.is_dtype_equal(df[col_name].dtype, properties['dtype']):
            print(df[col_name].dtype, col_name, properties['dtype'])

            try:
                df[col_name] = df[col_name].astype(properties['dtype'])
            except ValueError:
                incorrect_dtype_columns.append(col_name)

    # Handle missing 'EventTime' column: attempt to create it
    if 'EventTime' in missing_required_columns:
        # Check if 'Year' and 'Semester' columns exist for course-related data
        if 'Year' in df.columns and 'Semester' in df.columns:
            df = create_event_time_for_course(df, gui=gui)
            df = df.drop(columns=['Year', 'Semester'])
        else:
            # Attempt to detect and parse date columns
            potential_date_columns = detect_date_columns(df)
            column_name = None

            if len(potential_date_columns) > 1:
                column_name = prompt_user_column_selection(potential_date_columns, columns=df.columns, gui=gui)
            else:
                column_name = potential_date_columns[0]
            
            if column_name:
                df = parse_dates(df, column_name)
        
        missing_required_columns.remove('EventTime')
    elif 'EventTime' in incorrect_dtype_columns:
        df = parse_dates(df, 'EventTime')
        incorrect_dtype_columns.remove('EventTime')
    
    # Handle edge case: 'Category' column is missing but 'Department' column exists
    if 'Category' not in df.columns and 'Department' in df.columns:
        df['Category'] = df['Department']
        df = df.drop(columns=['Department'])

    # Log missing columns and incorrect types
    if missing_required_columns:
        print(f"Missing required columns: {missing_required_columns}")
    if incorrect_dtype_columns:
        print(f"Columns with incorrect data types: {incorrect_dtype_columns}")

    # Remove any remaining columns that are not in the data dictionary
    for col in df.columns:
        if col not in data_dict:
            df = df.drop(columns=[col])

    df, save_path = save_dataset(df)
    
    # Return corrected dataframe, save path, a flag indicating if it's valid
    return df, save_path, len(missing_required_columns) == 0 and len(incorrect_dtype_columns) == 0