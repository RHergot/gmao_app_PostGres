import os

LOG_FILE = os.path.join(os.path.dirname(__file__), '../../logs/app.log')

def clean_log_file():
    try:
        with open(LOG_FILE, 'w') as f:
            f.truncate(0)
        print(f"Log file '{LOG_FILE}' cleaned.")
    except Exception as e:
        print(f"Failed to clean log file: {e}")

if __name__ == "__main__":
    clean_log_file()
