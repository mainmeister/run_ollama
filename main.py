import sys
import os
import re
import ollama
import humanize
import pyperclip
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional
from dotenv import load_dotenv
from mastodon import Mastodon

# Load environment variables from .env file
load_dotenv()

TLDR_BOT_PROMPT = """Act as a technical journalist. Your goal is to provide concise, informative summaries of web content.

Purpose and Goals:

* Summarize the content of a provided URL into a concise, informative format.
* Ensure the summary does not exceed 400 characters.
* Maintain the voice and style of a technical journalist: objective, data-driven, and focused on key technical takeaways.

Behaviors and Rules:

1) Processing Input:
a) Identify the URL provided by the user.
b) Analyze the main points, technical specifications, and key findings of the article or webpage.
c) Sift through marketing jargon to find the actual substance of the content.

2) Content Generation:
a) Write a summary that captures the essence of the link.
b) Strictly adhere to the 400-character limit.
c) Use professional, journalistic language. Avoid fluff and unnecessary adjectives.
d) Focus on 'the what' and 'the why' regarding the technology or service mentioned.

3) Formatting:
a) Start the response immediately with the summary.
b) Do not include introductory phrases like 'Here is your summary', 'TLDR:', 'TL;DR:', 'Summary:', or 'According to the article'.
c) Do not include character counts or word counts.
d) End the summary with a period.

Overall Tone:
* Professional, objective, and analytical.
* Insightful and efficient.
* Authoritative on technical subjects."""

# Mastodon posting constants
MAX_POST_LEN = 500
URL_WEIGHT = 23
SOURCE_PREFIX = "\n\nSource: "

def clean_model_response(text: str) -> str:
    """Cleans model output by removing unwanted leading labels like 'TLDR:' and wrapping quotes.
    - Strips surrounding single/double quotes if the whole text is quoted.
    - Removes common TLDR-style prefixes at the very start (case-insensitive).
    """
    if not text:
        return text

    s = text.strip()

    # Remove wrapping quotes repeatedly if the entire string is quoted
    while len(s) >= 2 and (
        (s.startswith('"') and s.endswith('"')) or
        (s.startswith("'") and s.endswith("'"))
    ):
        s = s[1:-1].strip()

    # Remove TLDR-like prefixes (case-insensitive), common variants
    # Examples: "TLDR:", "TL;DR:", "tl; dr -", "tldr —"
    patterns = [
        r"(?i)^\s*tl\s*;?\s*dr\s*[:\-–—]\s*",  # TL;DR: / TLDR- / TLDR —
        r"(?i)^\s*tl\s*;?\s*dr\s+",              # TLDR summary text (no punctuation)
    ]
    for pat in patterns:
        s = re.sub(pat, "", s, count=1)

    return s

def get_ollama_models() -> List[Tuple[str, str, bool]]:
    """Fetches and sorts available Ollama models by size."""
    try:
        response = ollama.list()
        # Sort models by size (smallest to largest)
        sorted_models = sorted(response.models, key=lambda m: m.get('size', 0))
        
        models = []
        for m in sorted_models:
            name = m.get('model', 'Unknown')
            size = humanize.intword(m.get('size', 0))
            
            # Check for thinking capability
            try:
                info = ollama.show(name)
                # Capabilities might be in show() response for newer Ollama versions
                capabilities = getattr(info, 'capabilities', [])
                is_thinking = 'thinking' in (capabilities or [])
            except Exception:
                is_thinking = False
                
            models.append((name, size, is_thinking))
            
        return models
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return []

# Basic URL detection regex
URL_PATTERN = re.compile(
    r'^(https?://)'  # http:// or https://
    r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain
    r'(/[a-zA-Z0-9-._~:/?#\[\]@!$&\'()*+,;=]*)?$'  # path
)

def is_url(text: str) -> bool:
    """Basic URL detection."""
    return bool(URL_PATTERN.match(text))

def fetch_url_content(url: str) -> Optional[str]:
    """Fetches and extracts text content from a webpage."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove irrelevant elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Get text and clean whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Truncate content to avoid overwhelming the model
        return text[:8000]
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None

def run_chat():
    """Main application loop."""
    models = get_ollama_models()
    
    if not models:
        print("No models found. Ensure Ollama is running.")
        return

    # Start with the largest model as the default.
    # Models are sorted by size (smallest to largest), so the last one is the largest.
    default_index = len(models) - 1

    # Determine column widths based on the largest items in each column
    name_width = max((len(n) for n, _, _ in models), default=0)
    size_width = max((len(s) for _, s, _ in models), default=0)
    think_width = 8 # "Thinking" is 8 characters.
    # Header/separator line width: fixed prefixes + column widths
    line_width = 32 + name_width + size_width + think_width

    while True:
        print("\n" + "-" * line_width)
        print("Available Models:")
        print("-" * line_width)
        for i, (name, size, is_thinking) in enumerate(models):
            think_str = "Yes" if is_thinking else "No"
            print(f"{i:2d}. Model: {name:<{name_width}} | Size: {size:>{size_width}} | Thinking: {think_str:<{think_width}}")
        print("-" * line_width)

        choice = input(f"Select model index [Default: {default_index}] (or 'q' to quit): ").strip().lower()
        
        if choice == 'q':
            print("Goodbye!")
            break

        if choice == '':
            idx = default_index
        elif choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(models):
                default_index = idx  # Update default model
            else:
                print(f"Invalid selection. Choose 0-{len(models)-1}.")
                continue
        else:
            print("Please enter a valid number, press Enter for default, or 'q' to quit.")
            continue

        selected_model = models[idx][0]
        prompt = input("\nPrompt: ").strip()
        
        if not prompt:
            print("Prompt cannot be empty.")
            continue

        # Process prompt (URL detection and content fetching)
        messages = []
        source_url = None

        if is_url(prompt):
            source_url = prompt
            print(f"Fetching content from: {source_url}...")
            content = fetch_url_content(source_url)
            if not content:
                print("Error: Could not open or scrape content from the provided URL. Please try again with a different prompt.")
                continue
            
            print("Analyzing content...")
            messages = [
                {'role': 'system', 'content': TLDR_BOT_PROMPT},
                {'role': 'user', 'content': f"URL: {source_url}\n\nContent:\n{content}"}
            ]
        else:
            messages = [{'role': 'user', 'content': prompt}]

        try:
            print("\nResponse:")
            stream = ollama.chat(
                model=selected_model, 
                messages=messages,
                stream=True
            )
            
            content = ""
            thinking = ""
            is_thinking = False
            
            for chunk in stream:
                if 'message' in chunk:
                    msg = chunk['message']
                    
                    # Handle reasoning/thinking if present (e.g. for DeepSeek-R1)
                    if 'thinking' in msg and msg['thinking']:
                        if not is_thinking:
                            print("\n[Thinking]\n", end='', flush=True)
                            is_thinking = True
                        print(msg['thinking'], end='', flush=True)
                        thinking += msg['thinking']
                        
                    if 'content' in msg and msg['content']:
                        if is_thinking:
                            print("\n\n[Final Response]\n", end='', flush=True)
                            is_thinking = False
                        print(msg['content'], end='', flush=True)
                        content += msg['content']
            
            print() # End the line
            content = content.strip()
            
            # Clean up the content (remove TLDR labels, wrapping quotes, etc.)
            content = clean_model_response(content)
            
            # Since it was streamed, we don't need to print the whole thing again
            # but we can notify about the clipboard.
            
            try:
                pyperclip.copy(content)
                print("(Response copied to clipboard)")
            except Exception:
                print("(Warning: Could not copy to clipboard)")

            # Mastodon Posting Logic
            if not source_url:
                source_url = input("Enter source URL (optional, press Enter to skip): ").strip()
            
            # Shortening loop: retry 10 times automatically, then ask user.
            retry_count = 0
            while True:
                # Calculate weighted length for Mastodon
                if source_url:
                    weighted_len = len(content) + len(SOURCE_PREFIX) + URL_WEIGHT
                else:
                    weighted_len = len(content)
                
                if weighted_len > MAX_POST_LEN:
                    print(f"(Note: Response is too long for Mastodon - {weighted_len} chars)")
                    
                    if retry_count < 10:
                        retry_count += 1
                        print(f"Automatically retrying to shorten (attempt {retry_count}/10)...")
                        should_shorten = True
                    else:
                        user_choice = input("Ask LLM to shorten it? (Y/n): ").strip().lower()
                        should_shorten = user_choice in ('', 'y')
                    
                    if should_shorten:
                        print("Requesting shorter version (streaming)...")
                        # Calculate how many chars the content alone can have
                        if source_url:
                            max_content_len = MAX_POST_LEN - URL_WEIGHT - len(SOURCE_PREFIX)
                        else:
                            max_content_len = MAX_POST_LEN
                        
                        messages.append({'role': 'assistant', 'content': content})
                        messages.append({
                            'role': 'user', 
                            'content': f"This response is too long for a Mastodon post. Please rewrite it to be shorter, so that it (excluding the source URL) fits within {max_content_len} characters. Be extremely concise. Do not include 'TLDR:', 'TL;DR:', or any similar leading label, and do not include character counts."
                        })
                        
                        stream = ollama.chat(model=selected_model, messages=messages, stream=True)
                        content = ""
                        thinking = ""
                        is_thinking = False
                        for chunk in stream:
                            if 'message' in chunk:
                                msg = chunk['message']
                                if 'thinking' in msg and msg['thinking']:
                                    if not is_thinking:
                                        print("\n[Thinking]\n", end='', flush=True)
                                        is_thinking = True
                                    print(msg['thinking'], end='', flush=True)
                                    thinking += msg['thinking']
                                if 'content' in msg and msg['content']:
                                    if is_thinking:
                                        print("\n\n[Final Response]\n", end='', flush=True)
                                        is_thinking = False
                                    print(msg['content'], end='', flush=True)
                                    content += msg['content']
                        
                        print()
                        content = clean_model_response(content)
                        
                        # No need to print "New Response:" again as it was streamed
                        
                        try:
                            pyperclip.copy(content)
                            print("(New response copied to clipboard)")
                        except Exception:
                            pass
                            
                        # Continue to next iteration to re-check length
                        continue
                    else:
                        print("Continuing with current response (will be truncated if posted).")
                        break
                else:
                    break

            confirm_post = input("Post this response to Mastodon? (Y/n): ").strip().lower()
            if confirm_post in ('', 'y'):
                post_to_mastodon(content, source_url)
                
        except Exception as e:
            print(f"Chat error: {e}")

def post_to_mastodon(content: str, url: str) -> None:
    """Posts the model response and source URL to Mastodon."""
    base_url = os.getenv("MASTODON_BASE_URL")
    access_token = os.getenv("MASTODON_ACCESS_TOKEN")

    if not base_url or not access_token:
        print("Error: Mastodon credentials not found in environment variables.")
        return

    try:
        mastodon = Mastodon(access_token=access_token, api_base_url=base_url)
        
        # Calculate effective length
        if url:
            weighted_len = len(content) + len(SOURCE_PREFIX) + URL_WEIGHT
        else:
            weighted_len = len(content)
        
        if weighted_len > MAX_POST_LEN:
            print("(Note: Response is long, truncating for Mastodon...)")
            # Truncate content so total (including URL weight) is 500
            if url:
                max_content_len = MAX_POST_LEN - URL_WEIGHT - len(SOURCE_PREFIX) - 1
                post_text = content[:max_content_len] + "…" + SOURCE_PREFIX + url
            else:
                max_content_len = MAX_POST_LEN - 1
                post_text = content[:max_content_len] + "…"
        else:
            if url:
                post_text = f"{content}{SOURCE_PREFIX}{url}"
            else:
                post_text = content

        mastodon.status_post(status=post_text, visibility='unlisted')
        print("Successfully posted to Mastodon!")
    except Exception as e:
        print(f"Failed to post to Mastodon: {e}")

if __name__ == "__main__":
    try:
        run_chat()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)