import subprocess
import json
import re
import sys

def get_CR_feedback(pr_id: str, repo: str="promptfoo/promptfoo") -> str:
    """
    Extract Code Rabbit feedback from a GitHub PR reviews, focusing on AI Agent prompts.
    Args:
        pr_id: The PR number (e.g., "4485")
        repo: The repository in format "owner/repo" (default: "promptfoo/promptfoo")
    Returns:
        String containing either:
        - The Code Rabbit review feedback content with AI Agent prompts
        - "Code Rabbit is still processing changes. Try again later."
        - "No Code Rabbit feedback found. CR may not be set up for this repo."
        - Error message if API call fails
    """
    try:
        # Get all reviews from the PR
        cmd = ["gh", "api", f"repos/{repo}/pulls/{pr_id}/reviews"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            return f"Error fetching PR reviews: {result.stderr}"
        # Check if stdout is empty or None
        if not result.stdout or result.stdout.strip() == "":
            return "No response from GitHub API. The PR may not exist or you may not have access."
        try:
            reviews = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return f"Error parsing GitHub API response: {str(e)}. Raw response: {result.stdout[:200]}..."
        # Find Code Rabbit reviews
        coderabbit_reviews = [review for review in reviews if "coderabbit" in review["user"]["login"].lower()]
        if not coderabbit_reviews:
            return "No Code Rabbit feedback found. CR may not be set up for this repo."
        # Find the review with the most detailed feedback
        best_review = None
        max_score = 0
        for review in coderabbit_reviews:
            body = review["body"]
            actionable_match = re.search('\*\*Actionable comments posted: (\d+)\*\*', body)
            if actionable_match:
                count = int(actionable_match.group(1))
                has_nitpicks = "🧹 Nitpick comments" in body
                has_additional = "🔇 Additional comments" in body
                score = count + (10 if has_nitpicks else 0) + (5 if has_additional else 0)
                if score > max_score:
                    max_score = score
                    best_review = review
        if not best_review:
            best_review = coderabbit_reviews[-1]  # fallback to most recent
        review_body = best_review["body"]
        # Check if Code Rabbit is still processing
        if "processing new changes" in review_body.lower() or "review in progress" in review_body.lower():
            return "Code Rabbit is still processing changes. Try again later."
        # Extract actionable feedback
        feedback_parts = []
        # Extract actionable comments count
        actionable_match = re.search('\*\*Actionable comments posted: (\d+)\*\*', review_body)
        if actionable_match:
            count = actionable_match.group(1)
            feedback_parts.append(f"Actionable comments: {count}")
        # Function to extract AI Agent prompts from any section

        def extract_ai_prompts(content, section_name):
            ai_prompts = []
            # Look for "🤖 Prompt for AI Agents" sections with various patterns
            patterns = [r'🤖\s*Prompt for AI Agents[:\s]*\n?(.*?)(?=\n\n|\n---|\n`|</blockquote>|🤖|$)', r'🤖[^🤖]*?Prompt[^🤖]*?Agent[^🤖]*?\n?(.*?)(?=\n\n|\n---|\n`|</blockquote>|🤖|$)']
            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    clean_prompt = match.strip()
                    if clean_prompt and len(clean_prompt) > 10:
                        # Clean up HTML tags and normalize whitespace
                        clean_prompt = re.sub('<[^>]+>', '', clean_prompt)
                        clean_prompt = re.sub('\s+', ' ', clean_prompt).strip()
                        if clean_prompt not in ai_prompts:  # Avoid duplicates
                            ai_prompts.append(clean_prompt)
            if ai_prompts:
                feedback_parts.append(f"\n## 🤖 AI Agent Prompts from {section_name}:")
                for i, prompt in enumerate(ai_prompts, 1):
                    feedback_parts.append(f"{i}. {prompt}")
            return ai_prompts
        # Search the entire review body for AI prompts first
        extract_ai_prompts(review_body, "Full Review")
        # Extract nitpick comments with improved parsing
        nitpick_section = re.search('<summary>🧹 Nitpick comments \(\d+\)</summary><blockquote>(.*?)</blockquote></details>', review_body, re.DOTALL)
        if nitpick_section:
            nitpick_content = nitpick_section.group(1)
            print(f"DEBUG: Found nitpick section with {len(nitpick_content)} characters")
            # Extract AI prompts from nitpick section
            extract_ai_prompts(nitpick_content, "Nitpick Comments")
            # Extract file-specific feedback with better parsing
            file_sections = re.findall('<details>\s*<summary>([^<]+)</summary><blockquote>(.*?)</blockquote></details>', nitpick_content, re.DOTALL)
            print(f"DEBUG: Found {len(file_sections)} file sections")
            if file_sections:
                feedback_parts.append("\n## 🧹 Nitpick Comments:")
                for file_name, file_content in file_sections:
                    feedback_parts.append(f"\n### {file_name.strip()}")
                    print(f"DEBUG: Processing file {file_name.strip()} with {len(file_content)} characters")
                    # Extract AI prompts from this file's content
                    extract_ai_prompts(file_content, f"file {file_name.strip()}")
                    # Parse the specific format we see in the debug output
                    # Look for patterns like: `163-209`: **Summary math will output `NaN` / incorrect percentages**
                    # followed by description text
                    # Split content by line ranges to handle each comment separately
                    comment_blocks = re.split('(?=`[^`]+`:\s*\*\*)', file_content)
                    print(f"DEBUG: Split into {len(comment_blocks)} comment blocks")
                    for i, block in enumerate(comment_blocks):
                        if not block.strip():
                            continue
                        print(f"DEBUG: Processing block {i}: {block[:100]}...")
                        # Extract line range and title
                        line_match = re.match('`([^`]+)`:\s*\*\*([^*]+)\*\*\s*(.*)', block, re.DOTALL)
                        if line_match:
                            line_range = line_match.group(1).strip()
                            title = line_match.group(2).strip()
                            description = line_match.group(3).strip()
                            print(f"DEBUG: Found match - Line: {line_range}, Title: {title[:50]}...")
                            feedback_parts.append(f"- **{line_range}**: {title}")
                            if description:
                                # Clean up the description
                                # Remove code blocks but indicate they were there
                                clean_desc = re.sub('```[^`]*?```', '[code example provided]', description, flags=re.DOTALL)
                                # Remove nested HTML details/summary tags
                                clean_desc = re.sub('<details>.*?</details>', '[additional details provided]', clean_desc, flags=re.DOTALL)
                                # Remove other HTML tags
                                clean_desc = re.sub('<[^>]+>', '', clean_desc)
                                # Normalize whitespace
                                clean_desc = re.sub('\s+', ' ', clean_desc).strip()
                                if clean_desc and len(clean_desc) > 10:
                                    if len(clean_desc) > 400:
                                        feedback_parts.append(f"  {clean_desc[:400]}...")
                                    else:
                                        feedback_parts.append(f"  {clean_desc}")
                        else:
                            print(f"DEBUG: No match found for block {i}")
        # Extract additional comments (positive feedback)
        additional_section = re.search('<summary>🔇 Additional comments \(\d+\)</summary><blockquote>(.*?)</blockquote></details>', review_body, re.DOTALL)
        if additional_section:
            additional_content = additional_section.group(1)
            # Extract AI prompts from additional section
            extract_ai_prompts(additional_content, "Additional Comments")
            # Extract file-specific feedback using same approach as nitpicks
            file_sections = re.findall('<details>\s*<summary>([^<]+)</summary><blockquote>(.*?)</blockquote></details>', additional_content, re.DOTALL)
            if file_sections:
                feedback_parts.append("\n## 🔇 Additional Comments (Positive Feedback):")
                for file_name, file_content in file_sections:
                    feedback_parts.append(f"\n### {file_name.strip()}")
                    # Extract AI prompts from this file's content
                    extract_ai_prompts(file_content, f"file {file_name.strip()}")
                    # Parse comments using same approach as nitpicks
                    comment_blocks = re.split('(?=`[^`]+`:\s*\*\*)', file_content)
                    for block in comment_blocks:
                        if not block.strip():
                            continue
                        line_match = re.match('`([^`]+)`:\s*\*\*([^*]+)\*\*\s*(.*)', block, re.DOTALL)
                        if line_match:
                            line_range = line_match.group(1).strip()
                            title = line_match.group(2).strip()
                            description = line_match.group(3).strip()
                            feedback_parts.append(f"- **{line_range}**: {title}")
                            if description:
                                clean_desc = re.sub('```[^`]*?```', '[code example provided]', description, flags=re.DOTALL)
                                clean_desc = re.sub('<details>.*?</details>', '[additional details provided]', clean_desc, flags=re.DOTALL)
                                clean_desc = re.sub('<[^>]+>', '', clean_desc)
                                clean_desc = re.sub('\s+', ' ', clean_desc).strip()
                                if clean_desc and len(clean_desc) > 10:
                                    if len(clean_desc) > 400:
                                        feedback_parts.append(f"  {clean_desc[:400]}...")
                                    else:
                                        feedback_parts.append(f"  {clean_desc}")
        # Extract duplicate comments
        duplicate_section = re.search('<summary>♻️ Duplicate comments \(\d+\)</summary><blockquote>(.*?)</blockquote></details>', review_body, re.DOTALL)
        if duplicate_section:
            duplicate_content = duplicate_section.group(1)
            extract_ai_prompts(duplicate_content, "Duplicate Comments")
        # Extract files processed info
        files_match = re.search('<summary>📒 Files selected for processing \((\d+)\)</summary>\s*\*(.*?)\*', review_body, re.DOTALL)
        if files_match:
            file_count = files_match.group(1)
            files_list = files_match.group(2).strip()
            feedback_parts.append(f"\n## 📒 Files Processed ({file_count}):")
            # Extract filenames from backticks
            files = re.findall('`([^`]+)`', files_list)
            if files:
                for file_name in files:
                    # Only include actual filenames (contain a dot and reasonable length)
                    if '.' in file_name and len(file_name) < 100 and (not file_name.strip() in [',', ' ']):
                        feedback_parts.append(f"- {file_name}")
        # Extract skipped files info
        skipped_match = re.search('<summary>🚧 Files skipped from review as they are similar to previous changes \((\d+)\)</summary>\s*\*(.*?)\*', review_body, re.DOTALL)
        if skipped_match:
            skipped_count = skipped_match.group(1)
            skipped_list = skipped_match.group(2).strip()
            feedback_parts.append(f"\n## 🚧 Files Skipped ({skipped_count}):")
            files = re.findall('`([^`]+)`', skipped_list)
            for file_name in files:
                if '.' in file_name and len(file_name) < 100:
                    feedback_parts.append(f"- {file_name} (similar to previous changes)")
        if not feedback_parts:
            # If no structured content found, check for simple cases
            if "skipped from review" in review_body:
                return "Code Rabbit skipped detailed review (similar to previous changes)."
            elif "Actionable comments posted: 0" in review_body:
                return "Code Rabbit reviewed the changes but found no actionable issues."
            else:
                return "Code Rabbit comment found but no specific feedback extracted."
        return "\n".join(feedback_parts)
    except subprocess.TimeoutExpired:
        return "Timeout while fetching PR reviews. Try again later."
    except Exception as e:
        return f"Unexpected error: {str(e)}"
# Example usage
if __name__ == "__main__":
    feedback = get_CR_feedback("4485")
    print(feedback)