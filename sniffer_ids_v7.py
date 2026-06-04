import sys
import time
import json
import paho.mqtt.client as mqtt
from collections import deque
from scapy.all import AsyncSniffer, TCP, IP, conf

# ==============================================================================
# CONFIGURAÇÕES DA REDE E AUTO-DISCOVERY DE INTERFACES
# ==============================================================================
PORTA_ALVO = 1502
IP_FISICO = "192.168.0.10"
IP_LOOPBACK = "127.0.0.1"

def obter_nomes_interfaces_por_ip(ips_alvo):
    ifaces_selecionadas = []
    for iface_name, iface_data in conf.ifaces.items():
        ip_iface = getattr(iface_data, 'ip', '')
        if ip_iface in ips_alvo:
            ifaces_selecionadas.append(iface_data.name)
    return ifaces_selecionadas

INTERFACE_REDE = obter_nomes_interfaces_por_ip([IP_FISICO, IP_LOOPBACK])

if not INTERFACE_REDE:
    print("[X] ERRO CRÍTICO: Nenhuma interface encontrada com os IPs alvo.")
    sys.exit(1)

# ==============================================================================
# CONFIGURAÇÕES DO BASELINE E MQTT
# ==============================================================================
BROKER_MQTT = "broker.hivemq.com"
PORTA_MQTT = 1883
TOPICO_ALERTA = "ufrgs/tcc/vitor/ids/alertas"
TOPICO_VAZAO  = "ufrgs/tcc/vitor/ids/vazao"

LIMIAR_DOS = 25.0   
JANELA_TEMPO = 1.0 
INTERVALO_TELEMETRIA = 1.0 

historico_pacotes = deque()
ultimo_envio_vazao = 0.0   

print("[*] A estabelecer conexão ao Broker MQTT (HiveMQ)...")

try:
    cliente_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    cliente_mqtt = mqtt.Client()

try:
    cliente_mqtt.connect(BROKER_MQTT, PORTA_MQTT, 60)
    cliente_mqtt.loop_start()
    print("[V] Conexão MQTT estabelecida com sucesso!")
except Exception as e:
    print(f"[X] Erro ao conectar ao MQTT: {e}")
    sys.exit(1)

def publicar_alerta(tipo, ip, gravidade, detalhes=""):
    dados_alerta = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tipo_alerta": tipo,
        "ip_origem": ip,
        "gravidade": gravidade,
        "detalhes": detalhes
    }
    cliente_mqtt.publish(TOPICO_ALERTA, json.dumps(dados_alerta))
    print(f"    [>] Alerta MQTT publicado: {tipo} ({gravidade})")

def analisador_de_pacotes(pacote):
    global historico_pacotes, ultimo_envio_vazao
    
    if pacote.haslayer(TCP) and pacote[TCP].dport == PORTA_ALVO:
        if pacote.haslayer('Raw') and len(pacote['Raw'].load) >= 8:
            agora = time.time()
            payload_bytes = pacote['Raw'].load
            function_code = payload_bytes[7]
            ip_origem = pacote[IP].src
            hora_str = time.strftime("%H:%M:%S")

            # ---------------------------------------------------------
            # 1. CÁLCULO DA TAXA E TELEMETRIA (THROTTLING)
            # ---------------------------------------------------------
            while historico_pacotes and historico_pacotes[0] < agora - JANELA_TEMPO:
                historico_pacotes.popleft()
            
            historico_pacotes.append(agora)
            taxa_atual = round(len(historico_pacotes) / JANELA_TEMPO, 2)

            if (agora - ultimo_envio_vazao) >= INTERVALO_TELEMETRIA:
                cliente_mqtt.publish(TOPICO_VAZAO, taxa_atual)
                ultimo_envio_vazao = agora

            if taxa_atual >= LIMIAR_DOS:
                if len(historico_pacotes) == int(LIMIAR_DOS * JANELA_TEMPO): 
                    print(f"[!] ANOMALIA VOLUMÉTRICA! Taxa: {taxa_atual} pkt/s de {ip_origem}")
                    publicar_alerta("Ataque de Negação de Serviço (DoS)", ip_origem, "CRÍTICA", f"Vazão de pkt/s excedeu a tolerância de {LIMIAR_DOS}")

            # ---------------------------------------------------------
            # 2. INSPEÇÃO PROFUNDA DE PACOTES (DPI)
            # ---------------------------------------------------------
            if function_code in [5, 6, 15, 16]:
                if function_code == 15 and ip_origem == "192.168.0.50":
                    pass 
                else:
                    print(f"[*] [{hora_str}] Tráfego DPI: {ip_origem} | Function: {function_code}")
                    print(f"    [!] ALERTA CRÍTICO: Tentativa de ESCRITA detectada (FC {function_code})!")
                    publicar_alerta("Injeção Semântica (Escrita)", ip_origem, "ALTA", f"Function Code bloqueado: {function_code}")

if __name__ == "__main__":
    print("\n=======================================================")
    print("Sistema de Detecção de Anomalias ICS (DPI + Sliding Window)")
    print(f"Interfaces resolvidas via Auto-Discovery:")
    for i, iface in enumerate(INTERFACE_REDE):
        print(f"  [{i+1}] {iface}")
    print("=======================================================\n")

    # Cria um sniffer independente para cada interface
    lista_sniffers = []
    for interface in INTERFACE_REDE:
        try:
            sniffer = AsyncSniffer(
                iface=interface, 
                filter=f"tcp dst port {PORTA_ALVO}", 
                prn=analisador_de_pacotes, 
                store=False
            )
            sniffer.start()
            lista_sniffers.append(sniffer)
            print(f"[+] Escuta iniciada na interface: {interface}")
        except Exception as e:
            print(f"[X] Falha ao iniciar escuta na interface {interface}: {e}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Sinal de interrupção recebido. A encerrar ligações...")
        # Encerra todos os sniffers paralelos
        for s in lista_sniffers:
            s.stop() 
        cliente_mqtt.loop_stop()
        cliente_mqtt.disconnect()
        print("[V] Sistema encerrado de forma segura.")
        sys.exit(0)