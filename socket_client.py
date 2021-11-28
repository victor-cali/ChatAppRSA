import socket
from threading import Thread

import rsa 
HEADER_LENGTH = 128
client_socket = None

my_public_key, my_private_key = rsa.generar_llaves()
# Connects to the server
def connect(ip, port, my_username, error_callback):

    global client_socket, my_public_key

    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to a given ip and port
        client_socket.connect((ip, port))
    except Exception as e:
        # Connection error
        error_callback('Connection error: {}'.format(str(e)))
        return False

    # Prepare username and header and send them
    # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
    username = my_username.encode('utf-8')
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(username_header + username)

    # Prepare publik key and header and send them
    # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
    public_key = repr(my_public_key).encode('utf-8')
    public_key_header = f"{len(public_key):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(public_key_header + public_key)

    return True

# Sends a message to the server
def send(message,user):
    print(f'\nMessage text: \n{message}\n')
    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    cipher = rsa.cifrar(message, user['key'])
    print(f'\nCipher text: \n{cipher}\n')
    message = (cipher + ':>>>:' +  user['user']).encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')

    client_socket.send(message_header + message)

# Starts listening function in a thread
# incoming_message_callback - callback to be called when new message arrives
# error_callback - callback to be called on error
def start_listening(incoming_message_callback, error_callback):
    Thread(target=listen, args=(incoming_message_callback, error_callback), daemon=True).start()
    

# Listens for incomming messages
def listen(incoming_message_callback, error_callback):
    global my_private_key
    while True:

        try:
            # Now we want to loop over received messages (there might be more than one) and print them
            while True:
                
                # Receive our "header" containing username length, it's size is defined and constant
                new_header = client_socket.recv(HEADER_LENGTH)
                
                # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                if not len(new_header):
                    error_callback('Connection closed by the server')

                # Convert header to int value
                username_length = int(new_header.decode('utf-8').strip())

                # Receive and decode username
                username = client_socket.recv(username_length).decode('utf-8')
                
                # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                message_header = client_socket.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                
                if username != '__flag__':
                    cipher = client_socket.recv(message_length).decode('utf-8')
                    print(f'\nCipher text: \n{cipher}\n')
                    message = rsa.descifrar(cipher, my_private_key)
                    print(f'\nDeciphered text: \n{message}\n')
                else: 
                    message = client_socket.recv(message_length).decode('utf-8')

                # Print message
                
                incoming_message_callback(username, message)

        except Exception as e:
            # Any other exception - something happened, exit
            error_callback('Reading error: {}'.format(str(e)))