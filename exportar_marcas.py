import psycopg2
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
        
        # Consulta SQL para obter as marcas
        query = """
select
	marca.nome, 
	marca.fipeid, 
	tipo_veiculo.codigo
from
	marca
inner join tipo_veiculo on
	marca.tipo_veiculo = tipo_veiculo.id
group by
	marca.nome,
	marca.fipeid,
	tipo_veiculo.codigo
order by
	marca.nome
        """
        
        # Executa a consulta
        cur.execute(query)
        resultados = cur.fetchall()
        
        # Nome do arquivo CSV
        nome_arquivo = 'marcas_fipescrapper.csv'
        
        # Escreve os resultados no arquivo CSV
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as arquivo_csv:
            # Escreve o cabeçalho
            arquivo_csv.write('descricao,fipeid,tipoveiculo\n')
            
            # Escreve os dados
            for linha in resultados:
                arquivo_csv.write(f'{linha[0]},"{linha[1]}",{linha[2]}\n')
        
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