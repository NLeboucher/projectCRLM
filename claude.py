import subprocess
import argparse
import sys

def query_claude(user_message):
    """
    Query Claude using the locally installed Claude Code CLI.
    
    Args:
        user_message (str): The message to send to Claude
    
    Returns:
        str: Claude's response
    """
    try:
        # Use the local claude CLI
        result = subprocess.run(
            ['claude', user_message],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error calling Claude CLI: {e.stderr}")
    except FileNotFoundError:
        raise Exception("Claude CLI not found. Please ensure Claude Code is installed.")

def main():
    """Main function to run the query script with command-line arguments."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Query Claude using local Claude Code CLI')
    parser.add_argument('-p', '--prompt', type=str, help='Prompt to send to Claude')
    
    args = parser.parse_args()
    
    # If prompt is provided via command line, use single-query mode
    if args.prompt:
        try:
            print("Querying Claude...\n")
            response = query_claude(args.prompt)
            print("Claude's Response:")
            print("-" * 50)
            print(response)
            print("-" * 50)
        except Exception as e:
            print(f"Error querying Claude: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Otherwise, run interactive mode
    print("Claude AI Query Script (using local Claude Code CLI)")
    print("=" * 50)
    print("Press Ctrl+C to exit\n")
    
    try:
        while True:
            # Get user input
            user_input = input("Enter your question for Claude: ").strip()
            
            if not user_input:
                print("Please enter a valid question.\n")
                continue
            
            print("\nQuerying Claude...\n")
            
            try:
                # Query Claude
                response = query_claude(user_input)
                
                # Display response
                print("Claude's Response:")
                print("-" * 50)
                print(response)
                print("-" * 50 + "\n")
                
            except Exception as e:
                print(f"Error querying Claude: {e}\n", file=sys.stderr)
    
    except KeyboardInterrupt:
        print("\n\nExiting. Goodbye!")

if __name__ == "__main__":
    main()
