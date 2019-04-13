import socket
import threading

from client_connection import ClientConnection


class Server:
    def __init__(self, host, port, image_processor):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        self.stop_running = False
        self.clients_list = []
        self.clients_list_lock = threading.RLock()
        self.image_processor = image_processor
        print("Starting Server on " +
              self.server_socket.getsockname()[0] + ':' + str(self.server_socket.getsockname()[1]))

    def enter_main_loop(self):
        try:
            while True:
                (client_socket, address) = self.server_socket.accept()
                print(address[0] + ':' + str(address[1]) + " connected.")
                client_connection = ClientConnection(self, client_socket, self.image_processor)
                self.clients_list.append(client_connection)
                threading.Thread(target=client_connection.enter_main_loop).start()
        except OSError:
            if not self.stop_running:  # If not from us calling .stop()
                raise

    def stop(self):
        if not self.stop_running:
            self.stop_running = True
            print("Stopping Server...")
            self.server_socket.close()
            self.server_socket = None
            self.clients_list_lock.acquire()
            for client in self.clients_list:
                client.stop()
            self.clients_list = []
            self.clients_list_lock.release()

    def remove_client(self, client_connection):
        if not self.clients_list_lock.acquire(blocking=False):
            return False  # If the server is shutting down the client will be removed anyway
        self.clients_list.remove(client_connection)
        self.clients_list_lock.release()
        return True
