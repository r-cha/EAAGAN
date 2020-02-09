import os
import requests
import bs4
import zipfile
import shutil
import cv2
import numpy as np

from pathlib import Path


# TODO: Change the location of these defaults, and allow them to be more easily changed.
# Perhaps go object-oriented with it, take command line args, 
# or simply provide these as default values for named parameters in a function call.
USGS_BASE_URL = 'https://eros.usgs.gov'
EAA_BASE_URL = USGS_BASE_URL + '/image-gallery/earth-art'
COLLECTIONS = [1, 2, 3, 4, 5, 6]
OUTPUT_DIRECTORY = Path("./EarthAsArt")
OUTPUT_DIMENSIONS = (512, 512)

def collection_url(collection_number):
    """ Determine the url of the given collection"""
    return EAA_BASE_URL + '-' + str(collection_number)

def download_page(url):
    """ Request a page, then return a BeautifulSoup object of that page """
    res = requests.get(url)
    res.raise_for_status()
    resSoup = bs4.BeautifulSoup(res.text, features="html.parser")
    return resSoup

def access_collection(col_num):
    """ Get a list of the image landing page URLs for a given collection """
    # TODO: The results are paginated, so... scroll down? request them all? idk.
    # High priority, because right now we do NOT download "all" the images.
    # ALTERNATIVE: Navigate to the first image in the collection,
    # then get the download link and hit "next" all the way through the collection
    print(f"Accessing collection {col_num}...")

    url = collection_url(col_num)
    collectionSoup = download_page(url)
    img_elements = collectionSoup.select('.view-content a')
    img_urls = [USGS_BASE_URL + e.get('href') for e in img_elements]
    return img_urls

def access_image(url):
    """ Find the download page url on the landing page of an image """
    imgSoup = download_page(url)
    button = imgSoup.select_one('.btn-hallow')
    url = button.get('href')
    return url

def download_image_zip(url):
    """ Download the zip file for an image and return teh path to the zip """
    usgsSoup = download_page(url)
    button = usgsSoup.select_one('input[type="button"]')
    download_url = button.get('onclick') # this url is prepended with "window.location='"
    download_url = download_url[17:-1]   # so be sure to slice it all fancy (or sloppy)

    res = requests.get(download_url)
    img_name = os.path.basename(url.split('/')[-2])
    zip_path = OUTPUT_DIRECTORY / (img_name+".zip")

    print(f"    Downloading image zip {img_name}")

    imgFile = open(zip_path, 'wb')
    for chunk in res.iter_content(100000):
        imgFile.write(chunk)
    imgFile.close()

    return zip_path

def unzip_image(zip_path):
    """ Unzip to the output dir, then delete the zip. """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        img_name = zip_path.stem
        print(f"      Unzipping {img_name}")
        zip_ref.extractall(OUTPUT_DIRECTORY)
        print(f"      Cleaning {img_name}")
    os.remove(zip_path)

def fix_collection_4():
    """ EAA4 is a little wonky. Lets handle that. """
    print("Fixing collection 4 location...")
    source = OUTPUT_DIRECTORY / "EAA4_Final_JPGS"
    files = list(source.glob('*'))
    for f in files:
        f.rename(OUTPUT_DIRECTORY / f.name)
        print(f"    {f.stem} moved")
    
    source.rmdir()

def download_all():
    """ Download the complete collection of images """
    # access each collection
    OUTPUT_DIRECTORY.mkdir()
    for col_num in COLLECTIONS:
        img_page_urls = access_collection(col_num)
        # access each image
        for img_page in img_page_urls:
            # download the jpg image and unzip it
            dl_page_url = access_image(img_page)
            local_zip_loc = download_image_zip(dl_page_url)
            unzip_image(local_zip_loc)
    fix_collection_4()

def crop_and_resize(img_file, keep_fullsize=False):
    """
    Crop each image to the region of interest, then resize.
    Source: https://stackoverflow.com/a/13539194
    """
    img_name = img_file.name
    print(f"    Processing image {img_name}")
    # load image
    img = cv2.imread(str(img_file))

    # calculate image contours
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _,thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # find the largest contour area
    largest_contour = max([(cv2.contourArea(cnt), cnt) for cnt in contours], key=lambda x: x[0])[1]

    # crop to (a square of) that area
    print("      Cropping")
    x,y,w,h = cv2.boundingRect(largest_contour)
    if w != h:
        min_dim = min(w, h)
        w, h = min_dim, min_dim
    cropped = img[y:y+h,x:x+w]

    if keep_fullsize:
        # save full sized cropped image
        fullsize_dir = OUTPUT_DIRECTORY / "fullsize"
        fullsize_dir.mkdir()
        print(f'     Saving {str(full_size_dir / img_name)}')
        cv2.imwrite(str(OUTPUT_DIRECTORY / "fullsize" / img_name), cropped)

    # resize image
    print("      Resizing")
    resized = cv2.resize(cropped, OUTPUT_DIMENSIONS, interpolation=cv2.INTER_AREA)

    # save image
    cv2.imwrite(str(img_file), resized)

def process_all():
    """ Crop all images in the output directory to squares and resize to 512x512. """
    print("Processing images...")
    source = OUTPUT_DIRECTORY
    images = list(source.glob('*.jpg'))
    for img in images:
        crop_and_resize(img)

if __name__=="__main__":
    download_all()
    process_all()