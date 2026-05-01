from __future__ import absolute_import, print_function, unicode_literals
import Live
from _Framework.ControlSurface import ControlSurface
from queue import Queue
import threading
import socket

from .server import BridgeServer
from .api import LiveAPIHandler

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        return s.getsockname()[0]
    except:
        return '127.0.0.1'
    finally:
        s.close()

class LivePhoneBridge(ControlSurface):
    def __init__(self, c_instance):
        super(LivePhoneBridge, self).__init__(c_instance)
        self.log_message("=== LivePhoneBridge DEBUG VERSION STARTED ===")

        self.command_queue = Queue()
        self.response_queue = Queue()

        self.api_handler = LiveAPIHandler(self)

        self.server = BridgeServer(
            host="0.0.0.0",
            port=8765,
            command_queue=self.command_queue,
            response_queue=self.response_queue
        )
        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()

        ip = get_local_ip()
        message = f"LivePhoneBridge READY! Connect iOS app to {ip}:8765"
        self.log_message(message)
        self.show_message(message)

    def disconnect(self):
        self.log_message("LivePhoneBridge: Shutting down")
        self.server.shutdown()
        super(LivePhoneBridge, self).disconnect()

    def update_display(self):
        super(LivePhoneBridge, self).update_display()
        self._process_commands()

    def _process_commands(self):
        while not self.command_queue.empty():
            cmd = self.command_queue.get_nowait()
            self.log_message(f"RECEIVED COMMAND → {cmd.get('method')} | params: {cmd.get('params')}")
            try:
                result = self.api_handler.handle(cmd.get("method"), cmd.get("params", {}))
                response = {"jsonrpc": "2.0", "id": cmd.get("id"), "result": result}
                self.log_message(f"SUCCESS → {cmd.get('method')} returned: {result}")
            except Exception as e:
                response = {"jsonrpc": "2.0", "id": cmd.get("id"), "error": {"message": str(e)}}
                self.log_message(f"ERROR in {cmd.get('method')}: {e}")
            self.response_queue.put(response)
            self.log_message("Response queued for iOS app")

# THIS LINE MUST BE AT THE VERY END
def create_instance(c_instance):
    return LivePhoneBridge(c_instance)
