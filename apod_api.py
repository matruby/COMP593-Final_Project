'''
Library for interacting with NASA's Astronomy Picture of the Day API.
'''
import requests 

def get_api_info(apod_date):
    """Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.
    """
    # Make the initial request to the api
    apod_api_url = f'https://api.nasa.gov/planetary/apod?api_key=71TWdM7Y6l0U0QhSRBjuWQhfVWdUHKebAAuze8Vp&date={apod_date}&thumbs=True'
    resp_msg = requests.get(apod_api_url)

    # Checks if the request was succesful and converts the response to a dictionary
    if resp_msg.status_code == requests.codes.ok:
        apod_json = resp_msg.json()
        return apod_json
    else:
        return None

def get_apod_image_url(apod_info_dict):
    """
    Gets the URL of the APOD image from the dictionary of APOD information.
    If the APOD is an image, gets the URL of the high definition image.
    If the APOD is a video, gets the URL of the video thumbnail.
    """
    if 'hdurl' in apod_info_dict:
        img_download_url = apod_info_dict['hdurl']
        return img_download_url
    
    else:
        thmbnail_download_url = apod_info_dict['thumbnail_url']
        return thmbnail_download_url
    