import csv
import logging
from utils import setup_logging
from datetime import datetime

# Configuração do logging
setup_logging(__file__)

def comparar_marcas_inverso():
    try:
        # Lê o arquivo marcas_ojc.csv
        marcas_ojc = set()
        with open('marcas_ojc.csv', 'r', encoding='utf-8') as arquivo_ojc:
            reader = csv.reader(arquivo_ojc)
            next(reader)  # Pula o cabeçalho
            for linha in reader:
                nome_marca = linha[0].strip().upper()  # Nome da marca
                fipeid = linha[1].strip('"')  # FipeID (remove aspas)
                codigo_tipo = linha[2].strip()  # Código do tipo de veículo
                # Cria uma tupla única para cada marca
                marca = (nome_marca, fipeid, codigo_tipo)
                marcas_ojc.add(marca)
                logging.debug(f"OJC - Marca: {nome_marca}, FipeID: {fipeid}, Tipo: {codigo_tipo}")
        
        # Lê o arquivo marcas_fipescrapper.csv
        marcas_fipe = set()
        with open('marcas_fipescrapper.csv', 'r', encoding='utf-8') as arquivo_fipe:
            reader = csv.reader(arquivo_fipe)
            next(reader)  # Pula o cabeçalho
            for linha in reader:
                nome_marca = linha[0].strip().upper()  # Nome da marca
                fipeid = linha[1].strip('"')  # FipeID (remove aspas)
                codigo_tipo = linha[2].strip()  # Código do tipo de veículo
                # Cria uma tupla única para cada marca
                marca = (nome_marca, fipeid, codigo_tipo)
                marcas_fipe.add(marca)
                logging.debug(f"FIPE - Marca: {nome_marca}, FipeID: {fipeid}, Tipo: {codigo_tipo}")
        
        # Encontra as marcas que estão apenas no arquivo marcas_ojc.csv
        marcas_apenas_ojc = marcas_ojc - marcas_fipe
        
        # Gera o nome do arquivo com o mês e ano atual
        data_atual = datetime.now()
        nome_arquivo = f'marcas_apenas_ojc_{data_atual.month:02d}{data_atual.year}.csv'
        
        # Escreve as marcas no arquivo CSV
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as arquivo_csv:
            writer = csv.writer(arquivo_csv)
            writer.writerow(['descricao', 'fipeid', 'tipoveiculo'])
            for marca in sorted(marcas_apenas_ojc):
                nome, fipeid, codigo_tipo = marca
                writer.writerow([nome, f'"{fipeid}"', codigo_tipo])
        
        logging.info(f"Total de marcas no arquivo marcas_ojc.csv: {len(marcas_ojc)}")
        logging.info(f"Total de marcas no arquivo marcas_fipescrapper.csv: {len(marcas_fipe)}")
        logging.info(f"Total de marcas apenas em marcas_ojc.csv: {len(marcas_apenas_ojc)}")
        logging.info(f"Arquivo {nome_arquivo} criado com sucesso!")
        
        # Log das marcas que estão apenas no arquivo OJC
        logging.info("Marcas que estão apenas no arquivo OJC:")
        for marca in sorted(marcas_apenas_ojc):
            nome, fipeid, codigo_tipo = marca
            logging.info(f"- {nome} (FipeID: {fipeid}, Tipo: {codigo_tipo})")
        
    except Exception as e:
        logging.error(f"Erro ao comparar os arquivos: {str(e)}")

if __name__ == "__main__":
    comparar_marcas_inverso() 