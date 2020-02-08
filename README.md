# EAAGAN

## About

The plan for this project is to experiment with generating art using the USGS ["Earth As Art"](https://eros.usgs.gov/image-gallery/earth-art) collections as seed data.

There will likely be some GAN experimentation, but we'll see!

## Usage

Right now, there is only a script to download some EAA content. It does not download the entire series, but about 10-15 images from each collection. To download the images yourself using this script, run `python earth_as_art_download.py`.

If you are missing any modules, `pip install -r requirements.txt`.

## TODO

- Parameterize download script
- Download entire collections
- Crop images to squares
- Use StyleGAN
  - Investigate GPU compute options
  - Budget it all out
- Make a website for displaying results
  - Squarespace?
  - Personal site?
  - Etc
