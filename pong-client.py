import sys
import random
import json
import time

import pygame
from twisted.internet import reactor, protocol

class UDPEchoClient(protocol.DatagramProtocol):
    game_ele = None
    pong = None
    ping = [-1]*1000
    last_time = 0
    ping_index = 0
    packet_id = 0
    packets_delivered = [True]*1000


    def startProtocol(self):
        self.transport.connect("127.0.0.1", 8000)
        self.transport.write("0,0".encode())

    def datagramReceived(self, data, addr):
        # compute ping of last 1000 packets
        self.ping[self.ping_index] = time.time() - self.last_time
        if self.ping_index == 999:
            self.ping_index = 0
        else:
            self.ping_index += 1


        game_ele = json.loads(data.decode())
        self.game_ele.game_ele = game_ele

        # set packet as delivered
        self.packets_delivered[game_ele['packet_id']] = True

        # check packet packet loss
        temp_lost_packets = 0
        for id in self.packets_delivered:
            if not id:
                temp_lost_packets += 1
        self.packet_loss = temp_lost_packets
            

        # update game
        self.pong.run(self.game_ele, self)

        # if no delay here then the player not running the server will have problems connecting to the server,
        # because the server will be sending data too fast to player 1(server)
        time.sleep(0.005) # theoretically limits the server update rate to 200hz

        # update packet id
        if self.packet_id < 999:
            self.packet_id += 1
        else:
            self.packet_id = 0
        self.packets_delivered[self.packet_id] = False

        # send player speed and packet id to server
        packet = f"{str(self.game_ele.player_speed)},{self.packet_id}"
        print(f"packet: {packet}")
        self.transport.write(packet.encode())
        self.last_time = time.time()


class Game_elements:
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
        pygame.init() # pylint: disable=no-member

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

    def run(self, game, client):
        game_ele = game.game_ele
        # Handle events

        game.player_speed = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # pylint: disable=no-member
                client.transport.write("STOP".encode())
                pygame.quit() # pylint: disable=no-member
                sys.exit()
            if event.type == pygame.KEYDOWN: # pylint: disable=no-member
                if event.key == pygame.K_DOWN: # pylint: disable=no-member
                    game.player_speed += 7
                if event.key == pygame.K_UP: # pylint: disable=no-member
                    game.player_speed -= 7
            if event.type == pygame.KEYUP: # pylint: disable=no-member
                if event.key == pygame.K_DOWN: # pylint: disable=no-member
                    game.player_speed -= 7
                if event.key == pygame.K_UP: # pylint: disable=no-member
                    game.player_speed += 7

        # Receive game state from server
        self.ball.centerx = game_ele['ball_x']
        self.ball.centery = game_ele['ball_y']
        self.player.y = game_ele['player_1_y']
        self.opponent.y =  game_ele['player_2_y']

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
        
        # update rate in hz
        self.hz = self.hz + 1
        if time.time() - self.last_update >= 1:
            print(f"update rate: {self.hz}")
            self.last_update = time.time()
            self.update_rate = self.hz
            self.hz = 0

        update_rate_text = self.game_font.render(
            f"{self.update_rate} hz", False, self.light_grey)
        self.screen.blit(update_rate_text, (30, 50))
        
        # Draw ping
        avrg_ping = round(1000 * sum(client.ping)/len(client.ping), 3)
        ping_text = self.game_font.render(
            f"{avrg_ping} ms", False, self.light_grey)
        self.screen.blit(ping_text, (30, 20))

        # draw lost packets
        lost_packets_text = self.game_font.render(f"{client.packet_loss} PL/s", False, self.light_grey)
        self.screen.blit(lost_packets_text, (30, 80))

        # Update the display
        pygame.display.flip()


if __name__ == '__main__':
    game_ele = Game_elements()
    UDPEchoClient.game_ele = game_ele
    pong = Pong()
    UDPEchoClient.pong = pong
    reactor.listenUDP(0, UDPEchoClient())
    reactor.run()
