import math
import os

def clear_screen():
    # Clears the terminal screen depending on the operating system
    os.system('cls' if os.name == 'nt' else 'clear')

def universal_calculator():
    # Safe environment dictionary to restrict eval() for security
    safe_env = {
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "pi": math.pi, "e": math.e, "abs": abs
    }
    
    history = []

    while True:
        clear_screen()
        print("=" * 55)
        print("        UNIVERSAL ADVANCED CALCULATOR (CLI)        ")
        print("=" * 55)
        print(" Commands:")
        print("  - Type any math expression (e.g., 5 * (3 + 2) )")
        print("  - Type 'history' to view previous calculations")
        print("  - Type 'help' to see all available math functions")
        print("  - Type 'exit' to close the application")
        print("=" * 55)
        
        # Display the last calculation result if available
        if history:
            print(f" Last Result: {history[-1]}")
            print("-" * 55)

        user_input = input("\n> ").strip().lower()

        # Handle Commands
        if user_input in ['exit', 'quit']:
            print("\nGoodbye!")
            break
            
        elif user_input == 'help':
            print("\n--- AVAILABLE FUNCTIONS ---")
            print(" Operators: +, -, *, /, ** (power), % (modulo)")
            print(" Functions: sqrt(x), sin(x), cos(x), tan(x), log(x)")
            print(" Constants: pi, e")
            input("\nPress Enter to return to calculator...")
            
        elif user_input == 'history':
            print("\n--- CALCULATION HISTORY ---")
            if not history:
                print(" No calculations yet.")
            else:
                for item in history:
                    print(f" {item}")
            input("\nPress Enter to return to calculator...")
            
        elif user_input:
            try:
                # Calculate the result safely
                result = eval(user_input, {"__builtins__": None}, safe_env)
                
                # Format the result to remove unnecessary decimals if it's an integer
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                    
                # Add to history
                history.append(f"{user_input} = {result}")
            except Exception:
                print("\n[!] Error: Invalid Input. Type 'help' to see the rules.")
                input("Press Enter to try again...")

if __name__ == "__main__":
    universal_calculator()
