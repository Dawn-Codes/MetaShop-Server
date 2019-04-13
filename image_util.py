import requests
import numpy as np
import cv2
import os


def download_image_bytes(image_url):
    r = requests.get(image_url, stream=True)
    if r.status_code != 200:
        raise RuntimeError("Response wasn't \"200 OK\"!")
    if "Content-Type" not in r.headers:
        raise RuntimeError("Response didn't provide a \"Content-Type\"!")
    ext = r.headers["Content-Type"][6:]  # "image/EXTENSION"
    r.raw.decode_content = True  # in case the image is GZIPped
    img_bytes = np.asarray(bytearray(r.raw.read()), dtype=np.uint8)
    return img_bytes, ext


def save_image_bytes(filepath, image_data):
    with open(filepath + '.' + image_data[1], "wb") as outfile:
        image_data[0].tofile(outfile)


def load_image_bytes(filepath):
    ext = filepath[filepath.index('.') + 1:] if '.' in filepath else None
    with open(filepath, "rb") as infile:
        img_bytes = np.fromfile(infile, dtype=np.uint8)
    return img_bytes, ext


def load_cv_image_from_image_bytes(image_data):
    return cv2.imdecode(image_data[0], cv2.IMREAD_GRAYSCALE)


def get_full_filename(directory, basename):
    for fn in os.listdir(directory):
        if fn.startswith(basename + '.'):
            return fn
    return None
