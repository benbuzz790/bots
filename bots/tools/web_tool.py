"""Web search tool using Anthropic's internal web search capability.

This module provides an agentic search tool that leverages Claude's built-in web search
functionality using the raw Anthropic client directly.
"""

import os

import anthropic

from bots.dev.decorators import toolify


@toolify("Perform an agentic web search using Claude's internal web search capabilities")
def web_search(question: str) -> str:
    """Perform an intelligent web search and return raw API results.

    This tool uses Claude's built-in web search functionality to perform searches
    and returns the complete raw API response, including all search results,
    metadata, and processing information.

    Args:
        question (str): The search goal framed as a question.
        Good examples:
            "Who is Ben Rinauto?"
            "What is the connection between Paris, France and Buffalo, NY?"
        Bad examples:
            "Ben R wrestling"
            "paris buffalo"

    Returns:
        str: Raw API response from the web search as a string
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

        # Return raw response which includes citations and other useful info
        # TODO process and extract just info and citations.
        raw_response_str = str(response)
        return f"Raw API Response:\n{raw_response_str}"

    except Exception as e:
        return f"Web search failed: {str(e)}"
