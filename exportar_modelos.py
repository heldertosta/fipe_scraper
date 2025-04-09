import psycopg2
import config
import logging
from utils import setup_logging

# Configuração do logging
setup_logging(__file__)

def exportar_modelos_para_csv():
    try:
        # Conecta ao banco de dados
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Consulta SQL para obter os modelos
        query = """
        select
            marca.nome, 
            marca.fipeid as fipeid_marca,
            modelo.nome,
            modelo.fipeid as fipeid_modelo,
            tipo_veiculo.codigo
        from
            marca
        inner join tipo_veiculo on
            marca.tipo_veiculo = tipo_veiculo.id
        inner join modelo on 
            marca.id = modelo.marca_id
        group by
            marca.nome,	
            marca.fipeid,
            modelo.nome, 
            modelo.fipeid, 
            tipo_veiculo.codigo
        order by
            marca.nome, modelo.nome
        """
        
        # Executa a consulta
        cur.execute(query)
        resultados = cur.fetchall()
        
        # Nome do arquivo CSV
        nome_arquivo = 'modelos_fipescrapper.csv'
        
        # Escreve os resultados no arquivo CSV
        with open(nome_arquivo, 'w', encoding='utf-8') as arquivo_csv:
            # Escreve o cabeçalho
            arquivo_csv.write('"descricao","fipeid_marca","","fipeid_modelo","tipoveiculo"\n')
            
            # Escreve os dados
            for linha in resultados:
                marca_nome = linha[0]
                fipeid_marca = f'"{linha[1]}"'
                modelo_nome = linha[2]
                fipeid_modelo = f'"{linha[3]}"'
                tipo_veiculo = linha[4]
                
                arquivo_csv.write(f'{marca_nome},{fipeid_marca},{modelo_nome},{fipeid_modelo},{tipo_veiculo}\n')
        
        logging.info(f"Arquivo {nome_arquivo} criado com sucesso!")
        logging.info(f"Total de {len(resultados)} modelos exportados.")
        
    except Exception as e:
        logging.error(f"Erro ao exportar modelos: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    exportar_modelos_para_csv() 