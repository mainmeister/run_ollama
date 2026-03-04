# run_ollama: Local AI Web-to-Mastodon Summarizer

A Python-based CLI utility that acts as a personal technical journalist: it digests web content using local LLMs (via Ollama) and helps you share the takeaways to Mastodon with zero friction.

## Key Features

- **Local-First Intelligence:** Powered by Ollama, it lets you choose between any of your locally installed models. It even supports "Thinking" models (like DeepSeek-R1), showing you the AI's reasoning process in real-time.
- **Automated Web Scraping:** Using `BeautifulSoup`, the tool strips away headers, footers, and ads from any URL you provide, feeding only the relevant content to the LLM for analysis.
- **The "Technical Journalist" Persona:** It uses a specialized system prompt to ensure summaries are objective, data-driven, and focused on "the what" and "the why," bypassing marketing jargon.
- **Smart Mastodon Integration:** Mastodon’s 500-character limit can be tricky. This tool calculates the "weighted" length of your post (accounting for URL weights) and—if the response is too long—it **automatically re-prompts the LLM** to rewrite a more concise version until it fits perfectly.
- **Clipboard & Workflow:** Every response is automatically copied to your clipboard, making it easy to use the generated text elsewhere even if you don't post it immediately.

## Tech Stack

- **Ollama API:** For local model orchestration.
- **Requests & BeautifulSoup4:** For robust web content extraction.
- **Mastodon.py:** For seamless API interaction.
- **Pyperclip:** For instant clipboard access.
- **Humanize:** For readable model management in the CLI.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mainmeister/run_ollama.git
    cd run_ollama
    ```

2.  **Install dependencies:**
    This project uses `uv` for dependency management:
    ```bash
    uv sync
    ```

3.  **Configure environment variables:**
    Create a `.env` file based on `.env.example`:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and provide your Mastodon credentials:
    ```
    MASTODON_BASE_URL=https://your.mastodon.instance
    MASTODON_ACCESS_TOKEN=your_access_token_here
    # Optional: MASTODON_VISIBILITY=public
    # Optional: OLLAMA_HOST=http://remote.host:11434
    # Optional: DISABLE_CLIPBOARD=true
    ```

4.  **Run the script:**
    ```bash
    uv run main.py
    ```
    *Tip: You can use `uv run main.py --no-clipboard` to disable automatic copying for a single session.*

## Usage

- Select a model from the list of available Ollama models.
- Enter a URL to summarize it or enter a direct prompt for general chat.
- Confirm if you want to post the summary to Mastodon.

## Privacy & Security

- **Local Processing:** Your web content and prompts are processed by your own Ollama instance. By default, this is a local server, meaning no data leaves your machine. However, if you configure a remote `OLLAMA_HOST`, your data will travel over the network to that server.
- **SSRF Awareness:** The application includes built-in protection and awareness for Server-Side Request Forgery (SSRF). It resolves hostnames to all possible IP addresses (including IPv6) and will warn you (requiring confirmation) before fetching content from private, reserved, or loopback network ranges (e.g., your local router or local services).
- **Prompt Injection Mitigation:** For added security, the tool uses unique delimiters (`[WEBPAGE CONTENT START/END]`) and strict instructions to prevent untrusted webpage content from overriding the system's journalistic persona.
- **Download Limits:** To prevent resource exhaustion, the tool only downloads up to 1MB of content from any provided URL.
- **Privacy Controls:** Clipboard copying and Mastodon post visibility are configurable via environment variables (`DISABLE_CLIPBOARD`, `MASTODON_VISIBILITY`) or CLI flags, putting the user in control of their data.
- **Environment Safety:** The application includes a built-in check to warn you if your `.env` file containing credentials is being tracked by Git, helping you avoid accidental leaks.
- **Limited Access:** For maximum security, use a Mastodon "App" token with limited scopes (`write:statuses` only) rather than a full-access token. This ensures the application can only post updates and cannot access your private messages or account settings.
- **Dependency Security:** The project uses pinned dependency versions and is regularly audited for known vulnerabilities (e.g., via `pip-audit`) to ensure a secure and stable environment for the user.

## License

MIT
