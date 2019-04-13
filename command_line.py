import os
import requests
import cv2

import database
import shared_data
import google_search
import image_util
import config
from image_matcher import ImageMatcher


def enter_command_loop():
    """
    Allows a super user to enter the "build" command
    which will build an index for all the named images
    in the file given to it.
    Also allows the user to enter "exit" which will
    shutdown the MetaShop server application.
    """
    print("MetaShop Server Started.\nEnter \"help\" for instructions.\n")
    while True:
        raw_command = input("> ").strip()
        lower_command = raw_command.lower()
        if not lower_command or lower_command == "help":
            print("build \"products_file.txt\" - Rebuilds image index after adding any new products found in "
                  "the file provided.\n"
                  "exit                      - Terminates the MetaShop Server process.")
        elif lower_command == "exit":
            break
        elif lower_command == "build":
            print("Usage: build \"products_file.txt\"")
        elif lower_command.startswith("build ") and len(lower_command) > 6:
            filepath = raw_command[6:]
            if os.path.isfile(filepath):
                build_index(filepath)
            else:
                print('"' + filepath + "\" is not a valid file!")
        else:  # Unknown command
            print("Unrecognized command: \"" + raw_command + "\". Please enter \"help\" for suggestions.")


def build_index(filepath):
    product_names = []
    try:
        with open(filepath, 'r') as infile:
            for row in infile:
                product_names.append(row.strip())
    except IOError as ex:
        print(ex)
        return

    added_ids_count = 0
    existing_ids = database.get_product_ids(product_names)
    for i in range(len(product_names)):
        if existing_ids[i] is None:
            product_name = product_names[i]
            # Fetch product information firstly
            product_infos = None
            try:
                product_infos = google_search.search_retailers(product_name)
            except requests.exceptions.HTTPError as ex:
                print(ex)
            except requests.exceptions.ConnectionError as ex:
                print(ex)
            except requests.exceptions.Timeout as ex:
                print(ex)
            except requests.exceptions.RequestException as ex:
                print(ex)

            if product_infos is None:
                print("Skipped \"" + product_name + "\" as search connection could not be created!")
                continue

            # Insure we have entries for all retailers
            missing_retailers = []
            for (retailer, product_info) in product_infos.items():
                if product_info is None:
                    missing_retailers.append(retailer)
            if missing_retailers:
                print("Skipped \"" + product_name + "\" as product information could not be obtained from: [" +
                      ", ".join(missing_retailers) + "]!")
                continue

            # Insure a product image can be downloaded
            walmart_img_url = product_infos["walmart"][2]
            image_data = None
            try:
                image_data = image_util.download_image_bytes(walmart_img_url)
            except requests.exceptions.HTTPError as ex:
                print(ex)
            except requests.exceptions.ConnectionError as ex:
                print(ex)
            except requests.exceptions.Timeout as ex:
                print(ex)
            except requests.exceptions.RequestException as ex:
                print(ex)
            except RuntimeError as ex:
                print(ex)

            if image_data is None:
                print("Skipped \"" + product_name + "\" as product image could not be retrieved!")
                continue

            # Add entry to database
            walmart_sku = product_infos["walmart"][1]
            amazon_asin = product_infos["amazon"][1]
            dbid = database.insert_product(product_name, walmart_sku, amazon_asin)

            # Save image as identifier
            image_util.save_image_bytes(config.IMAGES_DIR + '/' + str(dbid), image_data)

            added_ids_count += 1
            print("Successfully added \"" + product_name + "\" to the database.")
        else:
            print("Skipped \"" + product_names[i] + "\" as it is already in the database.")

    if added_ids_count == 0:
        print("Nothing to build. Database is current!")
        return

    image_dbids = []
    train_images = []
    for fn in [fn for fn in os.listdir(config.IMAGES_DIR) if os.path.isfile(config.IMAGES_DIR + '/' + fn)]:
        try:
            if '.' not in fn:  # not a image file
                continue
            try:
                name_dbid = int(fn[0:fn.index('.')])
            except ValueError:
                continue

            img_data = image_util.load_image_bytes(config.IMAGES_DIR + '/' + fn)
            cv_image = image_util.load_cv_image_from_image_bytes(img_data)
            if cv_image is None:
                print("Could not decode image: \"" + fn + "\"!")
                continue
            image_dbids.append(name_dbid)
            train_images.append(cv_image)
        except cv2.error as ex:
            print(ex)
            print("Could not decode image: \"" + fn + "\"!")

    # Build FLANN Index
    new_matcher_index = ImageMatcher()
    new_matcher_index.build(image_dbids, train_images)

    shared_data.lock.acquire()  # Enter Critical Section
    shared_data.rebuild_in_progress = True

    # Set shared variable and save to disk
    shared_data.matcher_index = new_matcher_index
    new_matcher_index.save(os.getcwd())

    shared_data.index_needs_updating = True
    shared_data.rebuild_in_progress = False
    shared_data.lock.release()  # Exit Critical Section

    print("FLANN Index updated.")
