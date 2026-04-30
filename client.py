
import socket

# Exact prompts accepted by the assignment
VALID_QUERIES = [
    "What is the average moisture inside our kitchen fridges in the past hours, week and month?",
    "What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?",
    "Which house consumed more electricity in the past 24 hours, and by how much?"
]

def send_query(server_ip, server_port, query):
    # Open a TCP connection, send request, print reply
    client_socket = None
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        client_socket.send(query.encode())
        response = client_socket.recv(4096).decode()
        print("\n[SERVER RESPONSE]:", response)
    except Exception as e:
        print("Connection error:", e)
    finally:
        if client_socket:
            client_socket.close()

def main():
    # Ask user where the server is hosted
    server_ip = input("Enter Server IP Address: ").strip()
    server_port = 5000

    print("\nDistributed IoT Query Client")

    while True:
        user_input = input("\nEnter query (or exit): ").strip()
        if user_input.lower() == "exit":
            break

        # Only allow approved assignment queries
        if user_input in VALID_QUERIES:
            send_query(server_ip, server_port, user_input)
        else:
            print("Unsupported query. Try one of the listed options.")

if __name__ == "__main__":
    main()
