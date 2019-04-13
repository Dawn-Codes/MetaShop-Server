import socket
import json
import binascii

import json_protocol
import socket_util
import database
import retailer_lookup
import image_util
import config


#
#import numpy as np
#def load_image_bytes(filepath):
#    ext = filepath[filepath.index('.') + 1:] if '.' in filepath else None
#    with open(filepath, "rb") as infile:
#        img_bytes = np.fromfile(infile, dtype=np.uint8)
#    return img_bytes, ext


INVALID_IMAGE = image_util.load_image_bytes("invalid_image.png")
#


SERVER_TIMEOUT = 60  # 60 seconds


class ClientConnection:
    def __init__(self, server, client_socket, image_processor):
        self.server = server
        self.host = client_socket.getpeername()[0]
        self.port = client_socket.getpeername()[1]
        self.client_socket = client_socket
        self.client_socket.settimeout(SERVER_TIMEOUT)  # 60 seconds before connection is terminated
        self.image_processor = image_processor
        self.stop_running = False

    def enter_main_loop(self):
        try:
            while True:
                self.handle_json_protocol()
        except ConnectionResetError:
            print(self.host + ':' + str(self.port) + " disconnected.")
        except ConnectionAbortedError:
            print(self.host + ':' + str(self.port) + " disconnected.")
        except socket.timeout:
            print(self.host + ':' + str(self.port) + " timed out.")
        except OSError:
            if not self.stop_running:  # If not from us calling .stop()
                raise
            else:  # If us calling .stop()
                print(self.host + ':' + str(self.port) + " forced to shutdown.")

    def stop(self):
        if not self.stop_running:
            if not self.server.remove_client(self):
                return  # In the process of being stopped by main server thread
            self.stop_running = True
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
            except ConnectionResetError:  # In the case the Client has already terminated
                pass  # Silently fail
            self.client_socket.close()
            self.client_socket = None

    def handle_json_protocol(self):  # still debug stuff here
        json_data = self.read_json()
        try:
            (request_type, obj) = json_protocol.parse_json_request(json_data)
            if request_type is json_protocol.RequestType.IDENTIFY:
                products = []
                img_datas = obj
                for img_data in img_datas:
                    possible_matches = self.image_processor.match_image(img_data)
                    print(possible_matches)
                    if possible_matches:
                        best_metashop_id = possible_matches[0][0]
                        db_result = database.get_product(best_metashop_id)[:-2]  # Don't need pricing information
                        image_filename = config.IMAGES_DIR + '/' + image_util.get_full_filename(
                            config.IMAGES_DIR, str(best_metashop_id))
                        image = image_util.load_image_bytes(image_filename)
                        db_result.append(image)
                        temp = db_result[0]
                        db_result[0] = db_result[1]
                        db_result[1] = temp
                        products.append(db_result)
                    else:
                        products.append(['INVALID PRODUCT', '-1', '-1', '-1', INVALID_IMAGE])

                response = json_protocol.build_json_response(json_protocol.ResponseType.IDENTIFY, products)
                self.send_json(response)
            elif request_type is json_protocol.RequestType.PRICE_CHECK:
                metashop_ids = [int(metashop_id) for metashop_id in obj]
                products = database.get_products(metashop_ids)
                walmart_skus = []
                for product in products:
                    walmart_skus.append(product[2])
                walmart_prices = retailer_lookup.lookup_walmart_prices(walmart_skus)
                prices = []
                for walmart_price in walmart_prices:
                    prices.append([walmart_price, -1.0])

                response = json_protocol.build_json_response(json_protocol.ResponseType.PRICE_CHECK, prices)
                self.send_json(response)
        except binascii.Error as ex:
            self.send_json(json_protocol.build_json_response(json_protocol.ResponseType.ERROR, str(ex)))
        except RuntimeError as ex:
            self.send_json(json_protocol.build_json_response(json_protocol.ResponseType.ERROR, str(ex)))

    def read_json(self):
        """
        Throws ConnectionResetError, ConnectionAbortedError, socket.timeout
        """
        length = socket_util.read_u32(self.client_socket)
        raw_bytes = socket_util.readall(self.client_socket, length)
        dictionary = json.loads(raw_bytes, encoding="utf-8")
        return dictionary

    def send_json(self, dictionary):
        """
        Throws ConnectionResetError
        """
        if not isinstance(dictionary, dict):
            raise TypeError("send_json() must be passed a dictionary object!")
        raw_bytes = json.dumps(dictionary, ensure_ascii=False).encode("utf-8")
        length = len(raw_bytes)
        if length > 0xFFFFFFFF:
            raise RuntimeError("Object is too large for send_json()! Can only send a maximum of 4294967295 bytes!")
        socket_util.send_u32(self.client_socket, length)
        self.client_socket.sendall(raw_bytes)
