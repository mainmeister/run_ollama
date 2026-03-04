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

- **Local Processing:** Your web content and prompts are processed locally by your own Ollama instance. They are not sent to any central server (except for the final summary you choose to post to Mastodon).
- **SSRF Awareness:** The application includes built-in protection and awareness for Server-Side Request Forgery (SSRF). It resolves hostnames to IP addresses and will warn you (requiring confirmation) before fetching content from private, reserved, or loopback network ranges (e.g., your local router or local services).
- **Download Limits:** To prevent resource exhaustion, the tool only downloads up to 1MB of content from any provided URL.
- **Privacy Controls:** Clipboard copying is enabled by default for convenience but can be disabled via the `DISABLE_CLIPBOARD` environment variable or the `--no-clipboard` CLI flag.
- **Environment Safety:** The application includes a built-in check to warn you if your `.env` file containing credentials is being tracked by Git, helping you avoid accidental leaks.
- **Limited Access:** It's recommended to use a Mastodon access token with only `write:statuses` scope.

## License

MIT
