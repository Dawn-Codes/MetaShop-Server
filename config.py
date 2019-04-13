import os


#WORKING_DATA_DIR = "working_data"

IMAGES_DIR = "images"
DATABASE_PATHNAME = "products.db"

#NEW_DATA_DIR = "new_data"


def create_directories():
    os.makedirs(IMAGES_DIR, exist_ok=True)


"""
def create_directories():
    os.makedirs(WORKING_IMAGES_DIR, exist_ok=True)
    os.makedirs(NEW_DATA_DIR, exist_ok=True)
"""