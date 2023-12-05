import socketserver
import threading
import random
import json

import pygame

# Create a tuple with IP Address and Port Number
ServerAddress = ("192.168.142.44", 8000)

# Subclass the DatagramRequestHandler
class MyUDPRequestHandler(socketserver.DatagramRequestHandler):
    """ Handles datagram requests from clients """
    clients = []
    game = None

    def handle(self):
        data = self.rfile.readline().strip()

        if data.decode() == "STOP":
            self.clients.remove(self.client_address)
            self.game.reset_game()
            return
        if self.client_address not in self.clients:
            self.clients.append(self.client_address)

        data = (data.decode()).split(",")
        print(f"Received: {data} from {self.client_address}")
        if self.client_address == self.clients[0]:
            self.game.game_ele['player_1_speed'] = int(data[0])
        if len(self.clients) > 1 and self.client_address == self.clients[1]:
            self.game.game_ele['player_2_speed'] = int(data[0])
        self.game.game_ele['packet_id'] = int(data[1])

        # Send game state back to client
        game_state = json.dumps(self.game.game_ele)
        self.wfile.write(game_state.encode())


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
    game_ele['packet_id'] = 0

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
        self.game_ele['ball_speed_y'] = 4 + random.choice((1, -1))
        self.game_ele['ball_speed_x'] = 4 + random.choice((1, -1))


def loop(game):
    """ Main game loop """

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

        pygame.time.Clock().tick(100)


if __name__ == "__main__":
    # Create a GameLogic Instance
    game = GameLogic()

    # Create a Server Instance and share the GameLogic instance
    t = threading.Thread(target=loop, args=(game,))
    t.daemon = True
    t.start()

    # Create a UDP Server Instance and share the GameLogic instance
    MyUDPRequestHandler.game = game
    UDPServerObject = socketserver.ThreadingUDPServer(
        ServerAddress, MyUDPRequestHandler)

    # Make the server wait forever serving connections
    UDPServerObject.serve_forever()
