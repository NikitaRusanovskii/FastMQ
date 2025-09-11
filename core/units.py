from abc import ABC

import websockets


class Unit(ABC):
    pass


class Producer(Unit):
    def __init__(self, websocket: websockets.ClientConnection):
        self.websocket = websocket
        self.id = 0


class Consumer(Unit):
    def __init__(self, websocket: websockets.ClientConnection):
        self.websocket = websocket
        self.id = 0
