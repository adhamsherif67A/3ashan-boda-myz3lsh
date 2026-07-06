import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_grade_points(grade):
    # Standard GPA scale
    grades = {'A+': 4.0, 'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
              'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0}
    return grades.get(grade.upper().strip(), -1)

def calculate_gpa(subjects):
    total_points = 0
    total_credits = 0
    for sub in subjects:
        total_points += sub['credits'] * get_grade_points(sub['grade'])
        total_credits += sub['credits']
    
    if total_credits == 0: return 0.0, 0
    return total_points / total_credits, total_credits

def main():
    clear_screen()
    print("=" * 60)
    print("           ULTIMATE GPA CALCULATOR SYSTEM           ")
    print("=" * 60)
    
    # 1. Getting Student Info
    name = input(" Enter Student Name (e.g., Ibrahim Amr): ").strip()
    if not name: name = "Student"
    
    while True:
        try:
            age = int(input(" Enter Age: "))
            current_semester = int(input(" Enter Current Semester (e.g., 5): "))
            break
        except ValueError:
            print(" [!] Please enter valid numbers.")

    total_cumulative_points = 0
    total_cumulative_credits = 0

    # Loop through semesters up to the current one
    for sem in range(1, current_semester + 1):
        clear_screen()
        print("=" * 60)
        print(f" Student: {name} | Semester: {sem}/{current_semester}")
        if total_cumulative_credits > 0:
            cgpa = total_cumulative_points / total_cumulative_credits
            print(f" Current CGPA: {cgpa:.2f}")
        print("=" * 60)
        
        print(f"\n How would you like to enter data for Semester {sem}?")
        print(" 1. Enter the final GPA for this semester directly.")
        print(" 2. Enter subjects one by one to calculate it.")
        
        while True:
            choice = input("\n Enter your choice (1 or 2): ").strip()
            if choice in ['1', '2']: break
            print(" [!] Invalid choice.")

        if choice == '1':
            # Option 1: Direct GPA Entry
            while True:
                try:
                    sem_gpa = float(input(" Enter Semester GPA (0.0 to 4.0): "))
                    if not (0.0 <= sem_gpa <= 4.0):
                        print(" [!] GPA must be between 0.0 and 4.0")
                        continue
                    sem_credits = float(input(" Enter Total Credit Hours for this semester: "))
                    
                    total_cumulative_credits += sem_credits
                    total_cumulative_points += (sem_gpa * sem_credits)
                    print("\n [+] Semester added successfully!")
                    input(" Press Enter to continue...")
                    break
                except ValueError:
                    print(" [!] Please enter valid numbers.")

        else:
            # Option 2: Calculate Subject by Subject
            subjects = []
            while True:
                clear_screen()
                print("-" * 60)
                print(f" Semester {sem} - Detailed Entry")
                print("-" * 60)
                
                # Show current semester status
                if subjects:
                    print(" Current Subjects:")
                    for idx, sub in enumerate(subjects):
                        print(f" [{idx+1}] {sub['name']} | Credits: {sub['credits']} | Grade: {sub['grade'].upper()}")
                    
                    current_gpa, current_credits = calculate_gpa(subjects)
                    print("-" * 30)
                    print(f" Live Semester GPA: {current_gpa:.2f} (Total Credits: {current_credits})")
                    print("-" * 30)
                else:
                    print(" No subjects added yet.")
                
                print("\n Options:")
                print(" 1. Add Subject")
                print(" 2. Edit a Subject (Grade/Credits)")
                print(" 3. Finish this Semester")
                
                action = input("\n Choose an action (1/2/3): ").strip()
                
                if action == '1':
                    sub_name = input(" Subject Name (e.g., Thermodynamics): ").strip()
                    try:
                        sub_credits = float(input(" Credit Hours (e.g., 3): "))
                        sub_grade = input(" Grade (A+, A, B+, etc.): ").strip().upper()
                        
                        if get_grade_points(sub_grade) == -1:
                            print(" [!] Invalid Grade entered. Try again.")
                            input(" Press Enter...")
                            continue
                            
                        subjects.append({'name': sub_name, 'credits': sub_credits, 'grade': sub_grade})
                    except ValueError:
                        print(" [!] Invalid credit hours. Try again.")
                        input(" Press Enter...")
                        
                elif action == '2':
                    if not subjects:
                        print(" [!] No subjects to edit.")
                        input(" Press Enter...")
                        continue
                        
                    try:
                        sub_idx = int(input(" Enter subject number to edit: ")) - 1
                        if 0 <= sub_idx < len(subjects):
                            print(f" Editing: {subjects[sub_idx]['name']}")
                            new_credits = float(input(" New Credit Hours: "))
                            new_grade = input(" New Grade (A+, B, etc.): ").strip().upper()
                            
                            if get_grade_points(new_grade) != -1:
                                subjects[sub_idx]['credits'] = new_credits
                                subjects[sub_idx]['grade'] = new_grade
                            else:
                                print(" [!] Invalid grade format.")
                        else:
                            print(" [!] Subject number not found.")
                        input(" Press Enter...")
                    except ValueError:
                        print(" [!] Invalid input.")
                        input(" Press Enter...")
                        
                elif action == '3':
                    if not subjects:
                        print(" [!] You must add at least one subject, or choose direct GPA entry.")
                        input(" Press Enter...")
                        continue
                        
                    sem_gpa, sem_credits = calculate_gpa(subjects)
                    total_cumulative_credits += sem_credits
                    total_cumulative_points += (sem_gpa * sem_credits)
                    print(f"\n [+] Semester {sem} Finished! Final Semester GPA: {sem_gpa:.2f}")
                    input(" Press Enter to continue to next step...")
                    break

    # Final Result Screen
    clear_screen()
    print("=" * 60)
    print("                 FINAL REPORT                 ")
    print("=" * 60)
    print(f" Student Name : {name}")
    print(f" Total Semesters : {current_semester}")
    print(f" Total Credits Evaluated : {total_cumulative_credits}")
    
    if total_cumulative_credits > 0:
        final_cgpa = total_cumulative_points / total_cumulative_credits
        print(f" FINAL CUMULATIVE GPA (CGPA) : {final_cgpa:.2f} / 4.0")
    else:
        print(" FINAL CGPA : N/A (No credits entered)")
    print("=" * 60)

if __name__ == "__main__":
    main()
