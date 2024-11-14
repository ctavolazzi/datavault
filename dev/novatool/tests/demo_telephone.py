import subprocess
import time
import os
import sys
import psutil
import signal
from test_telephone_game import write_to_log
from novatool.core.hubs.ai_hub import AIHub
from novatool.utils.ai_config import AIService

def wait_for_hud_status(status, timeout=10):
    """Wait for specific HUD status"""
    status_file = os.path.join(os.path.dirname(__file__), 'hud_status.txt')
    start_time = time.time()

    while time.time() - start_time < timeout:
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                current_status = f.read().strip()
                if current_status == status:
                    return True
        time.sleep(0.5)
    return False

def send_status(status):
    """Send status to demo script"""
    status_file = os.path.join(os.path.dirname(__file__), 'hud_status.txt')
    with open(status_file, 'w') as f:
        f.write(status)

def is_hud_running():
    """Check if the HUD process is running"""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] in ['python', 'python3']:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'telephone_hud.py' in cmdline:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def handle_shutdown(signum, frame):
    """Handle graceful shutdown of demo and HUD"""
    print("\nShutting down demo and HUD...")

    # Find and terminate the HUD process
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' and proc.info['cmdline']:
                if 'telephone_hud.py' in ' '.join(proc.info['cmdline']):
                    proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    print("Cleanup complete")
    sys.exit(0)

def close_terminal_window(window_id):
    """Force close specific Terminal window using killall"""
    try:
        # First minimize the window for smooth transition
        applescript = f'''
            tell application "Terminal"
                set targetWindow to (every window whose id is {window_id})
                repeat with win in targetWindow
                    set miniaturized to true
                end tell
            end tell
        '''
        subprocess.run(['osascript', '-e', applescript])

        # Then force kill the process
        subprocess.run(['killall', '-9', 'Terminal'])

    except Exception as e:
        print(f"Error closing terminal: {e}")

def run_demo():
    print("Starting demo...")

    # Initialize AI Hub with Ollama as default
    hub = AIHub(service=AIService.OLLAMA)

    # Get actual AI service info from hub
    ai_info = {
        "service": hub.service.value,
        "model": hub.get_current_model(),
        "available_models": hub.available_models,
        "api_type": "Local Inference" if hub.service == AIService.OLLAMA else "API"
    }

    print("\nAI Service Configuration:")
    print("------------------------")
    print(f"Service: {ai_info['service']}")
    print(f"Model: {ai_info['model']}")
    print(f"Available Models: {', '.join(ai_info['available_models'])}")
    print(f"API Type: {ai_info['api_type']}\n")

    # Clear status file
    status_file = os.path.join(os.path.dirname(__file__), 'hud_status.txt')
    if os.path.exists(status_file):
        os.remove(status_file)

    # Start HUD
    terminal_window_id = None
    if sys.platform == 'darwin':
        script_path = os.path.join(os.path.dirname(__file__), 'telephone_hud.py')
        applescript = f'''
            tell application "Terminal"
                activate
                set newTab to do script "cd '{os.path.dirname(__file__)}' && python3 '{script_path}'"
                get the id of window 1
            end tell
        '''
        # Capture the window ID from the AppleScript output
        result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
        terminal_window_id = result.stdout.strip()
        print(f"Launched HUD terminal (window ID: {terminal_window_id})")

    # Wait for HUD to be ready
    if not wait_for_hud_status("ready", timeout=10):
        print("Error: HUD failed to start!")
        return

    print("HUD is ready! Starting demo sequence...")
    start_time = time.time()
    message_count = 0

    # Define initial message
    messages = [
        {
            "event": "startup",
            "type": "game_start",
            "timestamp": time.time(),
            "message": "Welcome to the AI Telephone Game Demo!",
            "ai_service": ai_info
        }
    ]

    # Write startup message
    write_to_log(messages[0])
    message_count += 1
    time.sleep(2)

    # Add query/response pairs
    queries = [
        "What's the meaning of life?",
        "Tell me a joke about programming!"
    ]

    for i, query in enumerate(queries, 1):
        # Add and write query message
        query_msg = {
            "event": "query",
            "message": query,
            "timestamp": time.time()
        }
        write_to_log(query_msg)
        message_count += 1
        time.sleep(2)

        # Get AI response using hub
        try:
            response = hub._call_ollama(query)
            response_msg = {
                "event": "response",
                "round": i,
                "message": response,
                "timestamp": time.time()
            }
        except Exception as e:
            print(f"Error getting AI response: {e}")
            response_msg = {
                "event": "error",
                "round": i,
                "message": f"Error: Could not get AI response - {str(e)}",
                "timestamp": time.time()
            }

        # Write response message
        write_to_log(response_msg)
        message_count += 1
        time.sleep(2)

    # Give user time to see final messages
    print("\nDemo messages complete! Closing HUD in 5 seconds...")
    print(f"Displayed {message_count} messages in {time.time() - start_time:.1f} seconds")
    time.sleep(5)

    # Signal HUD to close
    send_status("shutdown")
    time.sleep(1)  # Give HUD time to clean up

    # Close the Terminal window
    if terminal_window_id:
        close_terminal_window(terminal_window_id)
        print("Closed HUD terminal window")

    print("\nDemo complete!")

if __name__ == "__main__":
    run_demo()