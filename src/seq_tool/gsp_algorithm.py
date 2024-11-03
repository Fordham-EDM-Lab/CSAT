from os import path, makedirs
import time
from collections import defaultdict
from datetime import datetime
from .data_processing import dataframe_gen
from .utils import filter_and_export_to_csv, export_summary_to_file, generate_hash

def join_itemsets(itemset):
    """
    Perform the join operation of the Apriori algorithm by comparing different itemsets.

    Args:
        itemset (list): List of itemsets to join.

    Returns:
        list: List of joined itemsets.
    """
    unionset = []
    res = [i.strip("[]").split("|") for i in itemset]
    res2 = [i.strip("[]").replace("|", ",").split(",") for i in itemset]

    for i in range(len(res)):
        element1 = res[i]
        elem1 = res2[i]
        total = len(element1)
        for k in range(i+1, len(res)):     
            element2 = res[k]
            elem2 = res2[k]
            index = 0
            join_items = []
            join_items2 = []
            join_items3 = []
            status = 0
            sub_status = 0
            if len(element1) == len(element2):
                for j in range(len(element1)):
                    block1 = element1[j]
                    block1 = block1.strip("[]").split(",")
                    block2 = element2[j]
                    block2 = block2.strip("[]").split(",")
                    
                    if len(block1) == len(block2):
                        if j == len(element1) -1:
                            if block1[0:(len(block1)-1)] == block2[0:(len(block1)-1)]:
                                index += 1
                        else:    
                            if block1[0:(len(block1))] == block2[0:(len(block1))]:
                                index += 1
                
                # If number of matched blocks == number of total blocks, then perform join   
                # Three Join Cases: 
                # Case 1: a,b,c  -- a,b,d  --> a,b,c,d
                # Case 2: a,b,c  -- a,b|d  --> a,b,c|d
                # Case 3: a,b|c  -- a,b|d  --> a,b|c,d AND a,b,c|d AND a,b,d|c
                           
                if index == total: 
                    block_items = []
                    joined_block = []
                    unsort_block = []
                    
                    #Example: 1000, 1100| 1200, 1300, 1400  -- 1000, 1100| 1200, 1300, 1600 --> 1000, 1100| 1200, 1300, 1400, 1600
                    unsort_block.append(block1[-1])                  # Last item of itemset 1 - ex) 1400 
                    unsort_block.append(block2[-1])                  # Last item of itemset 2 - ex) 1600
                    sort_block = ','.join(sorted(unsort_block))      # Join together with ',' and sort - ex) 1400, 1600 
                    
                    list1 = '|'.join(element1[0: len(element1)-1])   # Join Element1 back together minus the last block -- ex) 1000, 1100
                    join_items.append(list1)                         
                    
                    if len(block1) > 1:  # If the last block has multiple items ex) a| b, c 
                        joined_block = ','.join(block1[0: len(block1)-1]) # Join the last block minus the last item -- ex) 1200, 1300
                        block_items.append(joined_block)                  # Add last block to block_items
                        
                        
                    block_items.append(sort_block)                 # Add the last two joined items to block_items
                    final_block = ','.join(block_items)            # Join block_items with a comma -- ex) 1200, 1300, 1400, 1600
                    
                    join_items.append(final_block)                 
                    result = '|'.join(join_items)                   # ex) -- 1000, 1100|1200, 1300, 1400, 1600
                    
                    unionset.append(result.rstrip(',').lstrip('|'))             # add to list of return items 
                    
                    
                    # Case 2: last delimotor is '|'  ex) elem1: a, b | c  -- elem2: a, b | d 
                    if len(block1) == 1:      # last block has only one item
                        part1 = '|'.join(res[i])  # join together all of elem1
                        join_items2.append(part1)  # add elem1 to join_items
                        join_items2.append(block2[-1])  # single element of final block2
                        result2 = '|'.join(join_items2) # result1 == a, b | c | d
                        unionset.append(result2.rstrip(',').strip('"'))
                    
                        status = 1 
                        sub_status = 1
                       
            # equal number of elements but different number of semesters 
            # EX: itemset1: a, b, c | e   --- itemset2: a, b, c, d --- result: a, b, c, d | e 
            elif len(elem1) == len(elem2) and (len(element1)-len(element2) == 1 or len(element2)-len(element1) == 1):
                if len(element1) > len(element2):
                    for j in range(len(element1)-1):   # all except last item/block
                        block1 = element1[j]
                        block1= block1.strip("[]").split(",")
                        
                        if index == (len(element1) -2):
                            block2 = element2[j]
                            block2= block2.strip("[]").split(",")
                            if block1[0:(len(block1))] == block2[0:(len(block2)-1)]:
                                block1 = element1[j+1]
                                if block1 != block2[-1]:
                                    index += 1                
                        else:
                            block2 = element2[j]
                            block2= block2.strip("[]").split(",")
                            if len(block1) == len(block2) and block1[0:(len(block1))] == block2[0:(len(block2))]:
                                index += 1                    
                    if index == len(element1)-1:
                        status = 1
                        sub_status = 1
                        block1 = element1[-1].strip("[]").split(",")
                # element2 = '1400|2000' AND element1 = '1400,1600' 
                elif len(element2) > len(element1):
                    for j in range(len(element2)-1):   # all except last item/block
                        block1 = element2[j]
                        block1= block1.strip("[]").split(",")
                        if index == (len(element2) -2):
                            block2 = element1[j]
                            block2= block2.strip("[]").split(",")
                            if block1[0:(len(block1))] == block2[0:(len(block2)-1)]:
                                block1 = element2[j+1]
                                if block1 != block2[-1]:
                                    index += 1                
                        else:
                            block2 = element1[j]
                            block2= block2.strip("[]").split(",")
                            if len(block1) == len(block2) and block1[0:(len(block1))] == block2[0:(len(block2))]:
                                index += 1                    
                    if index == len(element2)-1:
                        status = 1
                        sub_status = 2
                        block1 = element2[-1].strip("[]").split(",")    
            # EX: itemset1: a, b, c | e   --- itemset2: a, b, c, d --- result: a, b, c, d | e 
            if status == 1: 
                if sub_status == 1:
                    part2 = '|'.join(res[k])   # join together all of elem2 (a,b,c,d)
                elif sub_status == 2:
                    part2 = '|'.join(res[i])   # join together all of elem1
                join_items3.append(part2)      # add elem2 to join2_items
                join_items3.append(block1[-1]) # single element of final (e)
                result3 = '|'.join(join_items3)  # (a,b,c,d|e)
                unionset.append(result3.rstrip(',').strip('"'))
    return unionset        


def prune_candidates(count, minsupport):
    """
    Prune the candidates that do not meet the minimum support.

    Args:
        count (dict): Dictionary containing the count of occurrences for each itemset.
        min_support (int): Minimum support threshold.

    Returns:
        list: List of pruned itemsets.
    """        
    itemset = []
    for i in count:
        if count[i] >= minsupport:
            itemset.append(i)     
    return itemset

def count_subset(candidate, length, df):
    """
    Count occurrences of candidate subsets in the data.

    Args:
        candidate (list): List of candidate itemsets.
        length (int): Length of the itemsets.
        df (DataFrame): DataFrame containing the data.

    Returns:
        dict: Dictionary containing the count of occurrences for each candidate subset.
    """
    Lk = defaultdict(int)
    res = [i.split("|") for i in df]
    candidate_set = [i.replace(" ","").split("|")  for i in candidate]   
   
    for row in range(len(res)):
        data = res[row] 
        for item in range(0, length):         
            item1 = candidate_set[item]                         
            z = 0 
            counter = 0
            if len(data) >= len(item1):
                for i in range(len(item1)):        
                    block1= item1[i]                
                    block1 = block1.split(",")
                    for j in range(z, len(data)):   
                        block2 = data[j]
                        block2 = block2.split(",")
                        if len(block2) >= len(block1):
                            w = 0
                            sub_counter = 0
                            for k in range(len(block1)):
                                for l in range(w, len(block2)):
                                    if block1[k] == block2[l]:
                                        sub_counter += 1
                                        if w != len(block2):
                                            w = l + 1
                                        break
                            if sub_counter == len(block1):
                                counter +=1 
                                if z != len(data):
                                    z = j + 1 
                                break
                if counter == len(item1):
                    key = (candidate[item])
                    Lk[key] +=1
    return Lk                
                            
def apriori_algorithm(candidate_itemsets, min_support, k_value, dataframe): 
    """
    Runs the Apriori algorithm to determine frequent itemsets.

    Args:
        candidate_itemsets (list): List of candidate itemsets.
        min_support (float): Minimum support threshold.
        k_value (int): The current size of the itemsets being processed.
        dataframe (pd.DataFrame): The DataFrame containing the transaction data.

    Returns:
        dict: A dictionary containing frequent itemsets and their counts.
    """
    results_dict = {}
    
    while candidate_itemsets:                                         
        column_name = f"Freq {k_value}-Itemsets"
        itemset_count = count_subset(candidate_itemsets, len(candidate_itemsets), dataframe)               
        frequent_itemsets = prune_candidates(itemset_count, min_support)
        candidate_itemsets = join_itemsets(frequent_itemsets) 

        if candidate_itemsets:                                  
            results_dict[column_name] = itemset_count
        
        k_value += 1
    
    return results_dict

def run_apriori_on_data(df, new_df, transactions, minsupport, department_folder, department_name, start_time, output_path):
    """
    Run the Apriori algorithm on the given data and export the results.

    Args:
        df (pd.DataFrame): The original DataFrame containing the data.
        new_df (pd.DataFrame): The DataFrame after preprocessing.
        transactions (int): Total number of transactions in the data.
        minsupport (float): Minimum support value for the Apriori algorithm.
        department_folder (str): The directory where the results will be stored.
        department_name (str): The name of the department being processed.
        start_time (float): The start time for measuring runtime.
        output_path (str): The path to store the output file.

    Returns:
        tuple: A tuple containing the name of the exported CSV file, the results dictionary, and the runtime.
    """
    k = 2

    single_count = defaultdict(int)
    set_count = defaultdict(int)
    df['Item'] = df['Item'].astype(str)
    row = [i.strip("[]").replace(", ", ",").split(",") for i in df['Item']]

    for i in range(len(row)):
        elem = row[i]
        key = len(row[i])
        set_count[key] += 1
        for item in range(len(elem)):
            single_count[elem[item]] += 1

    freq_singles = prune_candidates(single_count, minsupport)
    Ck = join_itemsets(freq_singles)

    department_hash = generate_hash(department_name + str(minsupport))
    export_file_name = f"{department_hash}_{minsupport}.csv"

    department_export_dict = apriori_algorithm(Ck, minsupport, k, new_df)
    k_count = filter_and_export_to_csv(department_export_dict, minsupport, transactions, path.join(department_folder, export_file_name))
    session = (time.time() - start_time)
    export_summary_to_file(single_count, k_count, transactions, session, path.join(output_path, 'Export.txt'))

    return export_file_name, department_export_dict, session

def run_separate_mode(departments, min_supports, input_df, output_path, run_mode_var, concurrency_var):
    """
    Execute the Apriori algorithm for each department separately.

    Args:
        departments (list): List of department codes to process.
        min_supports (list): List of minimum support values.
        input_df (DataFrame): The input DataFrame containing the data to be processed.
        output_path (str): The directory where the results will be stored.
        run_mode_var (str): The running mode, should be "separate" in this case.

    Returns:
        tuple: A tuple containing the results dictionary and log entries.
    """
    export_dict = {}
    log_entries = []
    all_data = dataframe_gen(input_df, departments, run_mode_var, output_path, concurrency_var)

    for department in departments:
        department_folder = path.join(output_path, department)
        makedirs(department_folder, exist_ok=True)

        department_transactions, department_df, department_new_df = all_data[department]

        for minsupport in min_supports:
            start_time = time.time()

            export_file_name, department_export_dict, session = run_apriori_on_data(
                department_df, department_new_df, department_transactions, minsupport, department_folder, department, start_time, output_path
            )

            export_dict_key = f"{department}_{minsupport}"
            export_dict[export_dict_key] = department_export_dict
            log_entries.append(f"Department: {department}, Min Support: {minsupport}, Runtime: {session:.2f} seconds, CSV: {export_file_name}")

    return export_dict, log_entries

def run_together_mode(departments, min_supports, input_df, output_path, run_mode_var, concurrency_var):
    """
    Execute the Apriori algorithm for all departments together.

    Args:
        departments (list): List of department codes to process.
        min_supports (list): List of minimum support values.
        input_df (DataFrame): The input DataFrame containing the data to be processed.
        output_path (str): The directory where the results will be stored.
        run_mode_var (str): The running mode, should be "together" in this case.

    Returns:
        tuple: A tuple containing the results dictionary and log entries.
    """
    export_dict = {}
    log_entries = []

    departments_hash = generate_hash(f"{','.join(departments)}")
    min_supports_hash = generate_hash(f"{','.join(map(str, min_supports))}")
    department_folder_name = f"{departments_hash}_{min_supports_hash}"
    department_folder = path.join(output_path, department_folder_name)
    makedirs(department_folder, exist_ok=True)

    transactions, df, new_df = dataframe_gen(input_df, departments, run_mode_var, department_folder, concurrency_var)

    for minsupport in min_supports:
        start_time = time.time()

        export_file_name, department_export_dict, session = run_apriori_on_data(
            df, new_df, transactions, minsupport, department_folder, department_folder_name, start_time, output_path
        )

        export_dict_key = f"{department_folder_name}_{minsupport}"
        export_dict[export_dict_key] = department_export_dict
        log_entries.append(f"Min Support: {minsupport}, Runtime: {session:.2f} seconds, CSV: {export_file_name}")

    return export_dict, log_entries


def execute_tool(input_df, support_thresholds, departments, run_mode, concurrency_var, output_dir):
    """
    Main function to execute the tool based on the selected mode. It orchestrates the execution of the algorithm,
    stores the results in the specified output directory, and logs the details of the execution.

    Args:
        input_df (DataFrame): The input DataFrame containing the data to be processed.
        support_thresholds (list): List of minimum support values to be used in the Apriori algorithm.
        departments (list): List of department codes to be processed. If run_mode is "separate", each department is processed separately.
        run_mode (str): The running mode. Should be either "separate" or "together", depending on whether the departments are processed separately or together.
        output_dir (str): The directory where the results, including the log file, will be stored.

    Returns:
        dict: A dictionary containing the results of the Apriori algorithm execution for the given parameters.
    """
    results = {}

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_folder = f"Run_{timestamp}"
    output_path = path.join(output_dir, output_folder)
    makedirs(output_path, exist_ok=True)

    log_entries = []

    if run_mode == "separate":
        results, log_entries = run_separate_mode(departments, support_thresholds, input_df, output_path, run_mode, concurrency_var)
    elif run_mode == "together":
        results, log_entries = run_together_mode(departments, support_thresholds, input_df, output_path, run_mode, concurrency_var)

    log_filepath = path.join(output_path, "run_log.txt")
    with open(log_filepath, 'w') as log_file:
        for entry in log_entries:
            log_file.write(entry + '\n')

    return results
