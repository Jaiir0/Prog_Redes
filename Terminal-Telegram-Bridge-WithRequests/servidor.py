import socket
import threading
import sys
import requests
import time


TOKEN = 'SEUTOKENAQUI'
URL = "https://api.telegram.org/bot" + TOKEN
telegram_users = []
telegram_users_to_ignore = set()  # para armazenar usuários a serem ignorados

all_threads = []
all_conn = []

def request_telegram():
    id_update = 0
    while True:
        try:
            response = requests.get(URL + f"/getUpdates?offset={id_update}")
            dados = response.json()
            
            for info in dados["result"]:
                chat = info["message"]["chat"]
                chat_id = chat["id"]
                
                if chat_id not in telegram_users: #caso o id de chat nao esteja salvo ainda
                    telegram_users.append(chat_id)

                usuario = info["message"]["from"]["first_name"] + " " + info["message"]["from"]["last_name"]
                mensagem_telegram = info["message"].get("text", "")

                if mensagem_telegram:
                    print(f"{usuario} enviou: {mensagem_telegram}")
                    telegram_users_to_ignore.add(chat_id)  # adciona o chat_id à lista de ignorados
                    broadCastMensage(None, None, mensagem_telegram.encode('utf-8'))

                id_update = info["update_id"] + 1
        except Exception as e:
            print(f"Erro ao obter mensagens do Telegram: {e}")
        
        time.sleep(10)  


def broadCastMensage(my_conn, my_addr, msg):
    len_msg = len(msg).to_bytes(2, 'big')
    msg = len_msg + msg
    
    for conn in all_conn:
        if conn != my_conn:  # Não manda a msg para o próprio cliente que está enviando
            try:
                conn.send(msg)
            except:
                print(f"Falha no envio para {my_addr}")
    
    # Envia para os usuários do Telegram, mas não para os que enviaram mensagens
    send_message_to_telegram(msg.decode('utf-8'))


# envia mensagens para os usuários do Telegram
def send_message_to_telegram(mensagem):
    for chat_id in telegram_users:
        if chat_id not in telegram_users_to_ignore:  # Verifica se o usuário deve ser ignorado
            try:
                params = {'chat_id': chat_id, 'text': mensagem}
                requests.get(URL + "/sendMessage", params=params)
                print(f"Enviando para Telegram ID {chat_id}): {mensagem}")
            except Exception as e:
                print(f"Erro ao enviar para Telegram ID {chat_id}): {e}")
        else:
            print()
    
    # Limpa a lista de ignorados após o envio
    telegram_users_to_ignore.clear()


def client(my_conn, my_addr):
    print(f'Novo cliente conectado: {my_addr}')
    all_conn.append(my_conn)
    prefix = f"{my_addr} digitou: ".encode('utf-8')
    
    while True:
        try:
            len_msg = my_conn.recv(2)
            if not len_msg:
                break

            len_msg = int.from_bytes(len_msg, 'big')
            msg = prefix + my_conn.recv(len_msg)
            broadCastMensage(my_conn, my_addr, msg)
        except:
            print("Falha no processamento do cliente", my_addr, "saindo.")
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

# thread do telegram
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
