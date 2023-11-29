import random
import json
import threading

import pygame
from twisted.internet import reactor, protocol


class GameLogic:
    screen_width = 700
    screen_height = 500
    game_ele = {}
    game_ele['ball_speed_x'] = 0
    game_ele['ball_speed_y'] = 0
    game_ele['player_1_speed'] = 0
    game_ele['player_2_speed'] = 0
    game_ele['ball_x'] = screen_width/2
    game_ele['ball_y'] = screen_height/2
    game_ele['player_1_y'] = 0
    game_ele['player_2_y'] = 0
    game_ele['player_1_score'] = 0
    game_ele['player_2_score'] = 0

    def reset_game(self):
        self.game_ele['ball_speed_x'] = 0
        self.game_ele['ball_speed_y'] = 0
        self.game_ele['player_1_speed'] = 0
        self.game_ele['player_2_speed'] = 0
        self.game_ele['ball_x'] = self.screen_width/2
        self.game_ele['ball_y'] = self.screen_height/2
        self.game_ele['player_1_y'] = 0
        self.game_ele['player_2_y'] = 0
        self.game_ele['player_1_score'] = 0
        self.game_ele['player_2_score'] = 0

    def reset_ball(self):
        self.game_ele['ball_x'] = self.screen_width/2
        self.game_ele['ball_y'] = self.screen_height/2
        self.game_ele['ball_speed_y'] = 0
        self.game_ele['ball_speed_x'] = 0

    def start_ball(self):
        self.game_ele['ball_speed_y'] = 5 + random.choice((1, -1))
        self.game_ele['ball_speed_x'] = 5 + random.choice((1, -1))


class UDPEchoServer(protocol.DatagramProtocol):
    # index 0 is player 1, index 1 is player 2
    clients = []
    game = GameLogic()

    def datagramReceived(self, data, addr):
        if data.decode() == "STOP":
            self.clients.remove(addr)
            self.game.reset_game()
            return
        if addr not in self.clients:
            self.clients.append(addr)
        # print(f"Received: {data.decode()} from {addr}")
        if addr == self.clients[0]:
            self.game.game_ele['player_1_speed'] += int(data.decode())
        if len(self.clients) > 1 and addr == self.clients[1]:
            self.game.game_ele['player_2_speed'] += int(data.decode())

        # Send game state back to client
        game_state = json.dumps(self.game.game_ele)
        # print(f"Sending: {game_state} to {addr}")
        self.transport.write(game_state.encode(), addr)


def loop(game):
    while True:
        # Update game state
        if game.game_ele['ball_speed_x'] == 0 and game.game_ele["player_1_speed"] != 0:
            game.start_ball()
        game.game_ele['ball_x'] = game.game_ele['ball_x'] + \
            game.game_ele['ball_speed_x']
        game.game_ele['ball_y'] = game.game_ele['ball_y'] + \
            game.game_ele['ball_speed_y']

        if game.game_ele['ball_y'] + 15 <= 0 or game.game_ele['ball_y'] + 15 >= game.screen_height:
            game.game_ele['ball_speed_y'] *= -1
        if game.game_ele['ball_x'] <= 0:
            print("Player 2 scored!")
            game.game_ele['player_2_score'] += 1
            game.reset_ball()
        if game.game_ele['ball_x'] >= game.screen_width:
            print(f"ball x: {game.game_ele['ball_x']}")
            print("Player 1 scored!")
            game.game_ele['player_1_score'] += 1
            game.reset_ball()
        if game.game_ele['ball_x'] >= game.screen_width - 38 and game.game_ele['ball_y'] >= game.game_ele['player_1_y'] and game.game_ele['ball_y'] <= game.game_ele['player_1_y'] + 140 and game.game_ele['ball_speed_x'] > 0:
            game.game_ele['ball_speed_x'] *= -1
        if game.game_ele['ball_x'] <= 38 and game.game_ele['ball_y'] >= game.game_ele['player_2_y'] and game.game_ele['ball_y'] <= game.game_ele['player_2_y'] + 140 and game.game_ele['ball_speed_x'] < 0:
            game.game_ele['ball_speed_x'] *= -1

        # Move paddles
        game.game_ele['player_1_y'] += game.game_ele['player_1_speed']
        game.game_ele['player_2_y'] += game.game_ele['player_2_speed']

        pygame.time.Clock().tick(60)


if __name__ == '__main__':
    pygame.init()

    # Create a shared GameLogic object
    game = GameLogic()

    # Create a new thread that runs the loop function
    t = threading.Thread(target=loop, args=(game,))
    t.daemon = True  # Allows system to exit even if thread is still running
    t.start()

    # Start the UDP server
    UDPEchoServer.game = game
    reactor.listenUDP(8000, UDPEchoServer())
    reactor.run()
