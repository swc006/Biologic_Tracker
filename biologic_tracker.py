"""
This script manages and optimizes the scheduling of biologic preparations and tasks.
It performs the following functions:

1. Adjust Date to Previous Weekday:
   - The `get_previous_weekday` function adjusts a given date
   to a previous weekday. 

2. Distribute Preparation Volume:
   - The `distribute_volume` function splits the total volume
   of a preparation into batches, ensuring that no single batch
   exceeds the maximum allowed volume (500L).

3. Get Working Days:
   - The `get_working_days` function returns a list of all
   working days (Monday to Friday) between two given dates, inclusive.

4. Find Available Days:
   - The `find_available_days` function identifies available days
   for scheduling a preparation. It ensures that no more than two
   preparations are scheduled per day and that buffers and medias
   are not prepared on the same day.

5. Load Task Expirations from Excel:
   - The `load_task_expirations_from_excel` function reads an
   Excel file to load task expiration times into a dictionary, 
   where each task is associated with a timedelta object
   representing its expiration period.

6. Load Task Dates from Excel:
   - The `load_task_dates_from_excel` function reads an Excel
   file to load the start dates of tasks into a dictionary.

7. Load Preparations from Excel:
   - The `load_excel_into_dict` function reads an Excel file
   to load preparation details (preparation name and volume)
   into a dictionary organized by task names.

8. Load Preparation Details from Excel:
   - The `load_prep_details_from_excel` function reads an Excel
   file to load preparation details, including type
   (Media or Buffer) and expiration time, into a dictionary.

9. Optimize Schedule:
   - The `optimize_schedule` function generates an initial
   schedule by considering task start dates, preparation details,
   and product expiration times. It ensures that preparations
   are scheduled within their valid periods and that volume
   constraints are respected.

10. Consolidate Preparations:
    - The `consolidate_preps` function further optimizes the
    schedule by consolidating preparations to minimize the
    number of days used while adhering to constraints on the
    maximum number of preparations and volume per day.

11. Consolidate Preparations with Constraints:
    - The `consolidate_preps_with_constraints` function refines
    the consolidation process by considering additional constraints
    to ensure the schedule is feasible.

12. Main Execution:
    - The `Main` function loads data from Excel files,
    optimizes the schedule, consolidates the preparations,
    and prints the final schedule. It combines tasks and
    preparations into a calendar format for easy visualization.

This process ensures that biologic preparations and tasks
are scheduled efficiently, adhering to volume constraints
and minimizing the number of preparation days,
while respecting product expiration dates.
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import pandas as pd
# pylint: disable=line-too-long

def get_previous_weekday(given_date: datetime.date) -> datetime.date:
    """
    Adjusts the given date to a previous weekday
    If the given date is Monday, returns the previous Friday.
    Otherwise, subtracts two days to get the previous weekday.

    Parameters:
    given_date (date): The date for which the previous weekday is calculated.

    Returns:
    date: The previous weekday date.
    """

    weekday = given_date.weekday()  # Monday is 0, Sunday is 6
    if weekday == 0:  # If it's Monday
        return given_date - timedelta(days=3)  # Go back to the previous Friday
    if weekday == 1: # If it's Tuesday
        return given_date - timedelta(days=4) # Go back to the previous Friday
    return given_date - timedelta(days=2)

def distribute_volume(prep: str, total_volume: int) -> List[Tuple[str, int]]:
    """
    Distributes the total volume of a preparation into batches,
    ensuring that no single batch exceeds the maximum allowed volume.

    Parameters:
    prep (str): The name or identifier of the preparation (e.g., media or buffer).
    total_volume (int): The total volume of the preparation that needs to be distributed.

    Returns:
    list of tuples: A list of tuples where each tuple contains the
                    preparation name and the volume for that batch.
                    Each batch will have a volume of 500L or less.
    """

    batches = []
    max_volume = 500  # Maximum volume for a single batch

    # Distribute the total volume into batches
    while total_volume > 0:
        if total_volume >= max_volume:
            batches.append((prep, max_volume))
            total_volume -= max_volume
        else:
            batches.append((prep, total_volume))
            total_volume = 0

    return batches

def get_working_days(start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
    """
    Returns a list of all working days (Monday to Friday) between the start date and end date.

    Parameters:
    start_date (date): The start date of the range.
    end_date (date): The end date of the range.

    Returns:
    List[date]: A list of dates representing the working days within the specified range.
    """

    # Calculate the total number of days between start_date and end_date
    total_days = (end_date - start_date).days + 1

    # Generate a list of all dates in the range
    all_dates = [start_date + timedelta(days=x) for x in range(total_days)]

    # Filter out only the weekdays (Monday to Friday)
    weekday_dates = [date for date in all_dates if date.weekday() < 5]

    return weekday_dates

def find_available_days(schedule: Dict[datetime.date, List[Tuple[str, int]]], current_type: str, date_list: List[datetime.date], prep_details: Dict[str, Dict[str, str]]) -> List[datetime.date]:
    """
    Finds and returns a list of available days for scheduling a preparation.

    Parameters:
    schedule (Dict[date, List[Tuple[str, int]]]): The current schedule, where keys are dates and values are lists of tuples containing preparation names and 
    their volumes.
    current_type (str): The type of the current preparation (e.g., 'media' or 'buffer').
    date_list (List[datetime.date]): A list of dates to check for availability.
    prep_details (Dict[str, Dict[str, str]]): A dictionary containing details of preparations, where keys are preparation names and values are dictionaries 
    with preparation details including their types.

    Returns:
    List[datetime.date]: A list of available days for scheduling the current preparation.
    """

    available_days = []
    for day in date_list:
        if day not in schedule:
            available_days.append(day)  # Add the day if nothing is scheduled yet
        elif len(schedule[day]) < 2:
            # Check if all preps scheduled on this day are of the same type as the current prep type
            if all(prep_details[prep]['type'] == current_type for prep, _ in schedule[day]):
                available_days.append(day)
    return available_days

def load_task_expirations_from_excel(filepath: str, sheet_name: str) -> Dict[str, timedelta]:
    """
    Loads task expiration information from an Excel file and returns it as a dictionary.

    Parameters:
    filepath (str): The path to the Excel file.
    sheet_name (str): The name of the sheet containing the task expiration data.

    Returns:
    Dict[str, timedelta]: A dictionary where keys are task names and values are expiration times as timedelta objects.
    """

    df = pd.read_excel(filepath, sheet_name=sheet_name, usecols="G,I", skiprows=1)
    df = df.dropna(subset=['Process', 'Hold Time'])
    # Rename columns for clarity
    df.columns = ['Task', 'Expiration']

    # Create the dictionary for task expirations
    task_expirations = {}
    for _, row in df.iterrows():
        task = row['Task']
        # Convert expiration time to timedelta object
        expiration_time = timedelta(days=int(row['Expiration']))
        # Add the task expiration time to the dictionary
        task_expirations[task] = expiration_time

    return task_expirations

def load_task_dates_from_excel(filepath: str, sheet_name: str) -> Dict[str, datetime.date]:
    """
    Loads task start dates from an Excel file and returns them as a dictionary.

    Parameters:
    filepath (str): The path to the Excel file.
    sheet_name (str): The name of the sheet containing the task start date data.

    Returns:
    Dict[str, datetime.date]: A dictionary where keys are task names and values are start dates.
    """

    df = pd.read_excel(filepath, sheet_name=sheet_name, usecols="N,O", skiprows=1)
    df = df.dropna(subset=['Task', 'Start Date'])
    # Rename columns for clarity
    df.columns = ['Task', 'Start Date']

    # Create the dictionary for task start dates
    task_dates = {}
    for _, row in df.iterrows():
        task = row['Task']
        # Convert date to datetime object if not already
        start_date = pd.to_datetime(row['Start Date']).date()
        # Add the task start date to the dictionary
        task_dates[task] = start_date

    return task_dates


def load_excel_into_dict(filepath: str, sheet_name: str) -> Dict[str, List[Tuple[str, int]]]:
    """
    Loads task details from an Excel file and returns them as a dictionary.

    Parameters:
    filepath (str): The path to the Excel file.
    sheet_name (str): The name of the sheet containing the task data.

    Returns:
    Dict[str, List[Tuple[str, int]]]: A dictionary where keys are task names and values are lists of tuples 
    containing 
    preparation names and volumes.
    """

    df = pd.read_excel(filepath, sheet_name=sheet_name, usecols="A:E", skiprows=1)
    df = df.dropna(subset=['Task', 'Prep', 'Volume (L)'])

    # Create the dictionary
    tasks_dict = {}
    for _, row in df.iterrows():
        task = row['Task']
        prep_name = row['Prep']
        volume = int(row['Volume (L)'])

        # Add the prep details to the corresponding task in the dictionary
        if task not in tasks_dict:
            tasks_dict[task] = []
        tasks_dict[task].append((prep_name, volume))

    return tasks_dict

def load_prep_details_from_excel(filepath: str, sheet_name: str) -> Dict[str, Dict[str, object]]:
    """
    Loads preparation details from an Excel file and returns them as a dictionary.

    Parameters:
    filepath (str): The path to the Excel file.
    sheet_name (str): The name of the sheet containing the preparation details.

    Returns:
    Dict[str, Dict[str, object]]: A dictionary where keys are preparation names and values are dictionaries containing the type and expiration time.
    """

    df = pd.read_excel(filepath, sheet_name=sheet_name, usecols="G,C,H", skiprows=0)
    df = df.dropna(subset=['PN Name', 'Expiration', 'Is Media?'])

    # Rename columns for clarity
    df.columns = ['Expiration', 'Preps', 'Is Media?']

    # Create the dictionary for prep details
    prep_details = {}
    for _, row in df.iterrows():
        prep_name = row['Preps']
        expiration = timedelta(days=int(row['Expiration']))
        type_ = "Media" if row['Is Media?'] == 'Y' else "Buffer"

        # Add the prep details to the dictionary
        prep_details[prep_name] = {"type": type_, "Expiration": expiration}

    return prep_details

def optimize_schedule(task_dates: Dict[str, datetime.date], tasks: Dict[str, List[Tuple[str, int]]], prep_details: Dict[str, Dict[str, object]], product_expirations: Dict[str, timedelta]) -> Dict[datetime.date, List[Tuple[str, int]]]:
    """
    Optimizes the schedule for tasks based on their dates, preparation details, and product expiration times.

    Parameters:
    task_dates (Dict[str, datetime.date]): A dictionary where keys are task names and values are their start dates.
    tasks (Dict[str, List[Tuple[str, int]]]): A dictionary where keys are task names and values are lists of tuples 
    containing preparation names and volumes.
    prep_details (Dict[str, Dict[str, object]]): A dictionary where keys are preparation names and values are 
    dictionaries 
    containing the type and expiration 
    time.
    product_expirations (Dict[str, timedelta]): A dictionary where keys are task names and values are the product 
    expiration 
    times as timedelta objects.

    Returns:
    Dict[date, List[Tuple[str, int]]]: A dictionary where keys are dates and values are lists of tuples containing 
    preparation names and volumes scheduled for 
    those dates.
    """
    schedule = {}
    for task, task_date in task_dates.items():
        requirements = tasks.get(task, [])
        #product_expiration_date = task_date + product_expirations[task]
        for prep, volume in requirements:
            prep_type = prep_details[prep]['type']
            expiration_delta = prep_details[prep]['Expiration']

            # Set latest date as one or two days before the task
            end_date = get_previous_weekday(task_date)
            # Calculate start_date as the task_date minus the prep's expiration period
            start_date = task_date - expiration_delta  # Ensure start_date is not in the past

            batches = distribute_volume(prep, volume)
            working_days = get_working_days(start_date, end_date)
            available_days = find_available_days(schedule, prep_type, working_days, prep_details)

            for batch in batches:
                if not available_days:
                    print(f"No available days for {prep} with batch size {batch[1]}")
                    continue
                # Schedule the batch on the last available day to allow maximum flexibility
                prod_day = available_days.pop()
                if not schedule.get(prod_day):
                    schedule[prod_day] = []
                schedule[prod_day].append((prep, batch[1]))

    return schedule

def consolidate_preps(schedule: Dict[datetime.date, List[Tuple[str, int]]], prep_details: Dict[str, Dict[str, object]], max_preps_per_day: int = 2, max_volume_per_day: int = 500) -> Dict[datetime.date, List[Tuple[str, int]]]:
    """
    Consolidates preparations in the schedule to minimize the number of days used while respecting constraints on the 
    maximum number of preparations and volume 
    per day.

    Parameters:
    schedule (Dict[datetime.date, List[Tuple[str, int]]]): The initial schedule with preparations.
    prep_details (Dict[str, Dict[str, object]]): A dictionary containing preparation details including their type and 
    expiration time.
    max_preps_per_day (int): The maximum number of preparations allowed per day. Default is 2.
    max_volume_per_day (int): The maximum volume allowed per day for each type of preparation. Default is 500.

    Returns:
    Dict[date, List[Tuple[str, int]]]: An optimized schedule with consolidated preparations.
    """

    all_preps = {}
    for day, preps in schedule.items():
        for prep, volume in preps:
            if prep not in all_preps:
                all_preps[prep] = {'total_volume': 0, 'type': prep_details[prep]['type'], 'earliest_day': day}
            all_preps[prep]['total_volume'] += volume
            if day < all_preps[prep]['earliest_day']:
                all_preps[prep]['earliest_day'] = day

    # Create a new schedule, trying to fit preps into as few days as possible
    optimized_schedule = {}
    for prep, details in all_preps.items():
        volume_remaining = details['total_volume']
        earliest_possible_day = details['earliest_day']
        day = earliest_possible_day

        while volume_remaining > 0:
            if day not in optimized_schedule:
                optimized_schedule[day] = []

            # Calculate the available volume for this day
            current_volume_on_day = sum(v for p, v in optimized_schedule[day] if prep_details[p]['type'] == details['type'])
            available_volume = max_volume_per_day - current_volume_on_day

            if len(optimized_schedule[day]) < max_preps_per_day and available_volume > 0:
                volume_to_add = min(volume_remaining, available_volume)
                optimized_schedule[day].append((prep, volume_to_add))
                volume_remaining -= volume_to_add

            # Move to the next day if there's still volume remaining
            if volume_remaining > 0:
                day += timedelta(days=1)

    return optimized_schedule

def consolidate_preps_with_constraints(schedule: Dict[datetime.date, List[Tuple[str, int]]], prep_details: Dict[str, Dict[str, object]], max_preps_per_day: int = 2, max_volume_per_day: int = 500) -> Dict[datetime.date, List[Tuple[str, int]]]:
    """
    Consolidates preparations in the schedule to minimize the number of days used while respecting constraints on the 
    maximum number of preparations and volume per day.

    Parameters:
    schedule (Dict[datetime.date, List[Tuple[str, int]]]): The initial schedule with preparations.
    prep_details (Dict[str, Dict[str, object]]): A dictionary containing preparation details including their type and 
    expiration time.
    max_preps_per_day (int): The maximum number of preparations allowed per day. Default is 2.
    max_volume_per_day (int): The maximum volume allowed per day for each type of preparation. Default is 500.

    Returns:
    Dict[datetime.date, List[Tuple[str, int]]]: An optimized schedule with consolidated preparations.
    """
    # Sort the days in the schedule to ensure we are processing in order
    sorted_days = sorted(schedule.keys())
    optimized_schedule = {}

    # Temporary storage for preps, tracking the earliest day they can be combined without expiring
    temp_storage = {}

    for day in sorted_days:
        preps = schedule[day]
        for prep, volume in preps:
            if prep not in temp_storage:
                temp_storage[prep] = {'volume': 0, 'earliest_day': day, 'type': prep_details[prep]['type']}

            # Update total volume and reset earliest day if this entry is earlier
            temp_storage[prep]['volume'] += volume
            if day < temp_storage[prep]['earliest_day']:
                temp_storage[prep]['earliest_day'] = day

    # Attempt to place each prep on its earliest possible day or combine when possible
    for prep, details in temp_storage.items():
        day = details['earliest_day']
        volume_remaining = details['volume']

        while volume_remaining > 0:
            if day not in optimized_schedule:
                optimized_schedule[day] = []

            # Check if we can add to this day
            current_volume = sum(v for p, v in optimized_schedule[day] if prep_details[p]['type'] == details['type'])
            if len(optimized_schedule[day]) < max_preps_per_day and current_volume + volume_remaining <= max_volume_per_day:
                optimized_schedule[day].append((prep, volume_remaining))
                break  # Break because we've placed all the remaining volume
            else:
                # Find the next possible day to place the remaining volume
                available_volume = min(max_volume_per_day - current_volume, volume_remaining)

                if available_volume > 0 and len(optimized_schedule[day]) < max_preps_per_day:
                    optimized_schedule[day].append((prep, available_volume))
                    volume_remaining -= available_volume

                # Move to the next day
                day += timedelta(days=1)

    return optimized_schedule

# Calculate the optimized schedule
def main(filepath):
    """
    Runs the whole process
    """
    prep_details = load_prep_details_from_excel(filepath, 'Prep DB')
    product_expirations = load_task_expirations_from_excel(filepath,'Main')
    tasks = load_excel_into_dict(filepath, 'Preps to Use')
    task_dates = load_task_dates_from_excel(filepath, 'Main')
    print('task dates',task_dates,'tasks',tasks,'prepdetails',prep_details,'prodexp',product_expirations)
    final_schedule = optimize_schedule(task_dates, tasks, prep_details, product_expirations)

    # Combine tasks and preps in one calendar
    consolidated_schedule = consolidate_preps(final_schedule, prep_details)
    consolidated_schedule_new = consolidate_preps_with_constraints(consolidated_schedule, prep_details, max_preps_per_day=2, max_volume_per_day=500)

    print(consolidated_schedule_new)

    calendar_entries = {}
    for date, preps in consolidated_schedule_new.items():
        date_key = date
        calendar_entries.setdefault(date_key, []).extend(
            f"Prep: {prep} {volume}L ({prep_details[prep]['type']})" for prep, volume in preps)

    for task, date in task_dates.items():
        date_key = date
        calendar_entries.setdefault(date_key, []).append(f"Task: {task}")

    # Print the calendar
    for date in sorted(calendar_entries):
        print(f"{date}:")
        for entry in calendar_entries[date]:
            print(f"  - {entry}")
main(filepath = r'C:\Users\kgfj640\Documents\GPFN\GPFN_Scheduling.xlsm')
