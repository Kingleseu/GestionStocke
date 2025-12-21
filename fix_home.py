import os

file_path = r"c:\Users\ebenn\Pictures\GestionStocke\store\templates\store\home.html"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The target string with newline and specific indentation
    # I'll look for the split tag and join it
    
    # Pattern seems to be: "{% for category in" followed by newline and spaces and "filter_categories"
    
    new_content = content.replace(
        "{% for category in\n                                filter_categories|default:categories|default:filter_categories_fallback %}",
        "{% for category in filter_categories|default:categories|default:filter_categories_fallback %}"
    )

    if content == new_content:
        # Try finding with flexible whitespace if exact match failed
        import re
        pattern = r"\{%\s+for\s+category\s+in\s*\n\s+filter_categories\|default:categories\|default:filter_categories_fallback\s+%\}"
        replacement = "{% for category in filter_categories|default:categories|default:filter_categories_fallback %}"
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            print(f"Fixed {count} usage(s) using regex.")
        else:
            print("Target string not found (even with regex). Content unchanged.")
            # Print the area for debugging
            start_idx = content.find("get_active_categories as filter_categories_fallback")
            if start_idx != -1:
                print("Context around line 722:")
                print(content[start_idx:start_idx+200])
    
    else:
        print("Fixed usage using direct replace.")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("File written successfully.")

except Exception as e:
    print(f"Error: {e}")
