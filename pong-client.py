from twisted.internet import reactor, protocol
import pygame
import sys
import random
import json
import time


class UDPEchoClient(protocol.DatagramProtocol):
    game_ele = None
    pong = None
    ping = [0]*1000
    last_time = 0
    ping_index = 0

    def startProtocol(self):
        self.transport.connect("127.0.0.1", 8000)
        self.transport.write("0".encode())

    def datagramReceived(self, data, addr):
        self.ping[self.ping_index] = time.time() - self.last_time
        if self.ping_index == 999:
            self.ping_index = 0
        else:
            self.ping_index += 1
        print(f"Received: {data.decode()} from {addr}")
        game_ele = json.loads(data.decode())
        self.game_ele.game_ele = game_ele
        # print(f"Recieved: {self.game_ele.game_ele}")
        self.pong.run(self.game_ele, self)
        self.transport.write((str(self.game_ele.player_speed)).encode())
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
        pygame.init()

        # Set up the game window
        self.screen_width = 800
        self.screen_height = 600
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

    def run(self, game, client):
        game_ele = game.game_ele
        # Handle events

        game.player_speed = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.transport.write("STOP".encode())
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    game.player_speed += 7
                if event.key == pygame.K_UP:
                    game.player_speed -= 7
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    game.player_speed -= 7
                if event.key == pygame.K_UP:
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
        
        # Draw ping
        avrg_ping = round(1000 * sum(client.ping)/len(client.ping), 3)
        ping_text = self.game_font.render(
            f"{avrg_ping} ms", False, self.light_grey)
        self.screen.blit(ping_text, (30, 20))

        # Update the display
        pygame.display.flip()


if __name__ == '__main__':
    game_ele = Game_elements()
    UDPEchoClient.game_ele = game_ele
    pong = Pong()
    UDPEchoClient.pong = pong
    reactor.listenUDP(0, UDPEchoClient())
    reactor.run()
