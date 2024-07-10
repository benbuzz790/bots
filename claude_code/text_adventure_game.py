import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bots import AnthropicBot, Engines
import conversation_node as CN

class TextAdventureGame:
    def __init__(self):
        self.game_bot = AnthropicBot(
            model_engine=Engines.CLAUDE3OPUS,
            max_tokens=2000,  
            temperature=0.7,
            name="GameMaster",
            role="assistant",
            role_description="an AI game master that runs a text adventure game in a fantasy setting"
        )
        self.system_message = "You are a text adventure game set in an original fantasy world. The player will interact with you, and you will describe what happens based on their actions. Start by giving a brief introduction to set the scene."
        self.game_state = CN.ConversationNode(role="user", content="")

    def play(self):
        print("Welcome to the Text Adventure Game!")
        self.game_state.content = self.system_message
        
        while True:
            print("Generating response...")
            response, self.game_state = self.game_bot.cvsn_respond(cvsn=self.game_state) 
            print(f"{self.game_bot.name}: {response}")

            user_input = input("Player: ")
            if user_input.lower() in ["quit", "exit"]:
                print("Thanks for playing. Goodbye!")
                break

            print("Adding player input to game state...")
            self.game_state = self.game_state.add_reply(user_input, "user")

if __name__ == "__main__":
    game = TextAdventureGame()
    game.play()
