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

    # Example 3: Saving using API (non-interactive)
    print("\n--- Example 3: Save via API ---")
    if session.bot:
        try:
            session.bot.save("example_bot.bot")
            print("Bot saved successfully to example_bot.bot")
        except Exception as e:
            print(f"Save failed: {e}")
    else:
        print("No bot available to save")

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

    # Example 6: Short-term context within same session
    print("\n--- Example 6: Context Preservation (Same Session) ---")
    session.input("Remember: my favorite color is blue")
    response = session.input("What's my favorite color?")
    # Check if the bot can recall within the same session
    if "blue" in response.lower():
        print("Bot remembers within session: ✓")
    else:
        print(f"Bot response: {response}")

    print("\n✓ BotSession provides clean programmatic access!")


if __name__ == "__main__":
    main()
