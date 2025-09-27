"""Web search tool using Anthropic's internal web search capability.

This module provides an agentic search tool that leverages Claude's built-in web search
functionality using the raw Anthropic client directly.
"""

import os

import anthropic

from bots.dev.decorators import toolify


@toolify("Perform an agentic web search using Claude's internal web search capabilities")
def web_search(question: str) -> str:
    """Perform an intelligent web search and return organized results.

    This tool uses Claude's built-in web search functionality to perform searches
    and returns organized, pertinent information extracted from the results.

    Args:
        question (str): The search goal framed as a question.
        Good examples:
            "Who is Ben Rinauto?"
            "What is the connection between Paris, France and Buffalo, NY?"
        Bad examples:
            "Ben R wrestling"
            "paris buffalo"

    Returns:
        str: Organized search results with key information extracted
    """
    try:
        # Get API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "Error: ANTHROPIC_API_KEY environment variable not set"

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # Create the web search tool schema
        tools = [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            }
        ]

        # Create the search prompt
        search_prompt = f"""I need you to search the web answers to this question: "{question}"

        Please use the web search tool to find current, relevant information to precisely and
        accurately answer this question."""

        # Make the API call with web search enabled
        response = client.messages.create(
            model="claude-opus-4-1",
            max_tokens=16384,
            temperature=0.3,
            tools=tools,
            messages=[{"role": "user", "content": search_prompt}],
        )

        # Extract and organize the pertinent information
        raw_response_str = str(response)

        # Split into text blocks and extract content
        text_blocks = raw_response_str.split("TextBlock(")
        extracted_content = []

        for block in text_blocks:
            # Look for text content in double quotes
            if 'text="' in block:
                start_idx = block.find('text="') + 6
                end_idx = block.find('", type=')
                if end_idx > start_idx:
                    content_text = block[start_idx:end_idx]
                    if len(content_text.strip()) > 5:
                        extracted_content.append(content_text.strip())

        # Format the organized response
        if extracted_content:
            result_parts = ["=== SEARCH RESULTS ==="]
            for i, content in enumerate(extracted_content[:10], 1):
                result_parts.append(f"{i}. {content}")
            return "\n".join(result_parts)
        else:
            return "No structured content found in search results."

    except Exception as e:
        return f"Web search failed: {str(e)}"
