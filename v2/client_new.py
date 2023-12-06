import socket
import threading
import time
import pygame
import random
import sys
import json

# Server IP address and Port number
serverAddressPort = ("192.168.142.44", 8000)


# Connect2Server forms the thread - for each connection made to the server
def connect_to_server(game, metrics):
    bufferSize = 1024
    game_ele = None
    ping = [-1]*100
    last_time = 0
    ping_index = 0
    packet_id = 0
    packets_delivered = [True]*1000
    hz = 0
    last_update = time.time()

    # Create a socket instance - A datagram socket
    UDPClientSocket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)

    UDPClientSocket.setblocking(0)

    msg_to_server = f"{game.player_speed},{packet_id}"
    UDPClientSocket.sendto(msg_to_server.encode(), serverAddressPort)

    # Send message to server using created UDP socket
    while True:
        game_ele = game.game_ele
        try:
            # update rate in hz
            hz = hz + 1
            if time.time() - last_update >= 1:
                last_update = time.time()
                metrics["update_rate"] = hz
                hz = 0
            while True:
                data = UDPClientSocket.recvfrom(bufferSize)
                game_ele = json.loads(data[0].decode())
                game.game_ele = game_ele

        except socket.error:
            # compute ping of last 100 packets
            ping[ping_index] = round((time.time() - last_time) * 1000, 3)
            metrics["ping"] = sum(ping)/100
            if ping_index == 99:
                ping_index = 0
            else:
                ping_index += 1

            if packet_id == 1000:
                packet_id = 0

            # set packet as delivered
            if game_ele.get('packet_id') != None:
                packets_delivered[game_ele['packet_id']] = True

            # check packet packet loss
            temp_lost_packets = 0
            for id in packets_delivered:
                if not id:
                    temp_lost_packets += 1
            metrics["packet_loss"] = temp_lost_packets

            packets_delivered[packet_id] = False

            msg_to_server = f"{game.player_speed},{packet_id}"
            UDPClientSocket.sendto(msg_to_server.encode(), serverAddressPort)

            last_time = time.time()
            packet_id += 1
            
        pygame.time.Clock().tick(80)



class GameElements:
    game_ele = {}
    player_speed = 0

    def __init__(self):
        self.game_ele['ball_speed_x'] = 7 + random.choice((1, -1))
        self.game_ele['ball_speed_y'] = 7 + random.choice((1, -1))
        self.game_ele['player_1_speed'] = 0
        self.game_ele['player_2_speed'] = 0
        self.game_ele['ball_x'] = 0
        self.game_ele['ball_y'] = 0
        self.game_ele['player_1_y'] = 0
        self.game_ele['player_2_y'] = 0
        self.game_ele['player_1_score'] = 0
        self.game_ele['player_2_score'] = 0


class Pong:
    # Initialize Pygame
    def __init__(self):
        pygame.init()  # pylint: disable=no-member

        # Set up the game window
        self.screen_width = 700
        self.screen_height = 500
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height))
        pygame.display.set_caption("Pong")

        # Define game colors
        self.bg_color = pygame.Color("grey12")
        self.light_grey = (200, 200, 200)

        # Define game elements
        self.ball = pygame.Rect(
            self.screen_width/2 - 15, self.screen_height/2 - 15, 30, 30)
        self.player = pygame.Rect(
            self.screen_width - 20, self.screen_height/2 - 70, 10, 140)
        self.opponent = pygame.Rect(10, self.screen_height/2 - 70, 10, 140)

        self.game_font = pygame.font.Font("freesansbold.ttf", 32)

        self.last_update = time.time()
        self.update_rate = 0
        self.hz = 0

    def run(self, game, metrics):
        game_ele = game.game_ele
        # Handle events

        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # pylint: disable=no-member
                pygame.quit()  # pylint: disable=no-member
                sys.exit()
            if event.type == pygame.KEYDOWN:  # pylint: disable=no-member
                if event.key == pygame.K_DOWN:  # pylint: disable=no-member
                    game.player_speed = 7
                if event.key == pygame.K_UP:  # pylint: disable=no-member
                    game.player_speed = -7
            if event.type == pygame.KEYUP:  # pylint: disable=no-member
                if event.key == pygame.K_DOWN:  # pylint: disable=no-member
                    game.player_speed = 0
                if event.key == pygame.K_UP:  # pylint: disable=no-member
                    game.player_speed = 0

        # Receive game state from server
        self.ball.centerx = game_ele['ball_x']
        self.ball.centery = game_ele['ball_y']
        self.player.y = game_ele['player_1_y']
        self.opponent.y = game_ele['player_2_y']

        # Draw game elements
        self.screen.fill(self.bg_color)
        pygame.draw.rect(self.screen, self.light_grey, self.player)
        pygame.draw.rect(self.screen, self.light_grey, self.opponent)
        pygame.draw.ellipse(self.screen, self.light_grey, self.ball)
        pygame.draw.aaline(self.screen, self.light_grey, (self.screen_width /
                           2, 0), (self.screen_width/2, self.screen_height))

        # Draw scores
        player_text = self.game_font.render(
            f"{game_ele['player_2_score']}", False, self.light_grey)
        self.screen.blit(player_text, (self.screen_width /
                         2 + 20, self.screen_height/2 - 16))
        opponent_text = self.game_font.render(
            f"{game_ele['player_1_score']}", False, self.light_grey)
        self.screen.blit(opponent_text, (self.screen_width /
                         2 - 42, self.screen_height/2 - 16))

        # Draw Update rate
        update_rate_text = self.game_font.render(
            f"{metrics['update_rate']} hz", False, self.light_grey)
        self.screen.blit(update_rate_text, (30, 50))

        # Draw ping
        ping_text = self.game_font.render(
            f"{round(metrics['ping'], 3)} ms", False, self.light_grey)
        self.screen.blit(ping_text, (30, 20))

        # draw lost packets
        lost_packets_text = self.game_font.render(
            f"{metrics['packet_loss']} pr. 1000 packets", False, self.light_grey)
        self.screen.blit(lost_packets_text, (30, 80))

        # Update the display
        pygame.display.flip()


def loop(game, pong, metrics):
    while True:
        pong.run(game, metrics)
        pygame.time.Clock().tick(100)


if __name__ == "__main__":
    print("Client - Main thread started")

    game_ele = GameElements()
    pong = Pong()
    metrics = {"packet_loss": 0, "ping": 0, "update_rate": 0}

    ThreadInstance = threading.Thread(
        target=connect_to_server, args=(game_ele, metrics,))
    ThreadInstance.daemon = True
    ThreadInstance.start()

    loop(game_ele, pong, metrics)
