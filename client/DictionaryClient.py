# DictionaryClient.py
import json
import socket
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk


class DictionaryClient:
    def __init__(self, server_address, server_port):
        """Initialize the dictionary client"""
        self.server_address = server_address
        self.server_port = server_port
        self.socket = None
        self.connected = False

        # Create GUI
        self.root = tk.Tk()
        self.root.title("Dictionary Client")
        self.root.geometry("600x400")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()
        self.connect_to_server()

    def create_widgets(self):
        """Create GUI widgets"""
        # Top frame for connection status
        status_frame = tk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(status_frame, text="Server:").pack(side=tk.LEFT)
        self.status_label = tk.Label(status_frame, text="Connecting...", fg="orange")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Frame for word lookup
        lookup_frame = tk.Frame(self.root)
        lookup_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(lookup_frame, text="Word:").pack(side=tk.LEFT)
        self.word_entry = tk.Entry(lookup_frame, width=30)
        self.word_entry.pack(side=tk.LEFT, padx=5)
        self.word_entry.bind("<Return>", self.lookup_word)

        self.lookup_button = tk.Button(
            lookup_frame, text="Lookup", command=self.lookup_word
        )
        self.lookup_button.pack(side=tk.LEFT, padx=5)

        # Result area
        result_frame = tk.Frame(self.root)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(result_frame, text="Definition:").pack(anchor=tk.W)

        self.result_text = scrolledtext.ScrolledText(
            result_frame, wrap=tk.WORD, width=60, height=15
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.config(state=tk.DISABLED)

        # Status bar
        self.status_bar = tk.Label(
            self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def connect_to_server(self):
        """Connect to the dictionary server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_address, self.server_port))
            self.connected = True
            self.status_label.config(
                text=f"Connected to {self.server_address}:{self.server_port}",
                fg="green",
            )
            self.status_bar.config(text="Connected to server")
        except ConnectionRefusedError:
            self.status_label.config(text="Connection refused", fg="red")
            self.status_bar.config(text="Unable to connect to server")
            messagebox.showerror(
                "Connection Error",
                f"Could not connect to {self.server_address}:{self.server_port}",
            )
            self.connected = False
        except socket.gaierror:
            self.status_label.config(text="Invalid address", fg="red")
            self.status_bar.config(text="Invalid server address")
            messagebox.showerror(
                "Connection Error", f"Invalid address: {self.server_address}"
            )
            self.connected = False
        except Exception as e:
            self.status_label.config(text="Connection error", fg="red")
            self.status_bar.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
            self.connected = False

    def lookup_word(self, event=None):
        """Look up a word in the dictionary"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Not connected to server")
            return

        word = self.word_entry.get().strip()
        if not word:
            return

        self.status_bar.config(text=f"Looking up '{word}'...")

        # Prepare request
        request = {"action": "lookup", "word": word}

        try:
            # Send request
            self.socket.sendall(json.dumps(request).encode("utf-8"))

            # Receive response
            data = self.socket.recv(4096)
            response = json.loads(data.decode("utf-8"))

            # Update result area
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)

            if response.get("status") == "success":
                self.result_text.insert(tk.END, f"Word: {response.get('word')}\n\n")

                for i, meaning in enumerate(response.get("meanings", []), 1):
                    self.result_text.insert(tk.END, f"{i}. {meaning}\n")

                self.status_bar.config(text=f"Found definition for '{word}'")
            else:
                self.result_text.insert(
                    tk.END, response.get("message", "Unknown error")
                )
                self.status_bar.config(text=response.get("message", "Error occurred"))

            self.result_text.config(state=tk.DISABLED)

        except ConnectionError:
            self.connected = False
            self.status_label.config(text="Disconnected", fg="red")
            self.status_bar.config(text="Connection lost")
            messagebox.showerror("Connection Error", "Connection to server lost")
        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.socket and self.connected:
                try:
                    self.socket.close()
                except:
                    pass
            self.root.destroy()

    def run(self):
        """Run the client application"""
        self.root.mainloop()


def main():
    """Main function to start the client"""
    if len(sys.argv) != 3:
        print("Usage: python DictionaryClient.py <server-address> <server-port>")
        sys.exit(1)

    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])

        client = DictionaryClient(server_address, server_port)
        client.run()
    except ValueError:
        print("Error: Port must be a number")
        sys.exit(1)


if __name__ == "__main__":
    main()
