from pythonosc import osc_message_builder
from pythonosc import udp_client

sender = udp_client.SimpleUDPClient('127.0.0.1', 4560)
sender.send_message('/trigger/prophet', [70, 100, 8])

client = udp_client.SimpleUDPClient('192.168.1.2', 4560)

while True:
    client.send_message("/bpm", random.randint(40, 200))
    time.sleep(5)
