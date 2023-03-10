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
from apod_api import get_apod_info, get_apod_image_url
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
    apod_info = get_apod_info(apod_id)

    # Set the APOD as the desktop background image
    if apod_id != 0:
        set_desktop_background_image(apod_info['file_path'])

def get_apod_date():
    # Variables for the current date and the date of the first APOD
    current_date = date.today()
    first_apod = date(1995, 6, 16)
    
    # {REQ-1} 
    if len(sys.argv) == 1: # {REQ-4}
        # Return current if no date is given
        apod_date = current_date

    elif len(sys.argv) == 2: # {REQ-2}
        # Checks if the given parameter is in ISO format
        try: # {REQ-3} 
            apod_date = date.fromisoformat(str(sys.argv[1]))
        except ValueError:
            print("Date Isn't In ISO Format - YYYY-MM-DD\n! CODE EXITING !")
            sys.exit()

        # Checks if the date is not in the future 
        if apod_date > current_date:
            print(f"The Date {apod_date} is in the Future; Use a Valid Date\n! CODE EXITING !")
            sys.exit()

        # Checks if the date is not earlier than the first APOD
        if apod_date < first_apod:
            print(f"{apod_date} is before the first APOD; There is no APOD to be found\n! CODE EXITING !")
            sys.exit()
               
    else:
        print("Too many Arguments Given\n! CODE EXITING !")
        sys.exit()

    # If all the tests passed return the date 
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
    print(image_cache_dir)
    if os.path.isdir(image_cache_dir):
        print('Image cache directory already exists.')
    else:
        print('Image cache directory created.')
        os.mkdir(image_cache_dir)

    # Check if the image cache DB exists if not create it
    image_cache_db = image_cache_dir + r'\image_cache.db'
    if os.path.isfile(image_cache_db):
        print('Image cache DB already exists.')
    else:
        print('Image cache DB created.')
        # Create the database 
        image_db = sqlite3.connect(image_cache_db)
        # Create the proper SQL table structure 
        db_cursor = image_db.cursor()
        db_cursor.execute("""CREATE TABLE apods (
                            apod_title text,
                            apod_explanation text,
                            apod_date text,
                            full_path text,
                            hash text
                            )""")
        image_db.commit()
        image_db.close()

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
    print("APOD date:", apod_date.isoformat())
    # Get the APOD Image Information 
    apod_info = get_apod_info(apod_date)
    apod_img_url = get_apod_image_url(apod_info)

    # Get the image downloaded 
    img_link = f'https://api.nasa.gov/planetary/apod?api_key=71TWdM7Y6l0U0QhSRBjuWQhfVWdUHKebAAuze8Vp&date={apod_date}&thumbs=True'
    img_data = download_image(img_link)

    # Get the hash of the downloaded image 
    img_hash = hashlib.sha256(img_data).hexdigest()

    # Query the database to see if the image already exists
    img_db = sqlite3.connect(image_cache_db)
    db_cursor = img_db.cursor()
    db_cursor.execute(f"SELECT * FROM apods WHERE hash={img_hash}")
    query_result = db_cursor.fetchone()
    db_cursor.close()

    # Check if the query returned anything
    if query_result == None:
        apod_file_path = determine_apod_file_path(apod_info, apod_img_url)

        # Save the image to the image cache
        save_image_file(img_data.content, apod_file_path)

        # Add the Apod information to the image_cache.db
        add_apod_to_db(apod_info['title'], apod_info['explanation'], apod_file_path, img_hash, apod_date)

    else:
        print('APOD Image already in cache.')
    return 0

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
    try:
        img_db = sqlite3.connect(image_cache_db)
        db_cursor = img_db.cursor()

        # Add the information for the APOD to the database 
        db_cursor.execute("INSERT INTO apods VALUE (?, ?, ?, ?, ?)".format(title, explanation, file_path, sha256, date))
        
        # Commit the changes and close 
        img_db.commit()
        img_db.close()
    except Exception:
        return 0
    else:
        return 1

def get_apod_id_from_db(image_sha256):
    """Gets the record ID of the APOD in the cache having a specified SHA-256 hash value
    
    This function can be used to determine whether a specific image exists in the cache.

    Args:
        image_sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if it exists. Zero, if it does not.
    """
    # TODO: Complete function body
    return 0

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
    # TODO: Complete function body
    # Remove unwanted characters from title 
    apod_title = re.sub("[?!.,;:\/@#$%^&*()']", "", image_title)
    # Properly format the title of the image 
    split_title = apod_title.split(" ")
    formatted_title = "_".join(split_title)
        
    # Image name for image cache 
    img_cache_name = formatted_title + image_url[-4:]
    img_abs_path = image_cache_dir + f'\\{img_cache_name}'

    return img_abs_path

def get_apod_info(image_id):
    """Gets the title, explanation, and full path of the APOD having a specified
    ID from the DB.

    Args:
        image_id (int): ID of APOD in the DB

    Returns:
        dict: Dictionary of APOD information
    """
    # TODO: Query DB for image info
    # TODO: Put information into a dictionary
    apod_info = {
        #'title': , 
        #'explanation': ,
        'file_path': 'TBD',
    }
    return apod_info

def get_all_apod_titles():
    """Gets a list of the titles of all APODs in the image cache

    Returns:
        list: Titles of all images in the cache
    """
    # TODO: Complete function body
    # NOTE: This function is only needed to support the APOD viewer GUI
    return

if __name__ == '__main__':
    main()