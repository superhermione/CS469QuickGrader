import os
import csv
import pandas as pd
import math
import shutil


class GradeYear:
    def __init__(self, year, gradeyear_location=None, periods=None):
        self.year = str(year)
        if gradeyear_location is None:
            self.create_folder_on_desktop()
        else:
            self.path = os.path.join(gradeyear_location, self.year)

        self.periods = []
        if periods is not None:
            for period in periods:
                self.add_period_to_folder(period)

    def get_name(self):
        return self.year

    def get_period(self, name_of_period):
        if len(self.periods) == 0:
            return None
        else:
            for period in self.periods:
                if period.get_name() == name_of_period:
                    return period
        return None

    def print_periods(self):
        if not self.periods:
            print("No periods found.")
            return

        print("Periods:")
        for i, period in enumerate(self.periods, start=1):
            print(f"{i}. {period.get_name()}")

    def create_folder_on_desktop(self):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.path = os.path.join(desktop_path, self.year)
        os.makedirs(self.path, exist_ok=True)

    def add_period_to_folder(self, period):
        self.periods.append(period)
        self.move_period_to_gradeyear(period)

    def move_period_to_gradeyear(self, period):
        new_location = os.path.join(self.path, period.name)

        # Check if the new location is the same as the current location
        if new_location == period.path:
            raise ValueError("Destination folder is the same as the current location.")

        # Check if the destination folder already exists and is different from the current location
        if os.path.exists(new_location) and new_location != period.path:
            raise ValueError("Destination folder already exists.")

        # Move the period to the new location
        shutil.move(period.path, new_location)

        # Update the period's path to the new location
        period.path = new_location

        # Update the paths of self.original_data and self.graded_folder
        period.original_data_folder_path = os.path.join(period.path, "original_data")
        period.graded_folder_path = os.path.join(period.path, "Graded Assignments")

    def bulk_import_edpuzzle_assignment(self, csv_path):
        # Iterate through each period and import performance data for the respective usernames
        for period in self.periods:
            period.edpuzzle_filtering(csv_path)
            period.transfer_all_graded_to_gradebook()

class Period:
    def __init__(self, name, path=None):
        self.name = name

        if path is None:
            self.path = os.path.join(os.path.expanduser("~"), "Downloads", self.name)
        else:
            self.path = path

        # create period folder if it doesn't exist
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # create empty subfolders: original_data -- raw website provided CSV File folder
        #                          Graded Assignments -- filtered assignments for grading purposes
        self.original_data_folder_path = os.path.join(self.path, "original_data")
        if not os.path.exists(self.original_data_folder_path):
            os.makedirs(self.original_data_folder_path)
        self.graded_folder_path = os.path.join(self.path, "Graded Assignments")
        if not os.path.exists(self.graded_folder_path):
            os.makedirs(self.graded_folder_path)

        # create CSV file with USERNAME column (for confidential use, no real First & Last name column)
        csv_file_path = os.path.join(self.path, "gradebook.csv")
        with open(csv_file_path, mode='w', newline='') as csv_file:
            fieldnames = ['USERNAME']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

    def get_name(self):
        return self.name

    def print_gradebook_assignments(self):
        csv_file_path = os.path.join(self.path, "gradebook.csv")
        df = pd.read_csv(csv_file_path)
        columns = df.columns.tolist()

        # Find the index of the first assignment column after 'USERNAME'
        assignment_start_index = columns.index('USERNAME') + 1

        if assignment_start_index == len(columns):
            print("No assignments found.")
        else:
            print("Assignments:")
            for i, column in enumerate(columns[assignment_start_index:], start=1):
                print(f"{i}. {column}")

    def copy_period_tree(self, new_location):
        # Create a new instance of the Period class for the copied tree
        copied_period = Period(self.name)

        # Copy the entire Period tree to the new location
        shutil.copytree(self.path, new_location)

        # Update the path of the copied_period to the new location
        copied_period.path = new_location

        # Update the paths of the original_data_folder and graded_folder
        copied_period.original_data_folder_path = os.path.join(new_location, "original_data")
        copied_period.graded_folder_path = os.path.join(new_location, "Graded Assignments")

        # Update the csv_file_path (gradebook.csv) to the new location
        copied_period.csv_file_path = os.path.join(new_location, "gradebook.csv")

        return copied_period

    def import_new_assignment(self, file_path, new_csv_name):
        # read CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)

        # Filter grades: drop unwanted columns
        columns_to_drop = [col for col in df.columns if col not in ['Username', 'Score']]
        df.drop(columns_to_drop, axis=1, inplace=True)

        # sort by score: from the highest to the lowest, for later use
        df.sort_values(by=['Score'], ascending=False, inplace=True)

        # save graded assignments CSV file
        new_file_path = os.path.join(self.graded_folder_path, new_csv_name)
        df.to_csv(new_file_path, index=False)

    def edpuzzle_filtering(self, raw_data_path):
        # get the basename of the raw data file
        raw_data_name = os.path.splitext(os.path.basename(raw_data_path))[0]

        # create original_data folder if it doesn't exist
        if not os.path.exists(self.original_data_folder_path):
            os.makedirs(self.original_data_folder_path)

        # create a copy of the raw data file in the original_data folder
        with open(raw_data_path, mode='r') as f1, open(
                os.path.join(self.original_data_folder_path, f"original_{raw_data_name}.csv"), mode='w',
                newline='') as f2:
            reader = csv.reader(f1)
            writer = csv.writer(f2)
            writer.writerows(reader)

        # create a new CSV file in the Graded Assignments folder with the same name as the raw data file
        graded_file_path = os.path.join(self.graded_folder_path, f"{raw_data_name}.csv")
        with open(graded_file_path, mode='w', newline='') as csv_file:
            fieldnames = ['Username', 'Score']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

        # read the raw data into a pandas DataFrame
        raw_data_df = pd.read_csv(raw_data_path)

        # find column with header that matches 'Username' and 'Grade (out of 100)' (case-insensitive)
        username_col_index = None
        score_col_index = None
        with open(raw_data_path, mode='r') as input_file:
            reader = csv.reader(input_file)
            headers = next(reader)
            for i, h in enumerate(headers):
                if h.upper() == 'USERNAME':
                    username_col_index = i
                elif h.upper() == 'GRADE (OUT OF 100)':
                    score_col_index = i
        if username_col_index is None or score_col_index is None:
            raise ValueError("Could not find columns named 'Username' and 'Grade (out of 100)' in the raw data file.")

        # iterate through rows of the raw data and insert the valid pairs of username and score into the new CSV file
        with open(graded_file_path, mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            for index, row in raw_data_df.iterrows():
                username = row.iloc[username_col_index]
                score = row.iloc[score_col_index]
                if pd.notnull(username) and pd.notnull(score):
                    writer.writerow([username, score])

    def add_usernames_to_gradebook(self, csv_path):
        # find column with header that matches 'USERNAME' (case-insensitive)
        with open(csv_path, mode='r') as input_file:
            reader = csv.reader(input_file)
            headers = next(reader)
            username_col_index = next((i for i, h in enumerate(headers) if h.upper() == 'USERNAME'), None)

        if username_col_index is None:
            raise ValueError("Could not find a column named 'USERNAME' in the CSV file.")

        # read existing CSV file into a pandas DataFrame
        csv_file_path = os.path.join(self.path, "gradebook.csv")
        df = pd.read_csv(csv_file_path)

        # get unique usernames from the specified column
        usernames = set(pd.read_csv(csv_path, usecols=[username_col_index]).iloc[:, 0])

        # add new usernames to the existing DataFrame and save to CSV file
        new_df = pd.DataFrame({'USERNAME': list(usernames)})
        df = pd.concat([df, new_df], ignore_index=True, sort=False)
        df.sort_values(by=['USERNAME'], inplace=True)
        df.to_csv(csv_file_path, index=False)

    def transfer_assignment_scores_to_gradebook(self, assignment_path):
        # get the basename of the assignment file
        assignment_name = os.path.splitext(os.path.basename(assignment_path))[0]

        # read the assignment scores into a pandas DataFrame
        df = pd.read_csv(assignment_path)

        # check if the assignment name matches an existing column header in the gradebook CSV
        csv_file_path = os.path.join(self.path, "gradebook.csv")
        gradebook_df = pd.read_csv(csv_file_path)
        if assignment_name in gradebook_df.columns:
            raise ValueError(f"The assignment '{assignment_name}' already exists in the gradebook.")

        # create a new column in the gradebook CSV with the assignment name as the header
        gradebook_df[assignment_name] = ""

        # map and insert the scores into the new column based on the 'USERNAME' column
        username_col_index = next((i for i, h in enumerate(gradebook_df.columns) if h.upper() == 'USERNAME'), None)
        if username_col_index is None:
            raise ValueError("Could not find a column named 'USERNAME' in the gradebook CSV file.")
        for index, row in df.iterrows():
            username = row.iloc[username_col_index]
            score = row['Score']
            gradebook_df.loc[gradebook_df['USERNAME'].str.upper() == username.upper(), assignment_name] = score

        # sort the gradebook by 'USERNAME'
        gradebook_df.sort_values(by=['USERNAME'], ascending=True, inplace=True)

        # save the updated gradebook CSV file
        gradebook_df.to_csv(csv_file_path, index=False)

    def transfer_all_graded_to_gradebook(self):
        graded_folder_path = self.graded_folder_path
        csv_files = [f for f in os.listdir(graded_folder_path) if
                     os.path.isfile(os.path.join(graded_folder_path, f)) and f.lower().endswith('.csv')]

        for csv_file in csv_files:
            # check if the assignment name already exists in the gradebook CSV
            assignment_name = os.path.splitext(csv_file)[0]
            csv_file_path = os.path.join(self.path, "gradebook.csv")
            gradebook_df = pd.read_csv(csv_file_path)
            if assignment_name not in gradebook_df.columns:
                # transfer the assignment scores to the gradebook
                assignment_path = os.path.join(graded_folder_path, csv_file)
                self.transfer_assignment_scores_to_gradebook(assignment_path)

    def sort_gradebook_by_username(self):
        # read existing CSV file into a pandas DataFrame
        csv_file_path = os.path.join(self.path, "gradebook.csv")
        df = pd.read_csv(csv_file_path)

        # sort the gradebook by 'USERNAME'
        df.sort_values(by=['USERNAME'], ascending=True, inplace=True)

        # save the updated gradebook CSV file
        df.to_csv(csv_file_path, index=False)

    def bump_to_hundred(self, assignment_name):
        # read existing CSV file into a pandas DataFrame
        csv_file_path = os.path.join(self.path, "gradebook.csv")
        df = pd.read_csv(csv_file_path)

        # check if the assignment name matches an existing column header in the gradebook CSV
        if assignment_name not in df.columns:
            raise ValueError(f"The assignment '{assignment_name}' does not exist in the gradebook.")

        # find the highest grade in the assignment column
        max_grade = df[assignment_name].max()

        # subtract the max grade from 100 to get the bump value
        bump_value = 100 - max_grade

        # add the bump value to each grade in the assignment column
        df[assignment_name] = df[assignment_name].apply(lambda x: x + bump_value)

        # save the updated gradebook CSV file
        df.to_csv(csv_file_path, index=False)

    def drop_lowest(self):
        # read in the gradebook CSV as a pandas DataFrame
        csv_file_path = os.path.join(self.path, "gradebook.csv")
        df = pd.read_csv(csv_file_path)

        # iterate through each row of the DataFrame and find the lowest non-zero grade
        for index, row in df.iterrows():
            # find the average grade for the row
            grade_sum = 0
            grade_count = 0
            for col, grade in row.items():
                if col == "USERNAME":
                    continue
                if pd.notnull(grade):
                    grade_sum += grade
                    grade_count += 1
            average_grade = grade_sum / grade_count if grade_count > 0 else 0  # add check for grade_count > 0

            # find the lowest grade in the row
            lowest_grade = float('inf')
            for col, grade in row.items():
                if col == "USERNAME":
                    continue
                if pd.notnull(grade):
                    if grade < lowest_grade:
                        lowest_grade = grade

            # replace the lowest grade with the ceiling-rounded average grade
            for col, grade in row.items():
                if col == "USERNAME":
                    continue
                if pd.notnull(grade):
                    if grade == lowest_grade:
                        new_grade = math.ceil(average_grade)
                        df.at[index, col] = new_grade

        # sort the gradebook by 'USERNAME'
        df.sort_values(by=['USERNAME'], inplace=True)

        # save the updated gradebook CSV file
        df.to_csv(csv_file_path, index=False)


if __name__ == '__main__':
    run = True
    gradeyears = []
    periods = []

    def get_gradeyear(name_of_gradeyear):
        if len(gradeyears) == 0:
            return None
        else:
            for gradeyear in gradeyears:
                if gradeyear.get_name() == name_of_gradeyear:
                    return gradeyear
        return None

    def get_period(name_of_period):
        if len(periods) == 0:
            return None
        else:
            for period in periods:
                if period.get_name() == name_of_period:
                    return period
        return None

    while run is True:
        print("What would you like to do?")
        print("1. Start a new Grading Year")
        print("2. Work with existing Grading Year")
        choice = input("Enter your choice: ")
        if choice == "1":
            this_gradeyear_name = input("Provide a name for Grade Year (can be the year itself): ")
            gradeyears.append(GradeYear(this_gradeyear_name))
            this_gradeyear = get_gradeyear(this_gradeyear_name)
            print("Now you need to add a period.")
            this_period_name = input("Provide a name for this Period (can be the period number): ")
            periods.append(Period(this_period_name))
            user_provided_assignment_path = input("Copy and paste path to an assignment to scrape usernames: ")
            assignment_with_r = r"{}".format(user_provided_assignment_path)
            this_period = get_period(this_period_name)
            this_period.edpuzzle_filtering(assignment_with_r)
            this_period.add_usernames_to_gradebook(assignment_with_r)
            this_gradeyear.add_period_to_folder(this_period)
            keep_adding_assignment_data = True
            while keep_adding_assignment_data is True:
                print("Upload more assignment data?")
                more_assignment_data = input("1 = yes\n2 = no  \n")
                if more_assignment_data == '2':
                    keep_adding_assignment_data is False
                    break
                else:
                    new_assignment_data = input("Copy and paste path to assignment data:  ")
                    new_assignment_data_with_r = r"{}".format(new_assignment_data)
                    this_period.edpuzzle_filtering(new_assignment_data_with_r)
            print("Ok, adding assignment data to Period's gradebook...")
            this_period.transfer_all_graded_to_gradebook()
            print("Done.")

            within_period_options = True
            while within_period_options is True:
                print("What would you like to do?")
                print("1. drop the lowest grade for students")
                print("2. curve up to 100 an assignment?")
                print("3. add a universal assignment to all periods in gradebook")
                print("4. add another period")
                print("5. quit")
                option_choice = input("enter number of choice:   ")
                choices = ['1','2','3','4']
                if option_choice == '1':
                    print('Choose from among the periods')
                    this_gradeyear.print_periods()
                    period_name = input("type the period name that corresponds:    ")
                    selected_period = this_gradeyear.get_period(period_name)
                    selected_period.drop_lowest()

                if option_choice == '2':
                    print('Choose from among the periods')
                    this_gradeyear.print_periods()
                    period_name = input("type the period name that corresponds:    ")
                    selected_period = this_gradeyear.get_period(period_name)
                    selected_period.print_gradebook_assignments()
                    assignment_choice = input("Enter the name of the assignment: ")
                    # Subtract the maximum grade from 100 and add the difference to each grade in the assignment column
                    selected_period.bump_to_hundred(assignment_choice)
                if option_choice == '3':
                    bulk_assignment = input('copy and paste path to the universal assignment:  ')
                    bulk_assignment_with_r = r"{}".format(bulk_assignment)
                    this_gradeyear.bulk_import_edpuzzle_assignment(bulk_assignment_with_r)
                if option_choice == '4':
                    new_period_name = input("Provide a name for this Period (can be the period number): ")
                    periods.append(Period(new_period_name))
                    provided_assignment_path = input("Copy and paste path to an assignment to scrape usernames: ")
                    assignment_w_r = r"{}".format(provided_assignment_path)
                    new_period = get_period(new_period_name)
                    new_period.edpuzzle_filtering(assignment_w_r)
                    new_period.add_usernames_to_gradebook(assignment_w_r)
                    this_gradeyear.add_period_to_folder(new_period)
                    continue_adding_assignments = True
                    while continue_adding_assignments is True:
                        print("Upload more assignment data?")
                        more_assignments_data = input("1 = yes\n2 = no  \n")
                        if more_assignments_data == '2':
                            continue_adding_assignments is False
                            break
                        else:
                            new_ass_data = input("Copy and paste path to assignment data:  ")
                            new_ass_data_with_r = r"{}".format(new_ass_data)
                            new_period.edpuzzle_filtering(new_ass_data_with_r)
                    print("Ok, adding assignment data to Period's gradebook...")
                    new_period.transfer_all_graded_to_gradebook()
                    print("Done.")

                    in_period_options = True
                    while in_period_options is True:
                        print("Would you like to do?")
                        print("1. drop the lowest grade for students")
                        print("2. curve up to 100 an assignment?")
                        print("3. add a universal assignment to all periods in gradebook")
                        print("4. add another period")
                        print("5. quit")
                        new_choice = input("enter number of choice:   ")
                        new_choices = ['1', '2', '3', '4']
                        if new_choice == '1':
                            print('Choose from among the periods')
                            this_gradeyear.print_periods()
                            period_name = input("type the period name that corresponds:    ")
                            selected_period = this_gradeyear.get_period(period_name)
                            selected_period.drop_lowest()
                        if new_choice == '2':
                            print('Choose from among the periods')
                            this_gradeyear.print_periods()
                            period_name = input("type the period name that corresponds:    ")
                            selected_period = this_gradeyear.get_period(period_name)
                            selected_period.print_gradebook_assignments()
                            assignment_choice = input("Enter the name of the assignment: ")
                            # Subtract the maximum grade from 100 and add the difference to each grade in the assignment column
                            selected_period.bump_to_hundred(assignment_choice)

                        if new_choice == '3':
                            bulk_ass = input('copy and paste path to the universal assignment:  ')
                            bulk_ass_with_r = r"{}".format(bulk_ass)
                            this_gradeyear.bulk_import_edpuzzle_assignment(bulk_ass_with_r)

                        if option_choice == '4':
                            in_period_options = False
                            break
                        if option_choice == '5':
                            print("Grading completed. Bye Bye.")
                            run = False
                            break
                        if option_choice not in choices:
                            print("invalid choice")

                if option_choice == '5':
                    print("Grading completed. Bye Bye.")
                    run = False
                    break
                if option_choice not in choices:
                    print("invalid choice")

        else:
            run = False
            break





