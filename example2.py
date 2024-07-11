
from bot_mailbox import OpenAIMailbox, AnthropicMailbox
import conversation_node as CN
import os

def main():
    # Initialize mailboxes
    openai_mailbox = OpenAIMailbox(verbose=True)
    anthropic_mailbox = AnthropicMailbox(verbose=True)

    # Create a conversation node
    conversation = CN.ConversationNode(role="user", content="Hello, can you introduce yourself?")

    # System messages
    openai_system_message = "You are a helpful assistant named GPT. Always start your response with 'GPT:'."
    anthropic_system_message = "You are a helpful assistant named Claude. Always start your response with 'Claude:'."

    # OpenAI example
    print("OpenAI Example:")
    openai_response = openai_mailbox.send_message(
        conversation=conversation,
        model="gpt-3.5-turbo",
        max_tokens=150,
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        system_message=openai_system_message
    )
    print(f"OpenAI Response: {openai_response[0]}\n")

    # Anthropic example
    print("Anthropic Example:")
    anthropic_response = anthropic_mailbox.send_message(
        conversation=conversation,
        model="claude-3-opus-20240229",
        max_tokens=150,
        temperature=0.7,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        system_message=anthropic_system_message
    )
    print(f"Anthropic Response: {anthropic_response[0]}\n")

if __name__ == "__main__":
    main()
