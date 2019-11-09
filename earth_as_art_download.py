import os
import requests
import bs4
import zipfile
import shutil

from pathlib import Path


USGS_BASE_URL = 'https://eros.usgs.gov'
EAA_BASE_URL = USGS_BASE_URL + '/image-gallery/earth-art'
COLLECTIONS = [1, 2, 3, 4, 5, 6]
OUTPUT_DIRECTORY = Path("./EarthAsArt")

def collection_url(collection_number):
    return EAA_BASE_URL + '-' + str(collection_number)

def image_url(collection_url, image_title):
    return collection_url + '/' + image_title

def download_page(url):
    res = requests.get(url)
    res.raise_for_status()
    resSoup = bs4.BeautifulSoup(res.text, features="html.parser")
    return resSoup

def access_collection(col_num):
    # TODO: I think the results are paginated, so... scroll down? request them all? idk
    # ALTERNATIVE:
    # Navigate to the first image in the collection,
    # then get the download link and hit "next" all the way through the collection
    print(f"Accessing collection {col_num}...")

    url = collection_url(col_num)
    collectionSoup = download_page(url)
    img_elements = collectionSoup.select('.view-content a')
    img_urls = [USGS_BASE_URL + e.get('href') for e in img_elements]
    return img_urls

def access_image(url):
    imgSoup = download_page(url)
    button = imgSoup.select_one('.btn-hallow')
    url = button.get('href')
    return url

def download_image_zip(url):
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
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        img_name = zip_path.stem
        print(f"        Unzipping {img_name}")
        zip_ref.extractall(OUTPUT_DIRECTORY)
        print(f"        Cleaning {img_name}")
    os.remove(zip_path)

def fix_collection_4():
    # EAA4 is a little wonky. Lets handle that.
    print("Fixing collection 4 location...")
    source = OUTPUT_DIRECTORY / "EAA4_Final_JPGS"
    files = list(source.glob('*'))
    for f in files:
        f.rename(OUTPUT_DIRECTORY / f.name)
    
    source.rmdir()

def download_all():
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

if __name__=="__main__":
    download_all()