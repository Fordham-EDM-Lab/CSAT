import tkinter as tk
import json
import pandas as pd
import numpy as np
import dateparser
from hashlib import md5
from os import path, makedirs, getcwd

semester_mapping = {}

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
    save_path = path.join(getcwd(), 'data')
    df = save_to_folder(df, save_path, file_name)
    return df, save_path + '/' + file_name

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
    Creates 'EventTime' column based on 'Year' and 'Semester' columns.

    Args:
        df (pd.DataFrame): The dataframe containing 'Year' and 'Semester'.
        gui (bool): Whether to prompt the user in the tkinter GUI.
    
    Returns:
        pd.DataFrame: The dataframe with the new 'EventTime' column.
    
    
    """
    unique_semesters = df['Semester'].unique()
    global semester_mapping

    if not semester_mapping:
        semester_mapping = get_ordering_and_mapping(unique_semesters, gui=gui)
    
    df['EventTime'] = df.apply(
        lambda row: f"{row['Year']}-{semester_mapping[row['Semester']][0]}-{semester_mapping[row['Semester']][1]}",
        axis=1
    )
    df = parse_dates(df, 'EventTime')

    return df

def get_ordering_and_mapping(unique_values, gui=False):
    """
    Prompt the user to specify the order of unique semester values and 
    optionally map each semester to a specific month and day.
    
    Args:
        unique_values (list): List of unique values in the 'Semester' column.
        gui (bool): Whether to use a tkinter GUI for input.

    Returns:
        dict: A dictionary with ordered semesters mapped to specific dates.
    """
    ordered_mapping = {}
    numbered_values = {str(i+1): v for i, v in enumerate(unique_values)}

    if gui:
        import tkinter.simpledialog as sd
        root = tk.Tk()
        root.withdraw()
        
        # Prompt user for order
        message = "Specify order by entering numbers for each value, separated by commas:\n"
        for num, value in numbered_values.items():
            message += f"{num}: {value}\n"
        ordering_input = sd.askstring("Order Input", message)
        
        # Prompt for specific month/day or equal distribution
        date_option = sd.askstring(
            "Mapping Option",
            "Enter 'specific' to map semesters to specific months/days, "
            "or 'equal' to distribute evenly."
        )
    else:
        # CLI prompts
        print("Enter the order of semesters by number (e.g., 1,2,3):")
        for num, value in numbered_values.items():
            print(f"{num}: {value}")
        ordering_input = input("Order: ")
        
        date_option = input("Enter 'specific' to map each semester to a month/day, or 'equal' to distribute: ")

    # Convert input numbers to ordered semester values
    ordered_semesters = [numbered_values[num.strip()] for num in ordering_input.split(",") if num.strip() in numbered_values]
    
    if date_option.lower() == 'specific':
        # Specific mapping: ask for month/day for each semester
        for semester in ordered_semesters:
            if gui:
                month = int(sd.askstring(f"Month for {semester}", f"Enter month for {semester} (1-12): "))
                day = int(sd.askstring(f"Day for {semester}", f"Enter day for {semester} (1-31): "))
            else:
                month = int(input(f"Enter month for {semester} (1-12): "))
                day = int(input(f"Enter day for {semester} (1-31): "))
            ordered_mapping[semester] = (month, day)
    else:
        # Equal distribution: automatically assign evenly spaced months
        for i, semester in enumerate(ordered_semesters):
            month = int((i / len(ordered_semesters)) * 12 + 1)  # Spread across months
            day = 1  # Default day to start of month
            ordered_mapping[semester] = (month, day)

    return ordered_mapping

def create_event_order(df, time_column='EventTime', timegroup_unit='Y'):
    """
    Creates an 'EventOrder' column based on the specified time grouping unit.

    Args:
        df (pd.DataFrame): The dataframe to add the 'EventOrder' column to.
        time_column (str): The name of the column containing the time information.
        timegroup_unit (str): The time grouping unit to use for ordering.
    
    Returns:
        pd.DataFrame: The dataframe with the new 'EventOrder' column.
    """
    global semester_mapping
    if timegroup_unit == 'S':
        # Step 1: Create a sorted list of tuples (month, day, name, index)
        sorted_semesters = sorted(
            [(v[0], v[1], k, i + 1) for i, (k, v) in enumerate(semester_mapping.items())],
            key=lambda x: (x[0], x[1])
        )
        
        # Step 2: Determine the closest semester for each EventTime
        def get_semester(event_time):
            month, day = event_time.month, event_time.day
            for sm_month, sm_day, semester_name, semester_index in sorted_semesters:
                if (month, day) >= (sm_month, sm_day):
                    closest_semester_index = semester_index
                else:
                    break
            return closest_semester_index

        # Step 3: Generate EventOrder using year and semester index
        df['EventOrder'] = df[time_column].apply(lambda x: f"{x.year}{get_semester(x):02d}")
    elif timegroup_unit == 'Y':
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

    Args:
        df (pd.DataFrame): The dataframe to check for date columns.

    Returns:
        list: A list of column names that contain date-like values.
    """
    exclude_columns = ['ID', 'Item']
    date_columns = []
    for col in df.columns:
        if col not in exclude_columns and df[col].dropna().head(10).apply(lambda x: dateparser.parse(str(x)) is not None).any():
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

def get_timegroup_unit(gui=False):
    """
    Prompts the user to specify the time grouping unit.

    Args:
        gui (bool): Whether to prompt the user in the tkinter GUI.
    
    Returns:
        str: The time grouping unit.
    """
    isValid = False
    
    if gui:
        from tkinter import Tk
        root = Tk()
        root.withdraw()
        message = "Please specify the time grouping unit (e.g., 'Y' for Year, 'M' for Month, 'W' for Week, 'Q' for Quarter, 'S' for Semester)."
        timegroup_unit = tk.simpledialog.askstring("Specify Time Group Unit", message)

        # if cancel is clicked
        if timegroup_unit is None:
            return None
    else:
        print("Please specify the time grouping unit (e.g., 'Y', 'M', 'W', 'Q', 'S').")
        timegroup_unit = input("Enter the time unit: ")
    
    if timegroup_unit.strip().upper() in ['Y', 'M', 'W', 'Q', 'S']:
        if timegroup_unit.strip().upper() == 'S' and not semester_mapping:
            print("Semester mapping is required for 'S' time grouping unit.")
            isValid = False
        else:
            isValid = True
    else:
        isValid = False
    
    return timegroup_unit.strip().upper() if isValid else get_timegroup_unit(gui=gui)

def prompt_user_column_selection(potential_date_columns, columns, gui=False):
    """
    Prompts the user to select a column from a list of potential date columns.

    Args:
        potential_date_columns (list): List of potential date columns.
        columns (list): List of all columns in the dataset.
        gui (bool): Whether to prompt the user in the tkinter GUI.

    Returns:
        str: The name of the selected column.
    """
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
    # Clear semester mapping if it exists from previous runs
    semester_mapping.clear()

    data_dict = get_data_dictionary()
    missing_required_columns = []
    incorrect_dtype_columns = []

    # Check for missing required columns and incorrect data types
    for col_name, properties in data_dict.items():
        if properties['required'] and col_name not in df.columns:
            missing_required_columns.append(col_name)
        elif col_name in df.columns and not pd.api.types.is_dtype_equal(df[col_name].dtype, properties['dtype']):
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