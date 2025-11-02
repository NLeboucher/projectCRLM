#!/usr/bin/env python3
import subprocess

claude_cli_path = '/home/nico/.local/bin/claude'
prompt = "Hello, what is 2+2?"

print("Testing Claude CLI with subprocess...")
print(f"Prompt: {prompt}\n")

try:
    result = subprocess.run(
        [claude_cli_path, '-p'],
        input=prompt,
        capture_output=True,
        text=True,
        check=True,
        timeout=30
    )
    print("SUCCESS!")
    print(f"Output: {result.stdout.strip()}")
    print(f"Stderr: {result.stderr}")
except subprocess.CalledProcessError as e:
    print(f"ERROR: CalledProcessError")
    print(f"Return code: {e.returncode}")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")
except subprocess.TimeoutExpired:
    print("ERROR: Timeout")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
