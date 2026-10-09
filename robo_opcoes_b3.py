import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
import pytz
import sys

# ---------------------------------------------------------------------
# PROJETO: ROBÔ IA B3 + OPÇÕES ESTRUTURADAS (TEMPO REAL / ROBUSTO ITM)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAG0I120Ehu079dWuMX-cGkqLIjUGBgCsWU"
TELEGRAM_CHAT_ID = "@opcoes_b3_neto"

fuso_br = pytz.timezone('America/Sao_Paulo')
agora_br = datetime.now(fuso_br)
data_hoje = agora_br.strftime('%d-%m-%Y %H:%M')

acoes = [
    'ALOS3.SA', 'ALPA4.SA', 'ABEV3.SA', 'ASAI3.SA', 'B3SA3.SA', 'BBAS3.SA', 
    'BBDC3.SA', 'BBDC4.SA', 'BBSE3.SA', 'BEEF3.SA', 'BPAC11.SA', 'BRAP4.SA', 
    'BRKM5.SA', 'CMIG4.SA', 'CMIN3.SA', 'COGN3.SA', 'CPFE3.SA', 'CSAN3.SA', 
    'CSNA3.SA', 'CVCB3.SA', 'CYRE3.SA', 'DXCO3.SA', 'ENEV3.SA', 'ENGI11.SA',
    'EQTL3.SA', 'EZTC3.SA', 'FLRY3.SA', 'GGBR4.SA', 'GOAU4.SA', 'HAPV3.SA', 
    'HYPE3.SA', 'IGTI11.SA', 'IRBR3.SA', 'ITSA4.SA', 'ITUB4.SA', 'KLBN11.SA', 
    'LREN3.SA', 'LWSA3.SA', 'MGLU3.SA', 'MRVE3.SA', 'MULT3.SA', 'PCAR3.SA', 
    'PETR3.SA', 'PETR4.SA', 'RECV3.SA', 'RAIZ4.SA', 'RADL3.SA', 'RENT3.SA',
    'SANB11.SA', 'SMTO3.SA', 'SUZB3.SA', 'TAEE11.SA', 'TIMS3.SA', 'TOTS3.SA', 
    'UGPA3.SA', 'USIM5.SA', 'VALE3.SA', 'VAMO3.SA', 'VBBR3.SA', 'WEGE3.SA', 'YDUQ3.SA'
]

def calcular_opcao_teorica(ticker_acao, preco_entrada):
    letras_call = {1:'A', 2:'B', 3:'C', 4:'D', 5:'E', 6:'F', 7:'G', 8:'H', 9:'I', 10:'J', 11:'K', 12:'L'}
    mes_atual = datetime.now().month
    mes_seguinte = mes_atual + 1 if mes_atual < 12 else 1
    letra_vencimento = letras_call[mes_seguinte]
    raiz_ticker = ticker_acao.replace('.SA', '')
    
    # Calibrado a 3% de distância para garantir book cheio de formadores de mercado
    strike_alvo = preco_entrada * (1 - 0.03)
    sufixo_strike = str(int(round(strike_alvo)))
    
    ticker_opcao = f"{raiz_ticker}{letra_vencimento}{sufixo_strike}"
    return ticker_opcao, round(strike_alvo, 2)

def calcular_data_alvo_util(dias_necessarios):
    data_calc = datetime.now(fuso_br)
    dias_adicionados = 0
    while dias_adicionados < dias_necessarios:
        data_calc += timedelta(days=1)
        if data_calc.weekday() < 5:
            dias_adicionados += 1
    return data_calc.strftime('%d/%m/%Y')

def enviar_telegram(texto):
    site_base = "https://api.telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        response = requests.post(url_final, json=payload, timeout=15)
        if response.status_code == 200:
            print("📱 Relatório enviado com sucesso para o seu Telegram!", flush=True)
        else:
            print(f"❌ Erro de resposta do Telegram: {response.text}", flush=True)
    except Exception as e:
        print(f"❌ Erro de rede: {e}", flush=True)

print(f"📡 [MESA AO VIVO] Iniciando varredura em tempo real B3... {data_hoje}...")
oportunidades = []

try:
    dados_lote = yf.download(acoes, period='250d', group_by='ticker', progress=False)
    
    for ticker in acoes:
        try:
            if ticker in dados_lote.columns.get_level_values(0):
                dados = dados_lote[ticker].dropna()
            else:
                continue

            if dados.empty or len(dados) < 200: 
                continue

            dados['Media_20'] = dados['Close'].rolling(window=20).mean()
            dados['Desvio_20'] = dados['Close'].rolling(window=20).std()
            dados['Banda_Sup'] = dados['Media_20'] + (dados['Desvio_20'] * 2)
            dados['Vol_Media_20'] = dados['Volume'].rolling(window=20).mean()
            dados['Media_200'] = dados['Close'].rolling(window=200).mean()
            dados['High_Low'] = dados['High'] - dados['Low']
            dados['ATR'] = dados['High_Low'].rolling(window=14).mean()

            preco_atual = float(dados['Close'].iloc[-1])
            banda_sup_atual = float(dados['Banda_Sup'].iloc[-1])
            media_200_atual = float(dados['Media_200'].iloc[-1])
            volume_atual = float(dados['Volume'].iloc[-1])
            volume_medio = float(dados['Vol_Media_20'].iloc[-1])
            atr_atual = float(dados['ATR'].iloc[-1])

                      hora_atual = datetime.now(fuso_br).hour
            if 10 <= hora_atual < 17:
                fator_tempo = 7 / (hora_atual - 9)
                volume_projetado = volume_atual * fator_tempo
            else:
                volume_projetado = volume_atual

            # 🎯 ESTRATÉGIA REAL ATIVADA: Filtros de volatilidade, volume e tendência institucional
            if preco_atual > banda_sup_atual and volume_projetado > volume_medio and preco_atual > media_200_atual:
                stop_tecnico = preco_atual - (2 * atr_atual)
                distancia_risco = preco_atual - stop_tecnico
                alvo_tecnico = preco_atual + (3 * distancia_risco)
                
                porcentagem_stop = ((preco_atual - stop_tecnico) / preco_atual) * 100
                porcentagem_alvo = ((alvo_tecnico - preco_atual) / preco_atual) * 100
                score_volume = volume_projetado / volume_medio if volume_medio > 0 else 1.0

                # PROJEÇÃO DE TEMPO ESTIMADO BASEADO NO ATR (ESTATÍSTICA)
                distancia_ao_alvo = alvo_tecnico - preco_atual
                dias_estimados = int(np.ceil(distancia_ao_alvo / atr_atual)) if atr_atual > 0 else 5
                
                if dias_estimados < 3: dias_estimados = 3
                if dias_estimados > 10: dias_estimados = 10
                
                data_alvo_projetada = calcular_data_alvo_util(dias_estimados)
                opc_sugerida, strike_opc = calcular_opcao_teorica(ticker, preco_atual)

                # 🌐 CAPTURA E TRADUÇÃO DO NOME E SETOR EM TEMPO REAL
                try:
                    obj_ticker = yf.Ticker(ticker)
                    nome_empresa = obj_ticker.info.get('longName', ticker.replace('.SA', ''))
                    setor_en = obj_ticker.info.get('sector', 'General')
                    
                    # Dicionário de tradução ultra-leve dos setores principais da B3
                    tradutor_setores = {
                        'Financial Services': 'Financeiro / Serviços Financeiros',
                        'Financial': 'Financeiro / Bancos',
                        'Basic Materials': 'Materiais Básicos / Mineração e Siderurgia',
                        'Energy': 'Petróleo, Gás e Biocombustíveis',
                        'Utilities': 'Utilidade Pública / Energia Elétrica e Saneamento',
                        'Consumer Cyclical': 'Consumo Cíclico / Varejo e Imóveis',
                        'Consumer Defensive': 'Consumo não Cíclico / Alimentos e Bebidas',
                        'Healthcare': 'Saúde / Medicina e Medicamentos',
                        'Technology': 'Tecnologia da Informação',
                        'Communication Services': 'Telecomunicações',
                        'Industrials': 'Bens Industriais / Transporte e Máquinas'
                    }
                    setor_empresa = tradutor_setores.get(setor_en, setor_en)
                except:
                    nome_empresa = ticker.replace('.SA', '')
                    setor_empresa = 'Setor Geral B3'

                oportunidades.append({
                    'Ação': ticker.replace('.SA', ''),
                    'Nome': nome_empresa,
                    'Setor': setor_empresa,
                    'Entrada': round(preco_atual, 2),
                    'Alvo': round(alvo_tecnico, 2),
                    'Alvo_Porc': round(porcentagem_alvo, 1),
                    'Stop': round(stop_tecnico, 2),
                    'Stop_Porc': round(porcentagem_stop, 1),
                    'Vol': round(score_volume, 1),
                    'Opção_Sugerida': opc_sugerida,
                    'Strike_Sugerido': strike_opc,
                    'Data_Alvo': data_alvo_projetada,
                    'Dias_Est': dias_estimados
                })
        except:
            continue
except Exception as e:
    print(f"❌ Erro no download em lote: {e}", flush=True)
    sys.exit(1)

df_ops = pd.DataFrame(oportunidades)

if not df_ops.empty:
    df_ops = df_ops.sort_values(by='Vol', ascending=False).head(3)
    
    for index, row in df_ops.iterrows():
        msg_entrada = f"🚨 *ALERTA EM TEMPO REAL B3* 🚨\n"
        msg_entrada += f"_Rompimento com Pressão Compradora Detectado_\n\n"
        msg_entrada += f"📌 *Ação Principal:* {row['Ação']}\n"
        msg_entrada += f" • Empresa: {row['Nome']}\n"
        msg_entrada += f" • Setor: {row['Setor']}\n\n"
        msg_entrada += f"📊 *MÉTRICAS DE ENTRADA:*\n"
        msg_entrada += f" • Preço Atual: R\$ {row['Entrada']}\n"
        msg_entrada += f" • Alvo Técnico (3:1): R\$ {row['Alvo']} (+{row['Alvo_Porc']}%)\n"
        msg_entrada += f" • Stop de Proteção: R\$ {row['Stop']} (-{row['Stop_Porc']}%)\n"
        msg_entrada += f" • Projeção de Volume: {row['Vol']}x acima da média habitual\n\n"
        msg_entrada += f"📈 *ESTRUTURA EM DERIVATIVOS (OPÇÕES):*\n"
        msg_entrada += f" • CONTRATO RECOMENDADO: `{row['Opção_Sugerida']}`\n"
        msg_entrada += f" • Tipo: Opção de Compra (CALL - Estilo Robusto ITM)\n"
        msg_entrada += f" • Strike Estimado: R\$ {row['Strike_Sugerido']}\n\n"
        msg_entrada += f"⏳ *ESTIMATIVA DE CARREGAMENTO:*\n"
        msg_entrada += f" • Janela de Execução: {row['Dias_Est']} dias úteis\n"
        msg_entrada += f" • *DATA ALVO ESTIMADA: {row['Data_Alvo']}*\n\n"
        msg_entrada += f"⚠️ *Gatilho Operacional:* Verifique o book da opção no Home Broker. Confirme se há liquidez."
        
        enviar_telegram(msg_entrada)
        time.sleep(2)
else:
    print("📊 Varredura concluída: Nenhuma ação apresentou rompimento válido neste momento.", flush=True)

print("¼ Análise intradiária de opções finalizada com sucesso!", flush=True)
