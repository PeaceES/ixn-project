def log_message(message, log_file_path="messages_log.txt"):
    """Append a message to the log file."""
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(message + "\n")
