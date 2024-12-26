
def encode():
    fd = open('pedepano.jpeg','rb')
    dados = fd.read()
    print(dados)
    pos = 0
    fd.close()
    lista = []

    if len(dados) % 3 == 2:
        dados = dados + b'\00'
        
    if len(dados) % 3 == 1:
        dados = dados + b'\00\00'

    tabela = {"0":"A","1":"B","2":"C","3":"D","4":"E","5":"F","6":"G","7":"H","8":"I","9":"J","10":"K","11":"L","12":"M","13":"N","14":"O","15":"P",
            "16":"Q","17":"R","18":"S","19":"T","20":"U","21":"V","22":"W","23":"X","24":"Y","25":"Z","26":"a","27":"b","28":"c","29":"d","30":"e","31":"f",
            "32":"g","33":"h","34":"i","35":"j","36":"k","37":"l","38":"m","39":"n","40":"o","41":"p","42":"q","43":"r","44":"s","45":"t","46":"u","47":"v",
            "48":"w","49":"x","50":"y","51":"z","52":"0","53":"1","54":"2","55":"3","56":"4","57":"5","58":"6","59":"7","60":"8","61":"9","62":"+","63":"/",}
            

    while pos < len(dados):
        bites = int.from_bytes(dados[pos:pos+3],'big')
        b1 =  (bites >> 18)&63
        b2 =  (bites >> 12)&63
        b3 =  (bites >> 6)&63
        b4 = (bites >> 0)&63
        pos += 3

        lista.extend([tabela[str(b1)], tabela[str(b2)], tabela[str(b3)], tabela[str(b4)]])
        
        with open('arquivoencode','w') as file:
            for letra in lista:
                file.write(letra)

import struct

def decode():
    with open('arquivoencode','r') as arq:
        fdin = arq.read()
        
    pos = 0
    listadecode = []
    
    base = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

    for letra in fdin:
        if letra in base:
            listadecode.append(f'{base.index(letra):06b}') #pega a posição que esta o caractere na tabela e transforma em binario
    listadecode = ''.join(listadecode) #junta todos os numeros dos binarios
    
    
    listabytes = []
    while pos < len(listadecode) :
        listabytes.append(int(listadecode[pos:pos+8],2)) #o 2 apos a virgula para indicar que é base 2
        pos += 8
        
    listabytes = bytes(listabytes) #conerte os inteiros para bytes(nao usei bytearray porque ficava aparecendo 'bitearray()' no print)    
    
    with open('arquviodecode','w')as arqD:
        arqD.write(str(listabytes))
    
decode()
encode()

