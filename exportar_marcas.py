import psycopg2
import csv
import config
import logging
from utils import setup_logging

# Configuração do logging
setup_logging(__file__)

def exportar_marcas_para_csv():
    try:
        # Conecta ao banco de dados
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Consulta SQL para obter as marcas com referencia_id = 1
        query = """
        SELECT 
            m.nome,
            m.fipeid::text,            
            tv.codigo as codigo_tipo_veiculo
        FROM marca m
        JOIN tipo_veiculo tv ON m.tipo_veiculo = tv.id
        WHERE m.referencia_id = 1
        ORDER BY m.nome, m.fipeid
        """
        
        # Executa a consulta
        cur.execute(query)
        resultados = cur.fetchall()
        
        # Nome do arquivo CSV
        nome_arquivo = 'marcas_fipescrapper.csv'
        
        # Escreve os resultados no arquivo CSV
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as arquivo_csv:
            writer = csv.writer(arquivo_csv)
            
            # Escreve o cabeçalho
            writer.writerow(['descricao', 'fipeid', 'tipoveiculo'])
            
            # Escreve os dados
            for linha in resultados:
                writer.writerow(linha)
        
        logging.info(f"Arquivo {nome_arquivo} criado com sucesso!")
        logging.info(f"Total de {len(resultados)} marcas exportadas.")
        
    except Exception as e:
        logging.error(f"Erro ao exportar marcas: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    exportar_marcas_para_csv() 