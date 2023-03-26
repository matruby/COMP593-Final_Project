'''
Library of useful functions for working with images.
'''
import ctypes 
import os 
import requests 

def download_image(image_url):
    """
    Downloads an image from a specified URL.
    DOES NOT SAVE THE IMAGE FILE TO DISK.
    """
    # Image binary retrieved from image url 
    img_download = requests.get(image_url)

    # Check if the download succeeded 
    if img_download.status_code == requests.codes.ok:
        return img_download.content 
    else:
        return None

def save_image_file(image_data, image_path):
    """Saves image data as a file on disk."""
    # Try to write the image to the image path given
    try:
        with open(image_path, 'wb') as img_file:
            img_file.write(image_data)
        return True
    except Exception:
        return False

def set_desktop_background_image(image_path):
    """Sets the desktop background image to a specific image."""
    # Try and set the desktop background
    if os.path.isfile(image_path):
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)
        return True
    else:
        return False 
    
def scale_image(image_size, max_size=(800, 600)):
    """Calculates the dimensions of an image scaled to a maximum width
    and/or height while maintaining the aspect ratio  

    Args:
        image_size (tuple[int, int]): Original image size in pixels (width, height) 
        max_size (tuple[int, int], optional): Maximum image size in pixels (width, height). Defaults to (800, 600).

    Returns:
        tuple[int, int]: Scaled image size in pixels (width, height)
    """
    ## DO NOT CHANGE THIS FUNCTION ##
    # NOTE: This function is only needed to support the APOD viewer GUI
    resize_ratio = min(max_size[0] / image_size[0], max_size[1] / image_size[1])
    new_size = (int(image_size[0] * resize_ratio), int(image_size[1] * resize_ratio))
    return new_size
