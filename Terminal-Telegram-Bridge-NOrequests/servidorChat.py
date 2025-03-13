import socket
import ssl
import json
import threading
import sys
import time

TOKEN = 'SEUTOKENAQUI'
URL = "api.telegram.org"
telegram_users = []
telegram_users_to_ignore = set()

all_threads = []
all_conn = []

def request_telegram():
    id_update = 0
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=URL)
            sock.connect((URL, 443))  # HTTPS 

            request = (f"GET /bot{TOKEN}/getUpdates?offset={id_update} HTTP/1.1\r\n"
                       f"Host: {URL}\r\n"
                       "Connection: close\r\n\r\n")
            sock.send(request.encode())

            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            sock.close()

            if b"\r\n\r\n" in response: #caso não venha no formato esperado
                header, body = response.split(b"\r\n\r\n", 1) 
            else:
                print("Resposta inesperada do Telegram:", response)
                continue

            dados = json.loads(body.decode())

            for info in dados.get("result", []):
                message = info["message"]
                chat_id = message["chat"]["id"]
                if not chat_id:
                    continue

                if chat_id not in telegram_users:
                    telegram_users.append(chat_id)

                user_info = message.get("from", {})
                first_name = user_info.get("first_name", "")
                last_name = user_info.get("last_name", "")
                usuario = first_name + ' ' + last_name
                mensagem_telegram = message.get("text", "")

                if mensagem_telegram:
                    print(f"{usuario} enviou: {mensagem_telegram}")
                    formatted_msg = f"{usuario} (Telegram): {mensagem_telegram}"
                    broadCastMensage(None, "telegram", formatted_msg.encode('utf-8'))
                    telegram_users_to_ignore.add(chat_id)

                id_update = info["update_id"] + 1 #controla o id da ultima mensagem

        except Exception as e:
            print(f"Erro ao obter mensagens do Telegram: {e}")

        time.sleep(10) #verificação do telegram a cada 10s

def broadCastMensage(my_conn, my_addr, msg):

    original_msg = msg #mensagem sem tamanho para enviar ao telegram
    msg_for_clients = len(msg).to_bytes(2, 'big') + msg #mensagem com tamanho para o terminal

    for conn in all_conn:
        if conn != my_conn:
            try:
                conn.send(msg_for_clients)
            except Exception as e:
                print(f"Falha no envio para {my_addr}: {e}")

    send_message_to_telegram(original_msg.decode('utf-8'))

def send_message_to_telegram(mensagem):
    for chat_id in telegram_users:

        if chat_id not in telegram_users_to_ignore:  #tratamento para o sender nao receber a propria mensagem
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=URL)
                sock.connect((URL, 443))
                
                request = (f"GET /bot{TOKEN}/sendMessage?chat_id={chat_id}&text={mensagem} HTTP/1.1\r\n"
                           f"Host: {URL}\r\n"
                           "Connection: close\r\n\r\n")
                
                sock.send(request.encode())
                sock.close()

                print(f"Enviando para Telegram ID {chat_id}: {mensagem}")
            except Exception as e:
                print(f"Erro ao enviar para Telegram ID {chat_id}: {e}")

    telegram_users_to_ignore.clear() 

def client(my_conn, my_addr):
    print(f'Novo cliente conectado: {my_addr}')
    all_conn.append(my_conn)
    prefix = f"{my_addr} digitou: ".encode('utf-8')

    while True:
        try:
            len_msg = my_conn.recv(2)
            if not len_msg: #caso o cliente feche o terminal 
                break

            len_msg = int.from_bytes(len_msg, 'big')
            msg = prefix + my_conn.recv(len_msg)
            broadCastMensage(my_conn, my_addr, msg)
        except:
            print(f"Falha no processamento do cliente {my_addr}, saindo.")
            break

    print(f"Cliente {my_addr} desconectado.")
    all_conn.remove(my_conn)
    my_conn.close()

def startServer():
    try:
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", 8080))
        sock.listen()
        print("Aguardando conexões...")
    except OSError:
        print("Erro, endereço em uso.")
        sys.exit(2)
    return sock

# Thread do Telegram
telegram_thread = threading.Thread(target=request_telegram, daemon=True)
telegram_thread.start()

sock = startServer()

while True:
    try:
        conn, addr = sock.accept()
        t = threading.Thread(target=client, args=(conn, addr))
        all_threads.append(t)
        t.start()
    except:
        break

for t in all_threads:
    t.join()
sock.close()
