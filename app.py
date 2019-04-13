import threading

from server import enter_server_loop, stop_server
from command_line import enter_command_loop


def main():
    """
    Entry point to start the MetaShop server application.
    This function starts the client servicing thread and then
    uses this current thread to allow super users to issue commands.
    """

    # Kickoff servicing server
    server_thread = threading.Thread(target=enter_server_loop)
    server_thread.start()

    enter_command_loop()  # Handle commands until user exit
    #testmain()

    stop_server()  # Start stopping if not already
    server_thread.join()


#import image_util
#import server
#import database
import retailer_lookup
import image_util
import base64
import pprint
import numpy as np

def testmain():
    img_data = image_util.load_image_bytes("images/6.png")
    #print(type(img_data[0]))
    #pprint.pprint(img_data[0])
    encoded = base64.b64encode(img_data[0]).decode()
    img_bytes = np.frombuffer(base64.b64decode(encoded), dtype=np.uint8)
    #pprint.pprint(img_bytes)
    print(image_util.load_cv_image_from_image_bytes((img_bytes, img_data[1])))
    #print(retailer_lookup.lookup_walmart_prices([21618295, 30148619]))
    #database.set_product_prices(3, -1.0, -1.0)
    #database.print_all()
    #print(database.get_product(3)[:-2])
    #print(database.get)

    #print(server.image_processor.match_image(image_util.load_image_bytes("query_images/test_image.jpg")))

"""
import time

import server
import image_util


def testmain():
    time.sleep(1)

    query_image_pathname = "query_images/test_image.jpg"
    query_image_data = image_util.load_image_bytes(query_image_pathname)
    #query_image = image_util.load_cv_image_from_image_bytes(query_image_data)

    print(server.image_processor.match_image(query_image_data))
"""

main()
