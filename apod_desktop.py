""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py [apod_date]

Parameters:
  apod_date = APOD date (format: YYYY-MM-DD)
"""
from apod_api import get_api_info, get_apod_image_url
from datetime import date
from image_lib import download_image, save_image_file, set_desktop_background_image
import hashlib
import inspect
import os
import re 
import sys
import sqlite3

# Global variables
image_cache_dir = None  # Full path of image cache directory
image_cache_db = None   # Full path of image cache database

def main():
    ## DO NOT CHANGE THIS FUNCTION ##
    # Get the APOD date from the command line
    apod_date = get_apod_date()    

    # Get the path of the directory in which this script resides
    script_dir = get_script_dir()

    # Initialize the image cache
    init_apod_cache(script_dir)

    # Add the APOD for the specified date to the cache
    apod_id = add_apod_to_cache(apod_date)

    # Get the information for the APOD from the DB
    db_response = get_apod_info(apod_id)

    # Set the APOD as the desktop background image
    if apod_id != 0:
        print(f"Setting Desktop to {db_response['file_path']}...", end='')
        set_correctly = set_desktop_background_image(db_response['file_path'])
        # Check if the desktop background was set correctly
        if set_correctly:
            print('success')
        else:
            print('failed')

def get_apod_date():
    # Variables for the current date and the date of the first APOD
    current_date = date.today()
    first_apod = date(1995, 6, 16)
    
    if len(sys.argv) == 1: 
        # Return current if no date is given
        apod_date = current_date

    elif len(sys.argv) == 2:
        # Checks if the given parameter is a valid date
        iso_format = re.match(r'\d{4}-\d{2}-\d{2}', sys.argv[1])
        if iso_format:
            # Seperate the date values into a list and convert the values to ints 
            split_args = sys.argv[1].split('-')
            proper_args = [int(val) for val in split_args]
            # Try converting the string to a date object 
            try: 
                apod_date = date(proper_args[0], proper_args[1], proper_args[2])
            except ValueError as err_msg:
                print(f'Error: Invalid Date format; {err_msg}\nScript execution aborted')
                sys.exit()

            # Checks if the date is not in the future 
            if apod_date > current_date:
                print(f"Error: APOD date cannot be in the future\nScript execution aborted")
                sys.exit()

            # Checks if the date is not earlier than the first APOD
            if apod_date < first_apod:
                print(f"Error: APOD date before first APOD\nScript execution aborted")
                sys.exit()
        else:
            print(f"Error: Invalid date format; Invalid ISOformat string: '{sys.argv[1]}'\nScript execution aborted")
            sys.exit()
                    
    else:
        print("Error: Too many arguments given\nScript execution aborted")
        sys.exit()

    return apod_date

def get_script_dir():
    """Determines the path of the directory in which this script resides

    Returns:
        str: Full path of the directory in which this script resides
    """
    ## DO NOT CHANGE THIS FUNCTION ##
    script_path = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
    return os.path.dirname(script_path)

def init_apod_cache(parent_dir):
    """Initializes the image cache by:
    - Determining the paths of the image cache directory and database,
    - Creating the image cache directory if it does not already exist,
    - Creating the image cache database if it does not already exist.
    
    The image cache directory is a subdirectory of the specified parent directory.
    The image cache database is a sqlite database located in the image cache directory.

    Args:
        parent_dir (str): Full path of parent directory    
    """
    global image_cache_dir
    global image_cache_db
    # Check if the image directory exists if not create it
    image_cache_dir = parent_dir + r'\images'

    print(f'Image cache directory: {image_cache_dir}') # Process Statement #1 

    if os.path.isdir(image_cache_dir):
        print('Image cache directory already exists.') # Process Statement #2
    else:
        print('Image cache directory created.') # Process Statement #2 
        os.mkdir(image_cache_dir)

    # Check if the image cache DB exists if not create it
    image_cache_db = image_cache_dir + r'\image_cache.db'

    print(f'Image cache DB: {image_cache_db}') # Process Statement #3

    if os.path.isfile(image_cache_db):
        print('Image cache DB already exists.') # Process Statement #4
    else:
        print('Image cache DB created.') # Process Statement #4 
        # Create the database 
        image_db = sqlite3.connect(image_cache_db)
        # Create the proper SQL table structure 
        db_cursor = image_db.cursor()
        create_apod_table_query = """CREATE TABLE IF NOT EXISTS apods 
        (
            id                  INTEGER PRIMARY KEY,
            apod_title          TEXT NOT NULL,
            apod_explanation    TEXT NOT NULL,
            apod_date           DATE NOT NULL,
            full_path           TEXT NOT NULL,
            hash                TEXT NOT NULL
        );
        """
        db_cursor.execute(create_apod_table_query)
        # Commit changes and close 
        image_db.commit()
        image_db.close()

        # cur.lastrowid will return the recently added ID

def add_apod_to_cache(apod_date):
    """Adds the APOD image from a specified date to the image cache.
     
    The APOD information and image file is downloaded from the NASA API.
    If the APOD is not already in the DB, the image file is saved to the 
    image cache and the APOD information is added to the image cache DB.

    Args:
        apod_date (date): Date of the APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if a new APOD is added to the
        cache successfully or if the APOD already exists in the cache. Zero, if unsuccessful.
    """
    # Print the APOD date selected 
    print("APOD date:", apod_date.isoformat())

    # Let the user know that an attempt is being made to get the apod info
    print(f'Getting {apod_date} APOD information from NASA...', end='')

    # Get the APOD Image Information 
    apod_info = get_api_info(apod_date)

    # Check if the api call was successful
    if apod_info:
        print('success')
    else:
        print('failed')

    # Tell the user the title of the APOD 
    print(apod_info['title']) 

    # Get the APOD image url 
    apod_img_url = get_apod_image_url(apod_info)

    # Tell the user the url of the APOD
    print(f'APOD URL: {apod_img_url}')

    # Tell the user that the image is trying to be downloaded
    print(f'Downloading image from {apod_img_url}...', end='')

    # Get the image downloaded 
    img_data = download_image(apod_img_url)

    # Check if the image download was successful
    if img_data:
        print('success')
    else:
        print('failed')

    # Get the hash of the downloaded image and notify the user of the hash
    img_hash = hashlib.sha256(img_data).hexdigest()
    print(f'APOD SHA-256: {img_hash}')    

    # Query the database to see if the image already exists
    query_result = get_apod_id_from_db(img_hash)

    # Check if the query returned anything
    if query_result == 0:
        print('APOD image is not already in cache.')
        # Assign the image file path and notify the user of the path 
        apod_file_path = determine_apod_file_path(apod_info['title'], apod_img_url)
        print(f'APOD file path: {apod_file_path}')

        # Tell the user that the image is trying to be saved 
        print(f'Saving image file as: {apod_file_path}...', end='')

        # Save the image to the image cache
        saved = save_image_file(img_data, apod_file_path)

        # Check if the image saved
        if saved:
            print('success')
        else:
            print('failed')

        # Tell the user that the APOD is being added to the db 
        print('Adding APOD to image cache DB...', end='')

        # Add the APOD information to the image_cache.db
        row_id = add_apod_to_db(apod_info['title'], apod_info['explanation'], apod_file_path, img_hash, apod_date)
        
        # Check if it was added to the db successfully
        if row_id:
            print('success')
            return row_id
        else: 
            print('failed')
            
    else:
        print('APOD image already in cache.')
        return query_result

def add_apod_to_db(title, explanation, file_path, sha256, date):
    """Adds specified APOD information to the image cache DB.
     
    Args:
        title (str): Title of the APOD image
        explanation (str): Explanation of the APOD image
        file_path (str): Full path of the APOD image file
        sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: The ID of the newly inserted APOD record, if successful.  Zero, if unsuccessful       
    """

        # Connect with the database and initialize the cursor 
    img_db = sqlite3.connect(image_cache_db)
    db_cursor = img_db.cursor()
    # Add the information for the APOD to the database 
    image_query = ("""
                    INSERT INTO apods 
                    (
                        apod_title, 
                        apod_explanation,
                        apod_date,
                        full_path,
                        hash
                    ) 
                    VALUES (?, ?, ?, ?, ?);
                    """)
    
    # Get the Row ID from the most recent execute 
    row_id = db_cursor.execute(image_query, (title, explanation, date, file_path, sha256))

    # Commit to the database and close 
    img_db.commit()
    img_db.close()
    
    if row_id.lastrowid:
        return row_id.lastrowid
    else:
        return 0

def get_apod_id_from_db(image_sha256):
    """Gets the record ID of the APOD in the cache having a specified SHA-256 hash value
    
    This function can be used to determine whether a specific image exists in the cache.

    Args:
        image_sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if it exists. Zero, if it does not.
    """
    # Connect to the database and initialize the cursor 
    img_db = sqlite3.connect(image_cache_db)
    db_cursor = img_db.cursor()

    # Query the database for the image hash 
    db_cursor.execute(f"SELECT id FROM apods WHERE hash='{image_sha256}'")
    query_result = db_cursor.fetchone()
    img_db.close()

    # If no image exists return 0 otherwise return the id of the image row 
    if query_result == None:
        return 0 
    else:
        return query_result[0]

def determine_apod_file_path(image_title, image_url):
    """Determines the path at which a newly downloaded APOD image must be 
    saved in the image cache. 
    
    The image file name is constructed as follows:
    - The file extension is taken from the image URL
    - The file name is taken from the image title, where:
        - Leading and trailing spaces are removed
        - Inner spaces are replaced with underscores
        - Characters other than letters, numbers, and underscores are removed

    For example, suppose:
    - The image cache directory path is 'C:\\temp\\APOD'
    - The image URL is 'https://apod.nasa.gov/apod/image/2205/NGC3521LRGBHaAPOD-20.jpg'
    - The image title is ' NGC #3521: Galaxy in a Bubble '

    The image path will be 'C:\\temp\\APOD\\NGC_3521_Galaxy_in_a_Bubble.jpg'

    Args:
        image_title (str): APOD title
        image_url (str): APOD image URL
    
    Returns:
        str: Full path at which the APOD image file must be saved in the image cache directory
    """
    # Remove unwanted characters from title 
    apod_title = re.sub("[?!.,;:\/@#$%^&*()']", "", image_title)
    # Properly format the title of the image 
    split_title = apod_title.split(" ")
    formatted_title = "_".join(split_title)
        
    # Image name for image cache 
    img_cache_name = formatted_title + '.jpg'
    img_abs_path = image_cache_dir + f'\\{img_cache_name}'

    # Return the proper absolute path for the new image 
    return img_abs_path

def get_apod_info(image_id):
    """Gets the title, explanation, and full path of the APOD having a specified
    ID from the DB.

    Args:
        image_id (int): ID of APOD in the DB

    Returns:
        dict: Dictionary of APOD information
    """
    # Connect to the database and initialize the cursor 
    img_db = sqlite3.connect(image_cache_db)
    db_cursor = img_db.cursor()

    # Query the database for the image_id 
    db_cursor.execute(f"SELECT apod_title, apod_explanation, apod_date, full_path FROM apods WHERE id='{image_id}'")
    query_result = db_cursor.fetchone()

    # Close the connection 
    img_db.close()

    # Put the required information into a dictionary
    apod_info = {
        'title': query_result[0],
        'explanation': query_result[1],
        'date': query_result[2],
        'file_path': query_result[3]
    }
    return apod_info

def get_all_apod_titles():
    """Gets a list of the titles of all APODs in the image cache

    Returns:
        list: Titles of all images in the cache
    """
    # Connect to the database and initialize the cursor 
    img_db = sqlite3.connect(image_cache_db)
    db_cursor = img_db.cursor()

    # Execute the query 
    db_cursor.execute("SELECT apod_title FROM apods")
    all_titles = db_cursor.fetchall()

    # Close the database and return all of the apod titles 
    img_db.close()
    return all_titles 

if __name__ == '__main__':
    main()