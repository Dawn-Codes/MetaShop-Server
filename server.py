import atexit
import os

import config
import database
import shared_data
from image_matcher import ImageMatcher
from image_processor import ImageProcessor
from main_server import Server


main_server = None
stop_running = False

image_processor = ImageProcessor()


@atexit.register  # Register hook to safely shutdown application on OS shutdown
def stop_server():
    global main_server
    main_server.stop()


def enter_server_loop():
    """
    The main part of the MetaShop Server application that
    consists of maintaining the running state of the server,
    updating the FLANN image index when needed, and spawning
    client servicing threads.
    """
    global main_server, image_processor

    config.create_directories()
    database.open_connection(config.DATABASE_PATHNAME)

    # To insure the existing index isn't being saved
    shared_data.lock.acquire()  # Enter Critical Section
    if os.path.isfile(os.getcwd() + "/matcher.bin"):
        image_matcher = ImageMatcher()
        image_matcher.load(os.getcwd())
        image_processor.update_image_matcher(image_matcher)
    shared_data.lock.release()  # Exit Critical Section

    main_server = Server("localhost", 32304, image_processor)
    main_server.enter_main_loop()

    database.close_connection()


def update_index():
    global image_processor

    # If the lock couldn't be acquired
    if not shared_data.lock.acquire(blocking=False):  # Enter Critical Section
        return

    image_processor.update_image_matcher(shared_data.matcher_index)
    shared_data.matcher_index = None

    shared_data.index_needs_updating = False
    shared_data.lock.release()  # Exit Critical Section
