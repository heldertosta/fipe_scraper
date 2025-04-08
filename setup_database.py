# -*- coding: utf-8 -*-
import psycopg2
import logging
import config
from utils import setup_logging

# Configuração do logging
setup_logging(__file__)

def criar_tabelas(cur):
    """Cria as tabelas necessárias se elas não existirem"""
    try:
        # Tabela de tipo_veiculo
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tipo_veiculo (
                id SERIAL PRIMARY KEY,
                codigo INTEGER NOT NULL UNIQUE,
                descricao VARCHAR(50) NOT NULL
            )
        """)
        
        # Inserir dados iniciais na tabela tipo_veiculo
        cur.execute("""
            INSERT INTO tipo_veiculo (codigo, descricao)
            VALUES (0, 'carro'), (1, 'moto'), (2, 'caminhao')
            ON CONFLICT (codigo) DO NOTHING
        """)
        
        # Tabela de referências
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referencias (
                id SERIAL PRIMARY KEY,
                mes VARCHAR(20) NOT NULL,
                ano INTEGER NOT NULL,
                mes_ano VARCHAR(20) NOT NULL,
                UNIQUE(mes_ano)
            )
        """)
        
        # Tabela de marca
        cur.execute("""
            CREATE TABLE IF NOT EXISTS marca (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                fipeid INTEGER NOT NULL,
                tipo_veiculo INTEGER REFERENCES tipo_veiculo(id),
                referencia_id INTEGER REFERENCES referencias(id),
                UNIQUE(nome, tipo_veiculo, referencia_id),
                UNIQUE(fipeid, tipo_veiculo, referencia_id)
            )
        """)
        
        # Tabela de modelos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS modelos (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                marca_id INTEGER REFERENCES marca(id),
                referencia_id INTEGER REFERENCES referencias(id),
                UNIQUE(nome, marca_id, referencia_id)
            )
        """)
        
        # Tabela de anos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS anos (
                id SERIAL PRIMARY KEY,
                ano VARCHAR(20) NOT NULL,
                modelo_id INTEGER REFERENCES modelos(id),
                referencia_id INTEGER REFERENCES referencias(id),
                UNIQUE(ano, modelo_id, referencia_id)
            )
        """)
        
        # Tabela de valores
        cur.execute("""
            CREATE TABLE IF NOT EXISTS valores (
                id SERIAL PRIMARY KEY,
                valor VARCHAR(100) NOT NULL,
                ano_id INTEGER REFERENCES anos(id),
                referencia_id INTEGER REFERENCES referencias(id),
                UNIQUE(ano_id, referencia_id)
            )
        """)
        
        logging.info("Tabelas criadas/verificadas com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro ao criar tabelas: {e}")
        raise

def main():
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Cria as tabelas
        criar_tabelas(cur)
        
        conn.commit()
        logging.info("Setup do banco de dados concluído com sucesso!")
        
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