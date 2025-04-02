import psycopg2
import logging
import config

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inserir_referencias_2025.log'),
        logging.StreamHandler()
    ]
)

def inserir_referencias(cur):
    """Insere as referências de 2025 no banco de dados"""
    try:
        # Lista de meses disponíveis em 2025
        meses = [
            'janeiro',
            'fevereiro',
            'março',
            'abril'
        ]
        
        for mes in meses:
            mes_ano = f"{mes}/2025"
            cur.execute(
                "INSERT INTO referencias (mes, ano, mes_ano) VALUES (%s, %s, %s)",
                (mes, 2025, mes_ano)
            )
            logging.info(f"Referência {mes_ano} inserida com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro ao inserir referências: {e}")
        raise

def main():
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Insere as referências
        inserir_referencias(cur)
        
        conn.commit()
        logging.info("Referências de 2025 inseridas com sucesso!")
        
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