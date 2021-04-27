
import websocket
import gevent
import ssl
from pprint import pprint

from .messages import Hello, json_serialize, json_deserialize, now, sequence


class WebsocketChannel(object):

    def __init__(self, address):
        self.sequence = sequence()
        self.address = address
        self.thread = None
        self.reconnect_callback = None
        self.start_socket_thread()
        self.startup_messages = []
        self.opened = False
        self.outbox = None
        self.put_message(Hello(0, now()))

    def start_socket_thread(self):
        print('start_socket_thread')
        self.socket = websocket.WebSocketApp(self.address,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close,
                                             on_open=self.on_open)
        self.thread = gevent.spawn(self.socket.run_forever, sslopt={
                                   "cert_reqs": ssl.CERT_NONE})

    def put_message(self, message):
        message = message._replace(seq_num=next(self.sequence))
        self.put(json_serialize(message))

    def put(self, message):
        pprint(message)
        if not self.opened:
            self.startup_messages.append(message)
        else:
            self.socket.send(message)

    def on_open(self, ws=None):
        print('on_open')
        self.opened = True
        for message in self.startup_messages:
            self.put(message)
        self.startup_messages = []

    def on_message(self, message):
        print('on_message')
        if self.outbox:
            msg = json_deserialize(message)
            if not msg:
                print("Unknown message:", message)
            self.outbox.put(msg)

    def on_close(self, ws=None):
        print('on_close')
        self.opened = False
        old_thread = self.thread
        self.start_socket_thread()
        self.put_message(Hello(0, now()))
        if self.reconnect_callback:
            self.reconnect_callback(self)
        old_thread.kill()

    def on_error(self, ws=None, error=None):
        print('WebsocketChannel on_error', error)
        self.on_close(ws)
        gevent.sleep(1)


class NullChannel(object):

    thread = None
    outbox = None

    def put(self, message):
        pass

    def put_message(self, message):
        pass
