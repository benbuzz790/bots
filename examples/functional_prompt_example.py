import sys
import os


import bots
import bots.functional_prompts as fp
import bots.tools.python_tools as py_tools

def main():
    n_steps = 4
    p1 = f"""Please make a terminal-based connect four game in connect_four.py.
    It should meet the following requirements:
        1) Allow two players to play on a single device inside a terminal
        2) Be structured to allow a GUI later on (do not make a GUI).
        3) Be tested."""
    p2 = f"""Today we're working on connect_four.py. It's already
        in a usable state, allowing two players to play on a single device
        inside a terminal. I'd like to upgrade to a GUI while keeping the 
        current code intact. The GUI should meet the following requirements:
        1) Display a 6x7 (typical) connect four board
        2) Animate the pieces falling into place
        3) Highlight the column the piece will be placed into before the user clicks
        4) Be tested - ensure elements are non-overlapping (unless it's intended) and 
        ensure the circle piece elements are centered on the holes after the animation.
        Game logic does not have to be tested as it's already contained in connect_four.py
        5) Display the winner at the end of the game
        6) Have shaded graphics to simulate 3 dimensionality
        7) Save to connect_four_gui.py"""
    
    bot = bots.AnthropicBot(name="logic")
    bot2 = bots.AnthropicBot(name="gui")
    bot.add_tools(py_tools)
    bot2.add_tools(py_tools)

    fp.sequential_process(bot, p1, n_steps)
    fp.sequential_process(bot2, p2, 2*n_steps)

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


