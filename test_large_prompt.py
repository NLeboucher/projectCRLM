#!/usr/bin/env python3
import subprocess
import os

claude_cli_path = '/home/nico/.local/bin/claude'

# Read the actual prompt template
prompt_path = os.path.join('addons/contracts_management', 'extract_prompt.md')

with open(prompt_path, 'r', encoding='utf-8') as f:
    prompt_template = f.read()

# Simulate what the code does - replace placeholder
test_content = "This is test contract content with [FIELD1] and [FIELD2]"
full_prompt = prompt_template.replace('[INSERT RAW TEXT FROM TEMPLATE HERE]', test_content)

print(f"Prompt length: {len(full_prompt)} characters")
print(f"First 200 chars: {full_prompt[:200]}")
print(f"Last 200 chars: {full_prompt[-200:]}")
print("\nTesting with Claude CLI...")

try:
    result = subprocess.run(
        [claude_cli_path, '-p'],
        input=full_prompt,
        capture_output=True,
        text=True,
        check=True,
        timeout=30
    )
    print("SUCCESS!")
    print(f"Output length: {len(result.stdout)}")
    print(f"Output preview: {result.stdout[:500]}")
except subprocess.CalledProcessError as e:
    print(f"ERROR: CalledProcessError")
    print(f"Return code: {e.returncode}")
    print(f"Signal: {-e.returncode if e.returncode < 0 else 'N/A'}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
