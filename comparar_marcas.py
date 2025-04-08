import csv
import logging
from utils import setup_logging
from datetime import datetime

# Configuração do logging
setup_logging(__file__)

def comparar_marcas():
    try:
        # Lê o arquivo marcas_fipescrapper.csv
        marcas_fipe = {}
        with open('marcas_fipescrapper.csv', 'r', encoding='utf-8') as arquivo_fipe:
            reader = csv.reader(arquivo_fipe)
            next(reader)  # Pula o cabeçalho
            for linha in reader:
                nome_marca = linha[0].strip().upper()  # Nome da marca
                fipeid = linha[1]  # FipeID
                codigo_tipo = linha[2]  # Código do tipo de veículo
                marcas_fipe[nome_marca] = (fipeid, codigo_tipo)
        
        # Lê o arquivo marcas_ojc.csv
        marcas_ojc = set()
        with open('marcas_ojc.csv', 'r', encoding='utf-8') as arquivo_ojc:
            reader = csv.reader(arquivo_ojc)
            next(reader)  # Pula o cabeçalho
            for linha in reader:
                nome_marca = linha[0].strip().upper()  # Nome da marca
                marcas_ojc.add(nome_marca)
        
        # Encontra as marcas que estão apenas no arquivo marcas_fipescrapper.csv
        marcas_apenas_fipe = set(marcas_fipe.keys()) - marcas_ojc
        
        # Gera o nome do arquivo com o mês e ano atual
        data_atual = datetime.now()
        nome_arquivo = f'carga_fipe_marcas_{data_atual.month:02d}{data_atual.year}.sql'
        
        # Escreve os inserts no arquivo SQL
        with open(nome_arquivo, 'w', encoding='utf-8') as arquivo_sql:
            for marca in sorted(marcas_apenas_fipe):
                fipeid, codigo_tipo = marcas_fipe[marca]
                insert = f"INSERT INTO marca (descricao, fipeid, tipoveiculo) VALUES ('{marca}', '{fipeid}', {codigo_tipo});\n"
                arquivo_sql.write(insert)
        
        logging.info(f"Total de marcas no arquivo marcas_fipescrapper.csv: {len(marcas_fipe)}")
        logging.info(f"Total de marcas no arquivo marcas_ojc.csv: {len(marcas_ojc)}")
        logging.info(f"Total de marcas para inserir: {len(marcas_apenas_fipe)}")
        logging.info(f"Arquivo {nome_arquivo} criado com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro ao comparar os arquivos: {str(e)}")

if __name__ == "__main__":
    comparar_marcas() 