# ModbusTCP IDS

Repositório integrante do Trabalho de Conclusão de Curso (TCC) em Engenharia de Controle e Automação, com foco em Segurança Cibernética Industrial (OT).

Este projeto apresenta um protótipo de Sistema de Detecção de Intrusão (IDS) não-invasivo projetado para atuar sobre o protocolo Modbus TCP. O sistema analisa o tráfego de rede passivamente, sem inserir latência no ciclo de controle crítico (*polling* de 80ms), priorizando a disponibilidade e a segurança física (*Safety*), em conformidade com as diretrizes da norma ISA/IEC 62443.

## 🏗️ Arquitetura e Estrutura de Arquivos

A solução é composta pelos seguintes arquivos, divididos entre os domínios de Controle (OT) e Monitoramento (IT):

* **`sniffer_ids_v7.py`**: Motor principal do IDS desenvolvido em Python. Utiliza a biblioteca Scapy para captura em tempo real e Inspeção Profunda de Pacotes (DPI).
* **`pentest_ics.py`**: Script de auditoria (ferramenta ofensiva) utilizado para validar o IDS. É capaz de gerar ataques de Negação de Serviço (DoS), IP Spoofing e Injeção Semântica (FDI).
* **`flowsTCC_v4.json`**: Fluxo exportado do Node-RED contendo o *Dashboard* (SOC). Responsável por assinar o broker MQTT e exibir as métricas de rede e alertas de intrusão graficamente.
* **`code_tcc_rev3.ACD`**: Arquivo de projeto do Rockwell Studio 5000 contendo a lógica *ladder* de controle do CLP CompactLogix (Cliente Modbus).
* **`flexfact_code_tcc_rev3.ffs`**: Arquivo de configuração da planta industrial simulada no software FlexFact (Servidor Modbus).

## ✨ Regras de Detecção Implementadas

1. **Anomalia Volumétrica (DoS):** Utiliza um algoritmo de Janela Deslizante (*Sliding Window*) de 1 segundo para medir a vazão determinística. Rajadas acima do *baseline* (calibrado empiricamente para suportar variações nominais) disparam alertas críticos imediatos.
2. **Controle de Acesso (IP Whitelist):** Bloqueio semântico de comandos enviados por endereços IP não autorizados.
3. **Inspeção Profunda de Pacotes (DPI):** Análise do *Function Code* (FC) na Camada de Aplicação. Bloqueia códigos anômalos e tentativas de *IP Spoofing*, aceitando estritamente os comandos vitais para a operação do processo (ex: FC 15 e FC 02).

## 🚀 Como Executar

### 1. Pré-requisitos
* **Python 3.8+** com as bibliotecas: `scapy`, `paho-mqtt`, `pymodbus`.
* **Captura de Rede:** Npcap instalado (caso utilize Windows).
* **Monitoramento:** Node-RED instalado e acesso a um broker MQTT (ex: `broker.hivemq.com`).

### 2. Inicialização
1. Importe o arquivo `flowsTCC_v4.json` no seu Node-RED e faça o *deploy* do Dashboard.
2. Inicie a planta no FlexFact utilizando o arquivo `flexfact_code_tcc_rev3.ffs`.
3. Inicie a rotina do CLP no Studio 5000 (`code_tcc_rev3.ACD`).
4. Em um terminal com privilégios de administrador, execute o IDS:
   ```bash
   python sniffer_ids_v7.py
