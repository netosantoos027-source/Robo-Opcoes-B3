import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import pytz
import sys

# ---------------------------------------------------------------------
# PROJETO: ROBÔ IA B3 + OPÇÕES ESTRUTURADAS (ROBUSTO ITM)
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8977957095:AAFGcSuzjKxb2uX0lQzWwaozFdrreZ9myjc"
TELEGRAM_CHAT_ID = "@robo_over_05_ht"

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
    
    # Filtro Robusto: Strike estruturado ~6% dentro do dinheiro (ITM)
    strike_alvo = preco_entrada * (1 - 0.06)
    sufixo_strike = str(int(round(strike_alvo)))
    
    ticker_opcao = f"{raiz_ticker}{letra_vencimento}{sufixo_strike}"
    return ticker_opcao, round(strike_alvo, 2)

def enviar_telegram(texto):
    site_base = "https://telegram.org"
    pasta_bot = "/bot" + TELEGRAM_TOKEN
    acao_envio = "/sendMessage"
    url_final = site_base + pasta_bot + acao_envio
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try: 
        requests.post(url_final, json=payload, timeout=8)
        print("📱 Notificação enviada para o canal com sucesso!", flush=True)
    except: 
        print("❌ Falha de comunicação com a API do Telegram.", flush=True)

print(f"📡 [MESA DERIVATIVOS] Iniciando varredura automatizada B3... {data_hoje}", flush=True)
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

            if preco_atual > banda_sup_atual and volume_atual > volume_medio and preco_atual > media_200_atual:
                stop_tecnico = preco_atual - (2 * atr_atual)
                distancia_risco = preco_atual - stop_tecnico
                alvo_tecnico = preco_atual + (3 * distancia_risco)
                
                porcentagem_stop = ((preco_atual - stop_tecnico) / preco_atual) * 100
                porcentagem_alvo = ((alvo_tecnico - preco_atual) / preco_atual) * 100
                score_volume = volume_atual / volume_medio if volume_medio > 0 else 1.0

                opc_sugerida, strike_opc = calcular_opcao_teorica(ticker, preco_atual)

                oportunidades.append({
                    'Ação': ticker.replace('.SA', ''),
                    'Entrada': round(preco_atual, 2),
                    'Alvo': round(alvo_tecnico, 2),
                    'Alvo_Porc': round(porcentagem_alvo, 1),
                    'Stop': round(stop_tecnico, 2),
                    'Stop_Porc': round(porcentagem_stop, 1),
                    'Vol': round(score_volume, 1),
                    'Opção_Sugerida': opc_sugerida,
                    'Strike_Sugerido': strike_opc
                })
        except:
            continue
            
except Exception as e:
    print(f"❌ Falha crítica no processamento de lote: {e}", flush=True)
    sys.exit(1)

df_ops = pd.DataFrame(oportunidades)

if not df_ops.empty:
    df_ops = df_ops.sort_values(by='Vol', ascending=False).head(3)
    for index, row in df_ops.iterrows():
        msg_entrada = f"🚨 *ALERTA DE ENTRADA B3* 🚨\n"
        msg_entrada += f"_Rompimento de Volatilidade + Tendência de Alta_\n\n"
        msg_entrada += f"📌 *Ação Principal:* {row['Ação']}\n"
        msg_entrada += f" • Preço de Entrada: R\\$ {row['Entrada']}\n"
        msg_entrada += f" • Alvo Técnico (3:1): R\\$ {row['Alvo']} (+{row['Alvo_Porc']}%)\n"
        msg_entrada += f" • Stop de Proteção: R\\$ {row['Stop']} (-{row['Stop_Porc']}%)\n"
        msg_entrada += f" • Pressão Compradora: {row['Vol']}x acima do normal\n\n"
        msg_entrada += f"📈 *ESTRUTURA EM DERIVATIVOS (OPÇÕES):*\n"
        msg_entrada += f" • CONTRATO RECOMENDADO: `{row['Opção_Sugerida']}`\n"
        msg_entrada += f" • Tipo: Opção de Compra (CALL - Estilo Robusto ITM)\n"
        msg_entrada += f" • Strike Estimado Próximo: R\\$ {row['Strike_Sugerido']}\n\n"
        msg_entrada += f"⚠️ *Gatilho Operacional:* Executar entrada se o prêmio do contrato estiver líquido e com spread reduzido no Home Broker."
        
        enviar_telegram(msg_entrada)
else:
    print("📊 Varredura B3 concluída: Nenhuma ação atendeu aos critérios operacionais hoje.", flush=True)

print("✅ Processo de análise de opções finalizado com sucesso!", flush=True)
