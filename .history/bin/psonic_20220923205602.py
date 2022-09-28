import random
import time

from pythonosc import udp_client

client = udp_client.SimpleUDPClient('127.0.0.1', 4559)

while True:
    client.send_message("/bpm", random.randint(40, 200))
    time.sleep(5)
set_server_parameter('192.168.1.2',4560)

play(70)