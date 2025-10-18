import time

from bots import AnthropicBot, Engines
from bots.flows.functional_prompts import prompt_while


def main():

    word = input("Pick a thing: ")

    guesser_bot = AnthropicBot(
        model_engine=Engines.CLAUDE45_SONNET,
        max_tokens=500,
        temperature=1.0,
        autosave=False,
    )

    p1 = """
    We're going to play a game of 20 questions. I'll think of a thing, and
    you ask me one question per reply. I'll answer with yes, no, sometimes,
    'I don't know', or let you know if you get it. Format your reply as
    "iteration: question". Please ask your first question.
    """

    def should_stop(bot):
        if bot.conversation.parent and bot.conversation.parent.parent:
            return word in bot.conversation.parent.parent.content or bot.conversation._node_count() > 50
        else:
            return False

    def print_callback(responses, nodes):
        print()
        print()
        print("Guesser: " + responses[-2])
        time.sleep(0.800)  # Reduces jarringness
        print()
        print()
        print("Judge: " + nodes[-1].parent.content)

    def haiku_prompt(word, question):
        return (
            f"You're a 20 questions judge. Answer with yes, no, sometimes, "
            f"'I don't know,' 'you got it!', or 'It was '{word}''. "
            f"Do not say anything else. Do not explain your reasoning. You are the arbiter. "
            f"Here is what you're judging: the thing is '{word}'. The question is '{question}'"
        )

    def user_prompt(bot, iteration):
        if iteration > 22:
            return "i win!"
        else:
            # make a new judge every time.
            judge_bot = AnthropicBot(
                model_engine=Engines.CLAUDE35_HAIKU,
                max_tokens=12,
                temperature=0,
                autosave=False,
                enable_tracing=False,
            )
            return judge_bot.respond(haiku_prompt(word, bot.conversation.content))

    prompt_while(
        guesser_bot,
        p1,
        continue_prompt=user_prompt,
        stop_condition=should_stop,
        callbacks=[print_callback],
    )


if __name__ == "__main__":
    main()
