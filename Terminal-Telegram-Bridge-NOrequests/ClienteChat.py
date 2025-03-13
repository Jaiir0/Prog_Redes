import socket
import threading

host = '127.0.0.1'
porta = 8080

tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSock.connect((host, porta))

def enviar_mensagem():
    while True:
        try:
            mensagem = input("> ")
            len_msg =  len(mensagem.encode('utf-8')).to_bytes(2, 'big') #2 bytes do tamanho
            mensagem_completa = len_msg + mensagem.encode("utf-8")
            tcpSock.sendall(mensagem_completa)

        except KeyboardInterrupt:
            print("Parando programa.")
            tcpSock.close()

def receber_mensagem():
    while True:
        try:
            tam_msg = tcpSock.recv(2)  # Recebe os 2 primeiros bytes do tamanho
            if not tam_msg:
                break

            len_msg = int.from_bytes(tam_msg,'big')
            bytes_msg = tcpSock.recv(len_msg) #recebe a string da mensagem
            mensagem =  bytes_msg.decode("utf-8")
            print(f"Recebido: {mensagem}")

        except Exception as e:
            print(f"Erro ao receber mensagem: {e}")
            break

thread_enviarMsg = threading.Thread(target=enviar_mensagem) # Threads das funções
thread_receberMsg = threading.Thread(target=receber_mensagem)

print(f"Conectado em: {host, porta}")

thread_enviarMsg.start()
thread_receberMsg.start()
