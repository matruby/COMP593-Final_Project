import sys
from datetime import date

def get_apod_date():
    try:
        apod_date = date.fromisoformat(str(sys.argv[1]))
    except ValueError:
        print("Date Not In ISO Format - YYYY-MM-DD\n! CODE EXITING !")
        sys.exit()

    return apod_date



if __name__ == '__main__':
    print(date.today())
