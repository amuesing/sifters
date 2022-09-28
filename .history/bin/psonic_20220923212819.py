from psonic import *
set_server_parameter('127.0.0.1',4557,4560)
sender = udp_client.SimpleUDPClient('192.168.1.2', 4560)
sender.send_message('/trigger/prophet', [70, 100, 8])
