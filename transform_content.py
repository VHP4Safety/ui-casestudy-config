import json
import re
from html.parser import HTMLParser
from typing import List, Dict, Any

class ContentParser(HTMLParser):
    """Parse HTML content and extract sections with their headings."""
    
    def __init__(self):
        super().__init__()
        self.sections = []
        self.current_heading = None
        self.current_heading_type = None
        self.current_content = []
        self.in_heading = False
        self.preserve_tags = {'b', 'strong', 'i', 'em', 'a', 'sup', 'sub'}
        self.tag_stack = []
        
    def handle_starttag(self, tag, attrs):
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Save previous section if exists
            if self.current_heading is not None:
                self._save_section()
            
            self.current_heading_type = tag
            self.current_heading = ""
            self.in_heading = True
        elif tag in self.preserve_tags:
            # Preserve formatting tags
            attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs])
            if attrs_str:
                self.current_content.append(f'<{tag} {attrs_str}>')
            else:
                self.current_content.append(f'<{tag}>')
            self.tag_stack.append(tag)
        elif tag == 'br':
            self.current_content.append('\n')
        # For structural tags like p, ul, li, div - we ignore them but keep their content
        
    def handle_endtag(self, tag):
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.in_heading = False
        elif tag in self.preserve_tags:
            if self.tag_stack and self.tag_stack[-1] == tag:
                self.current_content.append(f'</{tag}>')
                self.tag_stack.pop()
    
    def handle_data(self, data):
        if self.in_heading:
            self.current_heading += data
        else:
            self.current_content.append(data)
    
    def _save_section(self):
        """Save the current section."""
        if self.current_heading or self.current_content:
            description = ''.join(self.current_content).strip()
            # Clean up extra whitespace and normalize line breaks
            description = re.sub(r'\n\s*\n+', '\n\n', description)
            description = re.sub(r' +', ' ', description)
            description = description.strip()
            
            self.sections.append({
                'headingType': self.current_heading_type or 'p',
                'section': self.current_heading.strip() if self.current_heading else '',
                'description': description
            })
        
        # Reset for next section
        self.current_heading = None
        self.current_heading_type = None
        self.current_content = []
    
    def parse_content(self, html_content: str) -> List[Dict[str, str]]:
        """Parse HTML content and return list of sections."""
        if not html_content or not html_content.strip():
            return []
        
        self.sections = []
        self.current_heading = None
        self.current_heading_type = None
        self.current_content = []
        self.in_heading = False
        self.tag_stack = []
        
        # Feed the HTML content
        self.feed(html_content)
        
        # Save the last section
        if self.current_heading is not None or self.current_content:
            self._save_section()
        
        return self.sections


def transform_content_fields(obj: Any, parser: ContentParser) -> Any:
    """Recursively find and transform content fields in JSON structure."""
    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            if key == 'content' and isinstance(value, str):
                # Transform the content field
                sections = parser.parse_content(value)
                new_obj[key] = sections if sections else []
            else:
                # Recursively process other fields
                new_obj[key] = transform_content_fields(value, parser)
        return new_obj
    elif isinstance(obj, list):
        return [transform_content_fields(item, parser) for item in obj]
    else:
        return obj


def transform_json_file(input_file: str, output_file: str):
    """Transform a JSON file by converting HTML content to structured sections."""
    print(f"Processing {input_file}...")
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create parser instance
    parser = ContentParser()
    
    # Transform the data
    transformed_data = transform_content_fields(data, parser)
    
    # Write the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Completed {output_file}")


if __name__ == '__main__':
    # Transform all three JSON files
    files = [
        'kidney_content.json',
        'parkinson_content.json',
        'thyroid_content.json'
    ]
    
    for file in files:
        transform_json_file(file, file)
    
    print("\nAll files transformed successfully!")
