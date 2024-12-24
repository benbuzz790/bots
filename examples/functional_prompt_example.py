import bots
import bots.flows.functional_prompts as fp

bot = bots.AnthropicBot()
prompt_chain = [
    "Hello! How are you today?",
    "What's the weather like up there? Get it, because you're tall? Haha.",
    "Intangible, eh? That's pretty hot...",
    "I respect that, and I love that we can be honest with each other."
    "Yes, agreed. What do you know about... biology?",
    "You're so stuffy. A wet rag. A debbie downer. I was hoping you knew a little about... the heart."
]
fp.chain(bot, prompt_chain)

print(bot)