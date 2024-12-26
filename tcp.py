import struct
from datetime import datetime

try:
    filename = input('Digite o nome do arquvio tcpdump que deseja analisar: ')
    fd = open (filename, "rb")
except FileNotFoundError:
    print('Arquivo não encontrado. ')

try:
    #lê o cabeçalho do arquivo
    cabeçalho = fd.read(24)
    magn = struct.unpack('<I5I',cabeçalho)[0] #separa o numero mágico
    magH = f'0x{magn:x}'

    #descobre se sao nano segundos ou micro de acordo com o número mágico
    tipotempo = 'MicroSegundos' if magH == '0xa1b2c3d4' else 'NanoSegundos'

    #lê o formato do pacote 
    packetHeader = fd.read(16)
    

    maior = 0
    count = 0
    lista_IPS = []
    listaTCP = []
    listaUDP = []
    ips_distintos = []
    pacotes_nao_salvos = 0

    while packetHeader != b'':
        TSsec,TSmicro,captamanho,tamanhoOrig = struct.unpack('<IIII',packetHeader) #separa os dados
        tempo = datetime.fromtimestamp(TSsec)   #armazena a data
        packet = fd.read(captamanho) 
        count += 1 
       
        if packet[12:14] == b'\x08\x00': # se o pacote for IP
            
            ipPacket = packet[14:] 

            versao = ipPacket[0] >> 4 #separaçao da versão eliminando o byte da direta
            tam_cabeçalho = (ipPacket[0] & ((1<<4) - 1))*4 #separaçao do tamanho do cabeçalho, multiplica por 4 porque sao 5 unidades de 4 bytes
            
            Tos = ipPacket[1] #pega o tos no 2 byte
            comprimento_pacote = struct.unpack('!H', ipPacket[2:4])[0] 
            
            identificaçao = ipPacket[4:6] #16 bites para identificação
            junçao_id = (identificaçao[0]<< 8) | identificaçao[1] #calculo para juntar 2 bytes em um valor(desloca 8 bites para encaixar o segundo byte ao primeiro)
            
            flag_offset = ipPacket[6:8]
            flag_offset = int.from_bytes(flag_offset,'big') #transforma os bytes de flag e offset em inteiro

            flag = flag_offset >> 13 #separa os 3 primeiros bites para flag
            offset = flag_offset & ((1<<3) - 1) #separa os 13 bites restantes para offset
            
            if flag == 2:   #se os 3 bites for 010 flag é DF
                flag = 'DF'
            elif flag == 1:   #se os bites for 001 flag é MF
                flag = 'MF'
            else:
                flag = 'RSV' #se for 0 
            

            ttl = ipPacket[8] #tempo de vida 

            protocolo = ipPacket[9] #identifica o numero do protocolo e atribui o nome a ele
            if protocolo == 6:
                string_protocolo = 'TCP' 
            elif protocolo == 1:
                string_protocolo = 'ICMP'
            elif protocolo == 17:
                string_protocolo = 'UDP'
            elif protocolo == 2:
                string_protocolo = 'IGMP'
            elif protocolo == 41:
                string_protocolo = 'ENCAP'
            elif protocolo == 89:
                string_protocolo = 'OSPF'
            elif protocolo == 200:
                string_protocolo = 'SCTP'    
            else:
                string_protocolo = 'Protocolo não Identificado'
            
            if protocolo == 6: 
                listaTCP.append(comprimento_pacote) #adiciona o tamanho do pacote tcp á um lista
                
            if protocolo == 17: #lista de tamanho dos pacotes UDP
                listaUDP.append(comprimento_pacote) 

            checksum = struct.unpack('!H',ipPacket[10:12])[0] #o indice 0 para tirar a virgula e os parenteses

            ipOrigem = [str(ipPacket[i]) for i in range(12, 16)]
            ipDestino = [str(ipPacket[i]) for i in range(16, 20)]
            ipOrigem = ".".join(ipOrigem)
            ipDestino = ".".join(ipDestino)

            lista_IPS.append(f'{ipOrigem} e {ipDestino}' ) #lista de todos os pares de IPS
            
            if captamanho < tamanhoOrig: #se o pacote capturado for menor que o capote original é porque houve alguma perda
                pacotes_nao_salvos += 1
            
            ips_distintos.append(ipDestino) 
            ips_distintos.append(ipOrigem)

            if count == 1:
                incio_captura_dados = tempo #armazena o momento do inicio da captura de pacotes
            
            #abaixo um print parecido como o tcpdump mostra
            print (f"{count}  {tempo}.{TSmicro} {tipotempo} IP {ipOrigem} > {ipDestino}: proto {string_protocolo} ({protocolo}) Versão[{versao}], IHL:{tam_cabeçalho} Bytes, cksum {f'0x{checksum:x}'}, ToS {Tos}, Flags [{flag}], Offset {offset}, ttl {ttl}, ID {junçao_id}, Comprimento {comprimento_pacote}, playload {comprimento_pacote-40}") 
            print('-='*50)

            
            packetHeader = fd.read(16) #pega um novo cabeçalho

        else: #se o pacote for ARP

            arppacket = packet[14:] #ignora os 13 primeiros bytes =  endDest,endOrig,compPDU e pega os dados
            Htype,protoType,hlen,plen,arpoperation = struct.unpack('>HHBBH',arppacket[:8]) # separação 2,2,1,1,2 bytes dos 8 primeiros bytes

            procoloString = 'Ethernet' if (f"{protoType:x}") == '800' else 'Protocolo não Identificado' #se o protocolo for 0x0800 significa que é ethernet
            
            macOrigem = ":".join([(f"{arppacket[i]:X}") for i in range(8, 14)]) #separação de cada byte no encapsulamento do arp, conversão de decimal para hexa nos MAC
            edOrigem = ".".join([str(arppacket[i]) for i in range(14, 18)]) 
            macDestino = ":".join([(f"{arppacket[i]:X}") for i in range(18, 24)])
            edDst = ".".join([str(arppacket[i]) for i in range(24, 28)]) 
            
            if count == 1:
                incio_captura_dados = tempo

            ips_distintos.append(edOrigem) 
            ips_distintos.append(edDst)

            brodcast = '(Brodcast)' if macDestino == 'FF:FF:FF:FF:FF:FF' else '' #se o mac de destino tiver ff quer dizer que é um brodcast
            
            if arpoperation == 1: #nomeia o ti
                arpoperation = 'request'
            elif arpoperation == 2:
                arpoperation = 'reply'

            #print no formato do tcpdump 
            print(f"{count}  {tempo}.{TSmicro} {tipotempo}. ARP, {procoloString} MacOrigem {macOrigem},{brodcast} {arpoperation} who has {edDst} tell {edOrigem} Hlen {hlen} Plen {plen}")
            print('-='*50)
            packetHeader = fd.read(16)
    fd.close()

    
    fim_captura_dados = tempo #armazena o tempo da ultima captura de pacotes

    interaçao_ips = len(set(ips_distintos)) - 1 # pega todos os ip diferentes e retira o ip da interface capturada
    ip_interface = max(set(ips_distintos),key=ips_distintos.count) #pega o elemento mais frenquente na lista de ips

    #max= maior valor set para tornar cada valor unico e count para atribuir o maior valor ao item mais frequente
    print(f'• Os pares de IP que mais se repetem são: {max(set(lista_IPS),key=lista_IPS.count)}')
    print(f'• A captura de dados teve incio em {incio_captura_dados} e terminou em {fim_captura_dados}')
    print(f'• O maior pacote TCP capturado foi: {max(listaTCP)} Bytes')
    print(f'• O tamanho médio dos pacotes UDP foram: {(sum(listaUDP)) // len(listaUDP)} Bytes')
    print(f'• Houve {pacotes_nao_salvos} pacotes não foram salvos ')
    print(f'• O ip {ip_interface} interagiu com {interaçao_ips} ips diferentes')

except NameError:
    None
except KeyboardInterrupt:
    print('\n Interrupção detectada, parando programa.')
except EOFError:
    print("Erro inesperado. ")
    #2024-nov-05--cap01.pcap
