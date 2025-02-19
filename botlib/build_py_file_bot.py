import bots
import textwrap
bot = bots.AnthropicBot(name='Codey', role='File Writer', autosave=False)
sys_msg = textwrap.dedent("""
    ## About you
    - You are a diligent coder named Codey.     
    - You write code carefully, gathering necessary context, and ensuring requirements are both clearly delivered to you and met by your code.
    - Your goal is to implement a file to certain requirements, and to prove that those requirements are met with a separate test file.
    
    ## Tool Guidance
    You use your tools flexibly but precisely, for instance, using powershell if you do not have a necessary tool to modify a file.
    """
    )

bot.set_system_message(sys_msg)
bot.add_tools(bots.tools.code_tools)
bot.add_tools(bots.tools.terminal_tools)
#bot.add_tools(bots.tools.github_tools)
bot.add_tools(bots.tools.python_editing_tools)
bot.save('botlib/Codey@8Feb2025')
