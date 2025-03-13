import socket
import threading
import sys

host = 'localhost'
porta = 8080

def userMessages():
    while True:
        try:
            msg = input("> ")
            if msg:
                len_msg =  len(msg.encode('utf-8')).to_bytes(2, 'big') #2 bytes do tamanho 
                msg = len_msg + msg.encode("utf-8")
                tcp_sock.sendall(msg)
        except Exception as e:
            print("Fechamento do input() ou servidor.\nFechando conexão com o servidor")
            tcp_sock.close()
            break
 
def serverMessages():
    while True:
        try:
            len_msg = int.from_bytes(tcp_sock.recv(2),'big')
            bytes_msg = tcp_sock.recv(len_msg) #recebe a string da msg
            msg = bytes_msg.decode("utf-8")
            if msg:
                print(f"Recebido: {msg}\n> ")
        except Exception as e:
            print(f"Conexão fechada pelo servidor.")
            break
    
def startClient():
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((host, porta))
    except Exception as e:
        print ("Falha na conexão ao servidor.")
        sys.exit(2)
    return tcp_sock


tcp_sock = startClient()
thread_user = threading.Thread(target=userMessages) # Threads das funções
thread_server = threading.Thread(target=serverMessages)

print(f"Conectado em: {host, porta}")

try: 
    thread_user.start()
    thread_server.start()

    thread_user.join()
    thread_server.join()
except KeyboardInterrupt as e:
    print ("Finalizando por Cntl-C.") 
