import csv
import logging
from utils import setup_logging

# Configuração do logging
setup_logging(__file__)

def carregar_modelos(arquivo):
    """Carrega os modelos de um arquivo CSV."""
    modelos = set()
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Cria uma chave única combinando marca, modelo e tipo de veículo
                chave = (row['descricao'], row[''], row['tipoveiculo'])
                modelos.add(chave)
        return modelos
    except Exception as e:
        logging.error(f"Erro ao carregar arquivo {arquivo}: {str(e)}")
        return set()

def comparar_modelos():
    try:
        # Carrega os modelos dos dois arquivos
        modelos_fipe = carregar_modelos('modelos_fipescrapper.csv')
        modelos_ojc = carregar_modelos('modelos_ojc.csv')
        
        # Encontra os modelos que estão no FIPEScraper mas não no OJC
        modelos_unicos = modelos_fipe - modelos_ojc
        
        # Nome do arquivo de saída
        nome_arquivo = 'modelos_unicos_fipe.csv'
        
        # Escreve os modelos únicos em um novo arquivo CSV
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['descricao', 'fipeid_marca', '', 'fipeid_modelo', 'tipoveiculo'])
            
            # Lê o arquivo original para obter os fipeids
            with open('modelos_fipescrapper.csv', 'r', encoding='utf-8') as original:
                reader = csv.DictReader(original)
                for row in reader:
                    chave = (row['descricao'], row[''], row['tipoveiculo'])
                    if chave in modelos_unicos:
                        writer.writerow([
                            row['descricao'],
                            row['fipeid_marca'],
                            row[''],
                            row['fipeid_modelo'],
                            row['tipoveiculo']
                        ])
        
        logging.info(f"Total de modelos no FIPEScraper: {len(modelos_fipe)}")
        logging.info(f"Total de modelos no OJC: {len(modelos_ojc)}")
        logging.info(f"Total de modelos únicos no FIPEScraper: {len(modelos_unicos)}")
        logging.info(f"Arquivo {nome_arquivo} criado com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro ao comparar modelos: {str(e)}")

if __name__ == "__main__":
    comparar_modelos() 