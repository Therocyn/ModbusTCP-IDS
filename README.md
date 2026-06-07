# ModbusTCP IDS

Repositório integrante do Trabalho de Conclusão de Curso (TCC) em Engenharia de Controle e Automação pela Universidade Federal do Rio Grande do Sul (UFRGS).

Este projeto apresenta um protótipo de Sistema de Detecção de Intrusão (IDS) não-invasivo projetado especificamente para atuar sobre o protocolo Modbus TCP em redes de Automação Industrial (OT). O sistema analisa o tráfego de rede de forma passiva através de escuta de interface (*sniffing*), operando de forma transparente e sem inserir atrasos ou latência no ciclo crítico de controle (*polling* nominal de 80ms), priorizando o princípio de segurança física (*Safety*) conforme preconizado pelas diretrizes ISA/IEC 62443.

## 🏗️ Arquitetura e Estrutura de Arquivos

A solução é composta pelos seguintes artefatos principais, cobrindo o *testbed* de controle (OT) e o sistema de monitoramento/auditoria (IT):

* **`sniffer_ids_v7.py`**: Motor principal do IDS desenvolvido em Python. Utiliza a biblioteca Scapy para captura assíncrona de pacotes e possui um motor de Inspeção Profunda de Pacotes (DPI) na Camada de Aplicação.
* **`pentest_ics.py`**: Script de auditoria de segurança (ferramenta ofensiva) customizado com suporte a três vetores de ataque distintos para validação das regras do IDS.
* **`flowsTCC_v4.json`**: Fluxo estruturado para importação no Node-RED (*Dashboard* SOC). Gerencia os gráficos, *gauges* de vazão e tabelas históricas de alarmes via protocolo MQTT.
* **`code_tcc_rev3.ACD`**: Arquivo binário de projeto para o Rockwell Studio 5000, contendo a lógica *ladder* e a temporização do cliente Modbus TCP embarcado no CLP CompactLogix.
* **`flexfact_code_tcc_rev3.ffs`**: Arquivo de *layout* e configuração da planta industrial simulada no software FlexFact (atuando como o servidor Modbus TCP).

## ✨ Regras de Detecção Implementadas

1. **Regra 1 - Anomalia Volumétrica (DoS):** Monitoramento contínuo de vazão por meio de um algoritmo de Janela Deslizante (*Sliding Window*) de 1 segundo. Rajadas contínuas com taxa igual ou superior a `40.0 pkt/s` disparam alarmes de criticidade ALTA de Negação de Serviço.
2. **Regra 2 - Controle de Acesso (IP Whitelist):** Filtro estrito de pacotes com base nos endereços IP de origem autorizados no ecossistema industrial para envio de comandos de alteração de estado.
3. **Regra 3 - Inspeção Profunda de Pacotes (DPI):** Validação semântica do cabeçalho Modbus TCP (Camada 7). Monitora e restringe a execução de *Function Codes* (FC) na rede. Comandos de escrita (como FC 15) são validados contra a identidade física do emissor, enquanto tentativas de injeção usando códigos anômalos ou ataques de *IP Spoofing* são bloqueadas e reportadas imediatamente.

## 🚀 Como Executar

### 1. Pré-requisitos
* **Python 3.8 ou superior** instalado no sistema.
* Bibliotecas Python necessárias:
  ```bash
  pip install scapy paho-mqtt pymodbus
* **Ambiente Windows:** Instalação obrigatória do driver **Npcap** (com a opção de compatibilidade WinPcap ativada) para permitir que o Scapy acesse as interfaces de rede físicas ou virtuais.
* **Infraestrutura de Monitoramento:** Instância ativa do Node-RED e acesso a um *Broker* MQTT público ou privado (configurado nativamente para o endereço `broker.hivemq.com` na porta `1883`).

### 2. Inicialização do Ambiente de Testes
1. Importe o arquivo `flowsTCC_v4.json` no seu Node-RED e faça o *Deploy* do *Dashboard*.
2. Inicie a planta no FlexFact utilizando o arquivo `flexfact_code_tcc_rev3.ffs`.
3. Inicie a rotina do CLP no Studio 5000 (`code_tcc_rev3.ACD`).
4. Em um terminal aberto com privilégios de **Administrador**, execute o IDS:
   ```bash
   python sniffer_ids_v7.py

### 3. Execução dos Testes de Intrusão (Auditoria)
Para testar violações nas regras implementadas, execute o script `pentest_ics.py` com privilégios de administrador. É necessário configurar previamente a variável `TIPO_ATAQUE` no cabeçalho do código-fonte para um dos seguintes valores:

* **`1`**: Ataque Volumétrico de Negação de Serviço (DoS) via inundação de requisições.
* **`2`**: Ataque Semântico através da injeção direta de comandos não autorizados.
* **`3`**: Ataque de Falsificação de Identidade (*IP Spoofing*) utilizando injeção direta de *frames* via Scapy.

Execute a ferramenta de auditoria utilizando o comando:
```bash
python pentest_ics.py
