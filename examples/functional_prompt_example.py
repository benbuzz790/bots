import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.anthropic_bots as ab
import src.functional_prompts as fp

def main():
    n_steps = 4
    p1 = f"Hi Claude! Let's make a connect four game. Start by making\
        a list of steps to complete the game. The list should be {n_steps}\
        steps long."
    p2 = f"Hi Claude! Today we're working on connect_four.py. It's already\
        in a usable state, allowing two players to play on a single device\
        inside a terminal. I'd like to upgrade to a GUI while keeping the \
        current code intact. Please write a list of {n_steps} instructions \
        to complete this task, but don't start working just yet."
    
    bot = ab.AnthropicBot(name="logic")
    bot2 = ab.AnthropicBot(name="gui")
    bot.add_tools(r'src/bot_tools.py')
    bot2.add_tools(r'src/bot_tools.py')

    fp.sequential_process(bot, p1, n_steps)
    fp.sequential_process(bot2, p2, n_steps)

    bot.save()
    bot2.save()


import sys
import traceback
def debug_on_error(type, value, tb):
    traceback.print_exception(type, value, tb)
    print("\n--- Entering post-mortem debugging ---")
    import pdb
    pdb.post_mortem(tb)

if __name__ == "__main__":
    sys.excepthook = debug_on_error
    main()