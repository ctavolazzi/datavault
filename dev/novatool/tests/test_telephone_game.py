import json
import time
import os

def write_to_log(message_data):
    """Write a message to the telephone game log file"""
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                           "telephone_game.log")

    with open(log_path, "a") as f:
        f.write(json.dumps(message_data) + "\n")
        f.flush()

def run_test():
    """Run a sequence of test events"""
    # Clear existing log file
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                           "telephone_game.log")
    open(log_path, 'w').close()

    print("Running test sequence...")

    # Test startup
    write_to_log({
        "event": "startup",
        "type": "game_start",
        "timestamp": time.time(),
        "message": "Game is starting!"
    })
    time.sleep(2)  # Give time to see the status change

    # Test multiple queries
    for i in range(3):
        write_to_log({
            "event": "query",
            "message": f"Test query {i+1}: What is AI?",
            "timestamp": time.time()
        })
        time.sleep(1)  # Show processing state

        write_to_log({
            "event": "response",
            "round": i+1,
            "message": f"AI response {i+1}: Artificial Intelligence is fascinating!",
            "processing_time": 1.2,
            "word_count": 5,
            "timestamp": time.time()
        })
        time.sleep(2)  # Show completed state

if __name__ == "__main__":
    print("Starting test sequence...")
    run_test()
    print("Test complete!")