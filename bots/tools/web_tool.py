"""Web search tool using Anthropic's internal web search capability.

This module provides an agentic search tool that leverages Claude's built-in web search
functionality using the raw Anthropic client directly.
"""

import os

import anthropic

from bots.dev.decorators import toolify


def _validate_question_format(query: str) -> bool:
    """Use a simple Haiku bot to validate if input is formatted as a question.

    Args:
        query (str): The input query to validate

    Returns:
        bool: True if formatted as a question, False otherwise

    Raises:
        ValueError: If query is not formatted as a question
    """
    try:
        # Get API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return True  # Skip validation if no API key

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # Simple validation prompt for Haiku
        validation_prompt = f'''Is this text formatted as a question? Answer only Y or N.

Text: "{query}"

Answer:'''

        # Make API call with Haiku (fast and cheap)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            temperature=0.0,
            messages=[{"role": "user", "content": validation_prompt}]
        )

        # Extract the response
        answer = response.content[0].text.strip().upper()

        if answer.startswith('N'):
            raise ValueError(
                "Input queries must be formatted as questions. "
                "Good examples: 'Who is...?', 'What is...?', 'How does...?' "
                "Bad examples: 'Ben R wrestling', 'paris buffalo'"
                "The more information, and the more specific, the better. You are asking an AI to answer a question, not performing a traditional web keyword search."
            )

        return True

    except ValueError:
        raise  # Re-raise validation errors
    except Exception:
        return True  # Skip validation on other errors



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
        # Validate that input is formatted as a question
        _validate_question_format(question)

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

        # Write raw API response to file immediately - DO NOT READ THIS FILE IN CONTEXT!
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_search_raw_api_response_{timestamp}.txt"
        
        # Extract clean, essential content from the web search response
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_search_clean_output_{timestamp}.txt"

        def extract_clean_content(response):
            """Extract only the essential content from web search response."""
            result = []
            result.append("=== WEB SEARCH RESULTS ===\n")
            result.append(f"Search: \"{question}\"\n")

            if hasattr(response, "content") and response.content:
                text_responses = []
                search_results = []

                for block in response.content:
                    # Extract Claude's text responses
                    if hasattr(block, 'type') and block.type == 'text' and hasattr(block, 'text') and block.text:
                        text_responses.append(block.text)

                    # Extract web search results
                    elif hasattr(block, 'type') and block.type == 'web_search_tool_result':
                        if hasattr(block, 'content') and block.content:
                            for item in block.content:
                                if isinstance(item, dict) and item.get('type') == 'web_search_result':
                                    search_results.append({
                                        'title': item.get('title', 'No title'),
                                        'url': item.get('url', 'No URL'),
                                        'age': item.get('page_age', 'Unknown age')
                                    })

                # Add Claude's responses
                if text_responses:
                    result.append("=== CLAUDE'S ANALYSIS ===\n")
                    for i, text in enumerate(text_responses, 1):
                        result.append(f"{i}. {text}\n")
                    result.append("")

                # Add search results
                if search_results:
                    result.append("=== SOURCES FOUND ===\n")
                    for i, item in enumerate(search_results, 1):
                        result.append(f"{i}. {item['title']}")
                        result.append(f"   {item['url']}")
                        if item['age'] and item['age'] != 'Unknown age':
                            result.append(f"   ({item['age']})")
                        result.append("")

                result.append(f"Search performed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")

            return "\n".join(result)

        # Write clean output to file
        clean_content = extract_clean_content(response)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(clean_content)

        # Return the clean content directly instead of just filename
        return clean_content

    except Exception as e:
        return f"Web search failed: {str(e)}"