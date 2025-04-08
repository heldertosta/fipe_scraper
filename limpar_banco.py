import psycopg2
import logging
import config
from utils import setup_logging

# Configuração do logging
setup_logging(__file__)

def limpar_tabelas(cur):
    """Remove todas as tabelas do banco de dados"""
    try:
        # Lista de tabelas na ordem correta para remoção (respeitando as dependências)
        tabelas = [
            'valores',
            'anos',
            'modelos',
            'marcas',
            'referencias'
        ]
        
        for tabela in tabelas:
            cur.execute(f"DROP TABLE IF EXISTS {tabela} CASCADE")
            logging.info(f"Tabela {tabela} removida com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro ao remover tabelas: {e}")
        raise

def main():
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Remove as tabelas
        limpar_tabelas(cur)
        
        conn.commit()
        logging.info("Banco de dados limpo com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro durante a execução: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 