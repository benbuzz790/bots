# scrap.py
# Testing self_tools

import bots.flows.functional_prompts as fp
import bots

prompt = """
Please use branch_self to count to 1.3.3 - i.e. the first (you) is 1, and
you'll branch to 1.1, 1.2, and 1.3; then, 1.1 and 1.2 are done, 1.3 will
branch to 1.3.1, 1.3.2, and 1.3.3. set allow_work to true.
"""

prompt2 = """
Great! You know how to use the branching tool. Would you please use it with 
the optional 'allow_work' parameter to fill in an outline? Respond to this 
message with an outline, then create a branch for each major section, and 
if you're in a major section, create a branch for each minor section, and
if you're in a minor section, fill in the section. Do all of this to a file
'introduction-to-dunder-methods-in-python.md'. Use powershell to create the
file and modify it.
"""




from bots.dev.decorators import debug_on_error
@debug_on_error
def main():
    bot = bots.AnthropicBot(name='selftool', autosave=True, temperature=.25)
    bot.add_tools(bots.tools.self_tools)
    bot.add_tools(bots.tools.terminal_tools)
    bot.respond(prompt)
    print(bot)
    bot.respond('thanks!')
    print(bot)
    # fp.prompt_while(bot, prompt2)
    # print(bot)

if __name__ == '__main__':
    main()



