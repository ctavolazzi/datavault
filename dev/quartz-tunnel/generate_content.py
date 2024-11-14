import ollama
import os
from pathlib import Path
from datetime import datetime
import re

# Define absolute paths
SCRIPT_DIR = Path("/Users/ctavolazzi/Code/datavault/dev/quartz-tunnel")
QUARTZ_CONTENT_DIR = Path("/Users/ctavolazzi/Code/quartz/content")

# Update the default model
DEFAULT_MODEL = "nemotron-mini"

def sanitize_filename(title):
    """Convert title to valid filename"""
    filename = title.lower().replace(' ', '-')
    filename = re.sub(r'[^a-z0-9-]', '', filename)
    return f"{filename}.md"

def generate_content(topic, model=DEFAULT_MODEL):
    """Generate markdown content about a topic using Ollama"""
    print(f"Using {model} model to generate content...")

    prompt = f"""
    Create a detailed markdown document about {topic}.
    Include the following:
    - A clear title using # heading
    - A brief introduction
    - Several subheadings using ##
    - Relevant information and explanations
    - A conclusion

    Use proper markdown formatting including:
    - Lists where appropriate
    - *Emphasis* where needed
    - `Code blocks` if relevant
    - > Blockquotes for important points

    Start with this frontmatter:
    ---
    title: {topic}
    date: {datetime.now().strftime('%Y-%m-%d')}
    tags: [generated, {topic.lower()}]
    ---
    """

    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response['response']
    except Exception as e:
        raise Exception(f"Error generating content: {e}")

def save_content(content, topic):
    """Save the generated content to Quartz content directory"""
    filename = sanitize_filename(topic)
    filepath = QUARTZ_CONTENT_DIR / filename

    try:
        # Ensure the directory exists
        QUARTZ_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    except Exception as e:
        raise Exception(f"Error saving content: {e}")

def main():
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"Quartz content directory: {QUARTZ_CONTENT_DIR}")

    # Verify directories exist
    if not QUARTZ_CONTENT_DIR.exists():
        raise Exception(f"Quartz content directory not found: {QUARTZ_CONTENT_DIR}")

    # Get topic from user
    topic = input("What topic would you like to generate content about? ")
    model = input(f"Which Ollama model would you like to use? (default: {DEFAULT_MODEL}) ") or DEFAULT_MODEL

    print(f"\nGenerating content about '{topic}' using {model}...")

    try:
        # Generate content
        content = generate_content(topic, model)

        # Save content
        filepath = save_content(content, topic)

        print(f"\nContent successfully generated and saved to: {filepath}")

        # Preview the first few lines
        print("\nPreview of generated content:")
        preview_lines = content.split('\n')[:10]
        print('\n'.join(preview_lines))
        print("...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()