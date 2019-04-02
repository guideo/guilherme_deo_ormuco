import socket
import importlib
import argparse
import sys
import pickle
from threading import Thread

cache_module = importlib.import_module('LRU_cache')
Cache = getattr(cache_module, 'Cache')


def parse_input(args):
    parser = argparse.ArgumentParser(description='Receives an address and port and start a Cache Node')
    parser.add_argument('address', type=str, help='String for the address')
    parser.add_argument('port', type=int, help='Integer for the port')

    parsed = parser.parse_args(args)
    return parsed


class CacheNode:

    def __init__(self, size, address, port):
        self.cache_size = size
        self.port = port
        self.address = address
        self.lru_cache = Cache(self.cache_size)

    def listen_for_calls(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.address, self.port))

        server_socket.listen(5)
        while True:
            print("Running...")
            client_socket, address = server_socket.accept()
            data = client_socket.recv(1024)
            data = pickle.loads(data)
            if data['key'] == "print":
                print(self.lru_cache.cache_dll)
            else:
                print("Data: {}".format(data['key']))
                return_data = self.lru_cache.check_cache(data['key'])
                print('return data: {}'.format(return_data))
                client_socket.sendall(pickle.dumps({'data': return_data}))
            client_socket.close()

    def listen_for_updates(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.address, self.port + 1))

        server_socket.listen(5)
        while True:
            print("Waiting for updates...")
            client_socket, address = server_socket.accept()
            data = client_socket.recv(1024)
            data = pickle.loads(data)
            print("Data: {}".format(data))
            self.lru_cache.check_cache(data['key'], data['data'])
            client_socket.close()

    def init_cache(self):
        try:
            db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            db_socket.connect(('localhost', 8741))
            db_socket.sendall(pickle.dumps({'id': self.lru_cache.cache_id,
                                            'request_type': 'NewCacheStarting',
                                            'address': self.address,
                                            'port': self.port}))
            data = db_socket.recv(1024 * self.cache_size)
            db_socket.close()
        except ConnectionRefusedError as e:
            print("CONNECTION REFUSED - Server is busy. \nERROR: {}".format(e))
        if data is not None:
            data = pickle.loads(data)
        self.lru_cache.build(data['data'])
        print(data)


if __name__ == "__main__":
    info = parse_input(sys.argv[1:])
    cache_node = CacheNode(3, info.address, info.port)

    cache_node.init_cache()

    thread = Thread(target=cache_node.listen_for_updates)
    thread.start()

    cache_node.listen_for_calls()
