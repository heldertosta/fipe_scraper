import logging
import psycopg2
from scraper import FipeScraper
from config import DB_CONFIG
from utils import setup_logging

# Configuração do logging
setup_logging(__file__)

def get_db_connection():
    """Estabelece conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        raise

def get_primeira_marca(cur, tipo_veiculo, referencia_id):
    """Obtém a primeira marca para o tipo de veículo e referência especificados."""
    cur.execute("""
        SELECT id, nome 
        FROM marcas 
        WHERE tipo_veiculo = %s AND referencia_id = %s 
        ORDER BY id 
        LIMIT 1
    """, (tipo_veiculo, referencia_id))
    return cur.fetchone()

def get_primeira_referencia(cur):
    """Obtém a primeira referência do banco de dados."""
    cur.execute("""
        SELECT id, mes_ano 
        FROM referencias 
        ORDER BY id 
        LIMIT 1
    """)
    return cur.fetchone()

def main():
    scraper = None
    conn = None
    cur = None
    
    try:
        logger.info("Iniciando teste de extração de modelos...")
        
        # Conecta ao banco de dados
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Obtém a primeira referência
        referencia = get_primeira_referencia(cur)
        if not referencia:
            logger.error("Nenhuma referência encontrada no banco de dados")
            return
        
        referencia_id, mes_ano = referencia
        logger.info(f"Referência selecionada: {mes_ano} (ID: {referencia_id})")
        
        # Obtém a primeira marca para carros
        marca = get_primeira_marca(cur, 'carro', referencia_id)
        if not marca:
            logger.error(f"Nenhuma marca encontrada para a referência {mes_ano}")
            return
        
        marca_id, marca_nome = marca
        logger.info(f"Marca selecionada: {marca_nome} (ID: {marca_id})")
        
        # Inicializa o scraper
        scraper = FipeScraper()
        
        # Acessa a página inicial
        logger.info("Acessando a página da FIPE...")
        scraper.driver.get("https://veiculos.fipe.org.br/")
        
        # Seleciona o tipo de veículo (carro)
        logger.info("Selecionando tipo de veículo 'carro'...")
        if not scraper.selecionar_tipo_veiculo('carro'):
            logger.error("Falha ao selecionar tipo de veículo. Encerrando execução.")
            return
        
        # Seleciona a referência
        logger.info(f"Selecionando referência: {mes_ano}...")
        if not scraper.selecionar_referencia(mes_ano):
            logger.error("Falha ao selecionar referência. Encerrando execução.")
            return
        
        # Seleciona a marca
        logger.info(f"Selecionando marca: {marca_nome}...")
        if not scraper.selecionar_marca(marca_nome):
            logger.error("Falha ao selecionar marca. Encerrando execução.")
            return
        
        # Extrai os modelos
        logger.info("Extraindo modelos...")
        modelos = scraper.get_modelos()
        
        if not modelos:
            logger.error("Nenhum modelo encontrado. Encerrando execução.")
            return
            
        logger.info(f"Encontrados {len(modelos)} modelos para a marca {marca_nome}")
        for modelo in modelos:
            logger.info(f"Modelo: {modelo}")
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")
    finally:
        if scraper:
            scraper.fechar()
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 