# DictionaryServer.py
import json
import socket
import sys
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DictionaryServer")


class DictionaryServer:
    def __init__(self, port, dictionary_file, max_workers=5):
        """Initialize the dictionary server with port and dictionary file"""
        self.port = port
        self.dictionary_file = dictionary_file
        self.dictionary = defaultdict(list)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.socket = None
        self.load_dictionary()

    def load_dictionary(self):
        """Load dictionary data from file"""
        try:
            with open(self.dictionary_file, "r", encoding="utf-8") as file:
                logger.info(f"Loading dictionary from {self.dictionary_file}")
                for line in file:
                    # Assuming format: word:meaning
                    if ":" in line:
                        word, meaning = line.strip().split(":", 1)
                        word = word.strip().lower()
                        meaning = meaning.strip()
                        self.dictionary[word].append(meaning)
                logger.info(
                    f"Dictionary loaded successfully with {len(self.dictionary)} words"
                )
        except FileNotFoundError:
            logger.error(f"Dictionary file {self.dictionary_file} not found")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading dictionary: {str(e)}")
            sys.exit(1)

    def lookup_word(self, word):
        """Look up a word in the dictionary"""
        word = word.lower()
        if word in self.dictionary:
            return {
                "status": "success",
                "word": word,
                "meanings": self.dictionary[word],
            }
        else:
            return {
                "status": "error",
                "message": f"Word '{word}' not found in dictionary",
            }

    def handle_client(self, client_socket, addr):
        """Handle client connection in a worker thread"""
        logger.info(f"New connection from {addr}")

        try:
            while True:
                # Receive data from client
                data = client_socket.recv(4096)
                if not data:
                    break

                try:
                    # Parse the JSON request
                    request = json.loads(data.decode("utf-8"))

                    if request.get("action") == "lookup":
                        word = request.get("word", "")
                        result = self.lookup_word(word)
                    else:
                        result = {"status": "error", "message": "Invalid action"}

                    # Send response back to client
                    client_socket.sendall(json.dumps(result).encode("utf-8"))

                except json.JSONDecodeError:
                    # Handle invalid JSON
                    error_response = {
                        "status": "error",
                        "message": "Invalid request format",
                    }
                    client_socket.sendall(json.dumps(error_response).encode("utf-8"))

        except ConnectionError:
            logger.info(f"Client {addr} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {addr}: {str(e)}")
        finally:
            client_socket.close()
            logger.info(f"Connection closed with {addr}")

    def start(self):
        """Start the dictionary server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.listen(5)

            logger.info(f"Dictionary Server started on port {self.port}")
            logger.info(f"Worker pool size: {self.max_workers}")

            try:
                while True:
                    client_socket, addr = self.socket.accept()
                    # Submit client handling to the thread pool
                    self.executor.submit(self.handle_client, client_socket, addr)
            except KeyboardInterrupt:
                logger.info("Server shutdown requested")
            finally:
                self.shutdown()

        except OSError as e:
            logger.error(f"Socket error: {str(e)}")
            sys.exit(1)

    def shutdown(self):
        """Shutdown the server gracefully"""
        logger.info("Shutting down server...")
        if self.socket:
            self.socket.close()
        self.executor.shutdown(wait=False)
        logger.info("Server shutdown complete")


def main():
    """Main function to start the server"""
    if len(sys.argv) != 3:
        print("Usage: python DictionaryServer.py <port> <dictionary-file>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        dictionary_file = sys.argv[2]

        server = DictionaryServer(port, dictionary_file)
        server.start()
    except ValueError:
        print("Error: Port must be a number")
        sys.exit(1)


if __name__ == "__main__":
    main()
