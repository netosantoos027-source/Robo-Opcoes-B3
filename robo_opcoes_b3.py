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
data_hoje = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M')

# Lista de ações principais e atualizadas da B3
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

# 🏛️ DICIONÁRIO INTEGRADO DE EMPRESAS E SETORES DA B3
info_empresas = {
    'ALOS3': {'nome': 'Allos', 'setor': 'Consumo Cíclico / Imóveis'},
    'ALPA4': {'nome': 'Alpargatas', 'setor': 'Consumo Cíclico / Calçados'},
    'ABEV3': {'nome': 'Ambev', 'setor': 'Consumo não Cíclico / Bebidas'},
    'ASAI3': {'nome': 'Assaí Atacadista', 'setor': 'Consumo não Cíclico / Alimentos'},
    'B3SA3': {'nome': 'B3 S.A.', 'setor': 'Financeiro / Serviços Financeiros'},
    'BBAS3': {'nome': 'Banco do Brasil', 'setor': 'Financeiro / Intermediários Financeiros'},
    'BBDC3': {'nome': 'Banco Bradesco (ON)', 'setor': 'Financeiro / Intermediários Financeiros'},
    'BBDC4': {'nome': 'Banco Bradesco (PN)', 'setor': 'Financeiro / Intermediários Financeiros'},
    'BBSE3': {'nome': 'BB Seguridade', 'setor': 'Financeiro / Previdência e Seguros'},
    'BEEF3': {'nome': 'Minerva Foods', 'setor': 'Consumo não Cíclico / Alimentos'},
    'BPAC11': {'nome': 'BTG Pactual', 'setor': 'Financeiro / Intermediários Financeiros'},
    'BRAP4': {'nome': 'Bradespar', 'setor': 'Materiais Básicos / Mineração'},
    'BRKM5': {'nome': 'Braskem', 'setor': 'Materiais Básicos / Químicos'},
    'CMIG4': {'nome': 'Cemig', 'setor': 'Utilidade Pública / Energia Elétrica'},
    'CMIN3': {'nome': 'CSN Mineração', 'setor': 'Materiais Básicos / Mineração'},
    'COGN3': {'nome': 'Cogna Educação', 'setor': 'Consumo Cíclico / Ensino'},
    'CPFE3': {'nome': 'CPFL Energia', 'setor': 'Utilidade Pública / Energia Elétrica'},
    'CSAN3': {'nome': 'Cosan', 'setor': 'Petróleo, Gás e Biocombustíveis'},
    'CSNA3': {'nome': 'Siderúrgica Nacional', 'setor': 'Materiais Básicos / Siderurgia'},
    'CVCB3': {'nome': 'CVC Viagens', 'setor': 'Consumo Cíclico / Viagens e Lazer'},
    'CYRE3': {'nome': 'Cyrela', 'setor': 'Consumo Cíclico / Incorporações'},
    'DXCO3': {'nome': 'Dexco', 'setor': 'Materiais Básicos / Madeira e Papel'},
    'ENEV3': {'nome': 'Eneva', 'setor': 'Utilidade Pública / Energia Elétrica'},
    'ENGI11': {'nome': 'Energisa', 'setor': 'Utilidade Pública / Energia Elétrica'},
    'EQTL3': {'nome': 'Equatorial Energia', 'setor': 'Utilidade Pública / Energia Elétrica'},
    'EZTC3': {'nome': 'EZTEC', 'setor': 'Consumo Cíclico / Incorporações'},
    'FLRY3': {'nome': 'Fleury', 'setor': 'Saúde / Medicina Diagnóstica'},
    'GGBR4': {'nome': 'Gerdau', 'setor': 'Materiais Básicos / Siderurgia'},
    'GOAU4': {'nome': 'Metalúrgica Gerdau', 'setor': 'Materiais Básicos / Siderurgia'},
    'HAPV3': {'nome': 'Hapvida', 'setor': 'Saúde / Planos de Saúde'},
    'HYPE3': {'nome': 'Hypera Pharma', 'setor': 'Saúde / Medicamentos'},
    'IGTI11': {'nome': 'Iguatemi', 'setor': 'Consumo Cíclico / Imóveis'},
    'IRBR3': {'nome': 'IRB Brasil RE', 'setor': 'Financeiro / Seguros'},
    'ITSA4': {'nome': 'Itaúsa', 'setor': 'Financeiro / Holdings Financeiras'},
    'ITUB4': {'nome': 'Itaú Unibanco', 'setor': 'Financeiro / Intermediários Financeiros'},
    'KLBN11': {'nome': 'Klabin', 'setor': 'Materiais Básicos / Papel e Celulose'},
    'LREN3': {'nome': 'Lojas Renner', 'setor': 'Consumo Cíclico / Tecidos e Vestuário'},
    'LWSA3': {'nome': 'Locaweb', 'setor': 'Tecnologia da Informação / Programas'},
    'MGLU3': {'nome': 'Magazine Luiza', 'setor': 'Consumo Cíclico / Eletrodomésticos'},
    'MRVE3': {'nome': 'MRV Engenharia', 'setor': 'Consumo Cíclico / Incorporações'},
    'MULT3': {'nome': 'Multiplan', 'setor': 'Consumo Cíclico / Imóveis'},
    'PCAR3': {'nome': 'Pão de Açúcar', 'setor': 'Consumo não Cíclico / Alimentos'},
    'PETR3': {'nome': 'Petrobras (ON)', 'setor': 'Petróleo, Gás e Biocombustíveis'},
    'PETR4': {'nome': 'Petrobras (PN)', 'setor': 'Petróleo, Gás e Biocombustíveis'},
    'RECV3': {'nome': 'PetroReconcavo', 'setor': 'Petróleo, Gás e Biocombustíveis'},
    'RAIZ4': {'nome': 'Raízen', 'setor': 'Petróleo, Gás e Biocombustíveis'},
    'RADL3': {'nome': 'RaiaDrogasil', 'setor': 'Saúde / Comércio e Distribuição'},
    'RENT3': {'nome': 'Localiza', 'setor': 'Consumo Cíclico / Aluguel de Carros'},
    'SANB11': {'nome': 'Banco Santander', 'setor': 'Financeiro / Intermediários Financeiros'},
    'SMTO3': {'nome': 'São Martinho', 'setor': 'Consumo não Cíclico / Agricultura'},
    'SUZB3': {'nome': 'Suzano', 'setor': 'Materiais Básicos / Papel e Celulose'},
    'TAEE11': {'nome': 'Taesa', 'setor': 'Utilidade Pública / Energia Elétrica'},
    'TIMS3': {'nome': 'TIM Brasil', 'setor': 'Telecomunicações'},
    'TOTS3': {'nome': 'Totvs', 'setor': 'Tecnologia da Informação / Programas'},
    'UGPA3': {'nome': 'Ultrapar', 'setor': 'Petróleo, Gás e Biocombustíveis'},
    'USIM5': {'nome': 'Usiminas', 'setor': 'Materiais Básicos / Siderurgia'},
    'VALE3': {'nome': 'Vale', 'setor': 'Materiais Básicos / Mineração'},
    'VAMO3': {'nome': 'Vamos', 'setor': 'Bens Industriais / Transporte'},
    'VBBR3': {'nome': 'Vibra Energia', 'setor': 'Petróleo, Gás e Biocombustíveis'},
    'WEGE3': {'nome': 'WEG', 'setor': 'Bens Industriais / Máquinas e Motores'},
    'YDUQ3': {'nome': 'Yduqs', 'setor': 'Consumo Cíclico / Ensino'}
}

def calcular_opcao_teorica(ticker_acao, preco_entrada):
    letras_call = {1:'A', 2:'B', 3:'C', 4:'D', 5:'E', 6:'F', 7:'G', 8:'H', 9:'I', 10:'J', 11:'K', 12:'L'}
    mes_atual = datetime.now().month
    mes_seguinte = mes_atual + 1 if mes_atual < 12 else 1
    letra_vencimento = letras_call[mes_seguinte]
    raiz_ticker = ticker_acao.replace('.SA', '')
    
    # Modelo Calibrado: Strike posicionado a 3% ITM para liquidez estável
    strike_alvo = preco_entrada * (1 - 0.03)
    sufixo_strike = str(int(round(strike_alvo)))
    
    ticker_opcao = f"{raiz_ticker}{letra_vencimento}{sufixo_strike}"
    return ticker_opcao, round(strike_alvo, 2)

def calcular_data_alvo_util(dias_necessarios):
    data_calc = datetime.now(fuso_br)
    dias_adicionados = 0
    while dias_adicionados < dias_necessarios:
        data_calc += timedelta(days=1)
        if data_calc.weekday() < 5:  # Considera apenas Segunda a Sexta-feira
            dias_adicionados += 1
    return data_calc.strftime('%d/%m/%Y')

def enviar_telegram(texto):
    site_base = "https://" + "api.telegram.org"
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

            # 🎯 ESTRATÉGIA REAL ATIVADA: Filtros de volatilidade, volume e tendência macro
