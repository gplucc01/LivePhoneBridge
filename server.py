from __future__ import absolute_import, print_function, unicode_literals

import socket
import threading
import json
import time
from queue import Queue

class BridgeServer:
    def __init__(self, host="0.0.0.0", port=8765, command_queue=None, response_queue=None):
        self.host = host
        self.port = port
        self.command_queue = command_queue
        self.response_queue = response_queue
        self.running = True
        self.client_socket = None
        self.lock = threading.Lock()

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)

        while self.running:
            try:
                client_socket, addr = server_socket.accept()
                with self.lock:
                    if self.client_socket:
                        self.client_socket.close()
                    self.client_socket = client_socket
                listener = threading.Thread(target=self._listen_to_client, args=(client_socket,), daemon=True)
                listener.start()
                sender = threading.Thread(target=self._send_responses, args=(client_socket,), daemon=True)
                sender.start()
            except:
                if not self.running:
                    break

    def _listen_to_client(self, client_socket):
        buffer = b""
        while self.running:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line.strip():
                        try:
                            message = json.loads(line.decode("utf-8"))
                            self.command_queue.put(message)
                        except:
                            pass
            except:
                break
        self._cleanup(client_socket)

    def _send_responses(self, client_socket):
        while self.running:
            if not self.response_queue.empty():
                try:
                    response = self.response_queue.get_nowait()
                    msg = (json.dumps(response) + "\n").encode("utf-8")
                    with self.lock:
                        if self.client_socket == client_socket:
                            client_socket.sendall(msg)
                except:
                    pass
            else:
                time.sleep(0.01)

    def _cleanup(self, client_socket):
        with self.lock:
            if self.client_socket == client_socket:
                self.client_socket = None
        try:
            client_socket.close()
        except:
            pass

    def shutdown(self):
        self.running = False
        with self.lock:
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass