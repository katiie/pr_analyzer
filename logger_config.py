import logging
import sys
import os

# Configure logging once at module import
log_file = os.path.join(os.path.dirname(__file__), "mcp_server.log")

logging.basicConfig(
    level=logging.INFO,
    format='{asctime} - {name} - {levelname} - {message}',
    style='{',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)

# Create a logger function for convenience
def get_logger(name):
    return logging.getLogger(name)
