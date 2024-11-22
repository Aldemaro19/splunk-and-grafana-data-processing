import json
from typing import Any

# Save the combined HTML content to a file for preview
def save_html_to_file(filename: str, content: str) -> None:
    with open(filename, 'w') as file:
        file.write(content)

# Load JSON data from files
def load_json(filename: str) -> Any:
    with open(filename, 'r') as file:
        return json.load(file)