from pymodbus.client import ModbusTcpClient
import time

# Conecta ao FlexFact (Servidor/Slave) no localhost, porta 1502
client = ModbusTcpClient('127.0.0.1', port=1502)

if client.connect():
    print("Conectado ao FlexFact com sucesso!")
else:
    print("Falha na conexão. Verifique se o FlexFact está rodando.")
    exit()

try:
    print("Iniciando ciclo de Scan do CLP (Alternando a cada 3s)...")
    
    # True  = Endereço 3 ligado, 4 desligado
    # False = Endereço 3 desligado, 4 ligado
    estado_atual = True 

    while True:
        # 1. Lê o estado dos sensores (Inputs)
        resultado_leitura = client.read_coils(address=0, count=23, device_id=1)
        
        if not resultado_leitura.isError():
            print(f"Sensores lidos: {resultado_leitura.bits[:23]}")
        
        # 2. Lógica de Controle (Escreve nos atuadores)
        if estado_atual:
            # Joga True no 3 e Falso no 4
            client.write_coil(address=3, value=True, device_id=1)
            client.write_coil(address=4, value=False, device_id=1)
            print("Atuadores: [Endereço 3: ON] | [Endereço 4: OFF]")
        else:
            # Joga Falso no 3 e True no 4
            client.write_coil(address=3, value=False, device_id=1)
            client.write_coil(address=4, value=True, device_id=1)
            print("Atuadores: [Endereço 3: OFF] | [Endereço 4: ON]")

        # 3. Inverte o estado para a próxima rodada
        # Se era True, vira False. Se era False, vira True.
        estado_atual = not estado_atual

        # 4. Pausa de 3 segundos para simular o tempo entre as ações
        time.sleep(3)

except KeyboardInterrupt:
    print("\nEncerrando cliente CLP...")
finally:
    client.close()