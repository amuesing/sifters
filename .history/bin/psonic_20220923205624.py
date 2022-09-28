import random
import time

from pythonosc import udp_client

client = udp_client.SimpleUDPClient('192.168.1.2', 4560)

while True:
    client.send_message("/bpm", random.randint(40, 200))
    time.sleep(5)
