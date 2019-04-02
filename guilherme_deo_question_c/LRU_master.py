import socket
import importlib
import sqlite3
import re
import pickle

cache_module = importlib.import_module('LRU_cache')
Cache = getattr(cache_module, 'Cache')


class CacheMaster:

    def __init__(self, size, db_conn):
        self.cache_list = {}
        self.cache_size = size
        self.lru_cache = Cache(self.cache_size, master=True, db_connection=db_conn)

    def listen_for_calls(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('localhost', 8741))

        server_socket.listen(5)
        while True:
            print("Running Master...")

            client_socket, address = server_socket.accept()
            data = client_socket.recv(1024)
            data = pickle.loads(data)
            node_id = data['id']
            return_data = ''
            print("Received request: {}".format(data))

            if 'request_type' in data and data['request_type'] == 'NewCacheStarting':
                new_address = data['address']
                new_port = data['port']
                self.register_node(node_id, new_address, new_port)
                init_data = str(self.lru_cache)
                client_socket.sendall(pickle.dumps({'data': init_data}))
            elif 'request_type' in data and data['request_type'] == 'HitUpdate':
                return_data = self.lru_cache.check_cache(data['key'])
            else:
                return_data = self.lru_cache.check_cache(data['key'])
                client_socket.sendall(pickle.dumps({'data': return_data}))
            if return_data != "Object not found!" and ('request_type' not in data or data['request_type'] != 'NewCacheStarting'):
                self.update_distributed_caches(data['key'], return_data, node_id)

            client_socket.close()

    def update_distributed_caches(self, key, data, origin):
        print("updating distributed caches")
        update = {'key': key, 'data': data}
        for cache_id, cache_info in self.cache_list.items():
            if cache_id != origin:
                print('update cache {}'.format(cache_id))
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((cache_info['address'], cache_info['port'] + 1))
                sock.sendall(pickle.dumps(update))
                sock.close()

    def register_node(self, node_id, address, port):
        self.cache_list[node_id] = {'address': address, 'port': port}


if __name__ == "__main__":
    conn = sqlite3.connect('ormuco_db.sqlite')

    cache_master = CacheMaster(3, conn)

    cache_master.listen_for_calls()
