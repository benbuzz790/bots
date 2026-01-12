"""
Example: Using BotSession for programmatic bot interaction.

This demonstrates how plugins like obsidian-vault-agent can use BotSession
directly without subprocess overhead.
"""

from bots.dev.bot_session import BotSession


def main():
    """Demonstrate BotSession usage."""
    print("Creating BotSession...")
    session = BotSession(auto_initialize=True)

    # Example 1: Simple chat
    print("\n--- Example 1: Simple Chat ---")
    response = session.input("What is the capital of France?")
    print(f"Bot: {response}")

    # Example 2: Using commands
    print("\n--- Example 2: Commands ---")
    help_text = session.input("/help")
    print(f"Available commands: {len(help_text)} chars of help text")

    # Example 3: Saving and loading
    print("\n--- Example 3: Save/Load ---")
    save_response = session.input("/save example_bot")
    print(f"Save result: {save_response}")

    # Example 4: Accessing bot directly
    print("\n--- Example 4: Direct Bot Access ---")
    bot = session.bot
    if bot:
        print(f"Bot name: {bot.name}")
        print(f"Model: {bot.model_engine}")
        print(f"Conversation depth: {len(bot.conversation.get_path_to_root())}")

    # Example 5: Configuration
    print("\n--- Example 5: Configuration ---")
    config = session.get_config()
    print(f"Max tokens: {config.max_tokens}")
    print(f"Temperature: {config.temperature}")
    print(f"Verbose mode: {config.verbose}")

    # Example 6: Multiple interactions with context
    print("\n--- Example 6: Context Preservation ---")
    session.input("Remember: my favorite color is blue")
    response = session.input("What's my favorite color?")
    print(f"Bot remembers: {'blue' in response.lower()}")

    print("\n✓ BotSession provides clean programmatic access!")


if __name__ == "__main__":
    main()
