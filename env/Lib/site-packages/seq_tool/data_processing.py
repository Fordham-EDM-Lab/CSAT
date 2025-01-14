from os import path
import pandas as pd

def dataframe_gen(input_df, categories, run_mode, category_folder, concurrency=False):
    """
    Generate a DataFrame from the input CSV file and filter based on categories and run mode, if applicable.

    Args:
        input_df (DataFrame): Input DataFrame from the CSV file.
        categories (list): List of category codes to filter. Ignored if 'Category' column is missing.
        run_mode (str): Run mode, either "separate" or "together." Ignored if 'Category' column is missing.
        category_folder (str): Directory where category-specific files will be stored.
        concurrency (bool): Whether to use EventOrder or just EventTime.

    Returns:
        dict or tuple: Results based on run mode if categories are present, otherwise a tuple for all data.
    """
    def process_data(df, category_folder):
        """Process the data, including sorting and resetting the index."""
        df = df.reset_index(drop=True)

        if concurrency:
            # Separate EventOrder into Year and Granularity for sorting
            df['Year'] = df['EventOrder'].astype(str).str[:4].astype(int)
            df['Granularity'] = df['EventOrder'].astype(str).str[4:].astype(int)

            # Sort by Year and Granularity
            sorted_df = df.sort_values(by=['Year', 'Granularity', 'Item'], ascending=[True, True, True])
        else:
            # Sort by EventTime if concurrency is not enabled
            sorted_df = df.sort_values(by=['EventTime'], ascending=True)

        grouped_df = sorted_df.groupby('ID').agg({
            'Item': lambda x: list(x),
            'EventOrder' if concurrency else 'EventTime': lambda x: list(x)
        }).reset_index()

        # Drop the ID column if needed
        grouped_df = grouped_df.drop(columns=['ID'])

        # Calculate transactions and insert delimiters
        transactions = len(grouped_df.index) + 1
        delimiter_df = insert_delimiter(grouped_df, category_folder, concurrency)

        return transactions, grouped_df, delimiter_df

    # Check if 'Category' exists in the dataframe
    if 'Category' in input_df.columns and categories:
        # Filter data based on categories
        input_df = input_df[input_df['Category'].isin(categories)]

        if run_mode == "separate":
            results = {}
            for category in categories:
                df_sub = input_df[input_df['Category'] == category]
                results[category] = process_data(df_sub, category_folder)
            return results
        elif run_mode == "together":
            return process_data(input_df, category_folder)
    else:
        # If 'Category' is not present, process all data together
        return process_data(input_df, category_folder)

def insert_delimiter(df, category_folder, concurrency):
    """
    Insert delimiters between different time groups in the event sequences.

    Args:
        df (DataFrame): The DataFrame containing the event items.
        category_folder (str): Directory where category-specific files will be stored.
        concurrency (bool): Whether to use EventOrder or EventTime.

    Returns:
        list: List of event sequences with inserted delimiters.
    """
    # Use the appropriate column for time-based sorting
    time_column = 'EventOrder' if concurrency else 'EventTime'

    # Convert the sequences to lists of strings
    items = [str(i).strip("[]").split(", ") for i in df['Item']]
    time_groups = [str(i).strip("[]").split(", ") for i in df[time_column]]

    K_itemset = []
    updated_elem1 = []
    part1 = " "

    for i in range(len(time_groups)):
        start = 0
        elem1 = items[i]
        time1 = time_groups[i]
        if len(time1) == 1:
            # Only one event in the sequence
            K_itemset.append(elem1[0])
        else:
            # All events in the same time group
            if len(set(time1)) == 1:
                part1 = ','.join(elem1)
                updated_elem1.append(part1)
            else:
                # Insert delimiters between different time groups
                for j in range(0, len(time1) - 1):
                    item1 = time1[j]  # Compare as strings (or lexicographically)
                    item2 = time1[j + 1]
                    if item1 < item2:  # Ensure correct ordering
                        part1 = ','.join(elem1[start:j + 1])
                        start = j + 1
                        updated_elem1.append(part1)
                part1 = ','.join(elem1[start:len(elem1)])
                updated_elem1.append(part1)

            item = '|'.join(updated_elem1)
            K_itemset.append(item)
            updated_elem1.clear()

    d = {'Sequence': K_itemset}
    new_df = pd.DataFrame(d)

    transactions_delimiter_file_path = path.join(category_folder, 'transactions_delimiter.csv')
    new_df.to_csv(transactions_delimiter_file_path, index=False)

    return K_itemset