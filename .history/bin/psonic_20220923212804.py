from pythonosc import osc_message_builder
from pythonosc import udp_client

sender = udp_client.SimpleUDPClient('192.168.1.2', 4560)
sender.send_message('/trigger/prophet', [70, 100, 8])
