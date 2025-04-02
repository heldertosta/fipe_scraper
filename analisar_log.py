import re
import psycopg2
import config

def extrair_referencias_sem_marcas():
    """Extrai as referências que não retornaram marcas do log"""
    referencias = []
    try:
        with open('reprocessar_marcas.log', 'r') as arquivo:
            for linha in arquivo:
                if "WARNING - Nenhuma marca encontrada para a referência" in linha:
                    # Extrai a referência e o tipo de veículo usando regex
                    match = re.search(r"referência (.+?) do tipo (.+?)$", linha)
                    if match:
                        referencia = match.group(1)
                        tipo_veiculo = match.group(2)
                        referencias.append((referencia, tipo_veiculo))
        return referencias
    except Exception as e:
        print(f"Erro ao extrair referências: {e}")
        return []

def get_referencias_ids(referencias):
    """Obtém os IDs das referências no banco de dados"""
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        referencias_com_ids = []
        for referencia, tipo_veiculo in referencias:
            # Extrai mês e ano da referência
            mes, ano = referencia.split('/')
            
            # Busca o ID da referência
            cur.execute("""
                SELECT id FROM referencias 
                WHERE mes = %s AND ano = %s
            """, (mes, ano))
            
            resultado = cur.fetchone()
            if resultado:
                referencias_com_ids.append((resultado[0], referencia, tipo_veiculo))
        
        cur.close()
        conn.close()
        return referencias_com_ids
    except Exception as e:
        print(f"Erro ao obter IDs das referências: {e}")
        return []

def main():
    # Extrai as referências que não retornaram marcas
    referencias = extrair_referencias_sem_marcas()
    print(f"Encontradas {len(referencias)} referências sem marcas no log")
    
    # Obtém os IDs das referências
    referencias_com_ids = get_referencias_ids(referencias)
    print(f"Encontrados {len(referencias_com_ids)} IDs de referências no banco")
    
    # Salva as referências em um arquivo
    with open('referencias_sem_marcas.txt', 'w') as arquivo:
        for ref_id, referencia, tipo_veiculo in referencias_com_ids:
            arquivo.write(f"{ref_id},{referencia},{tipo_veiculo}\n")
    
    print("Arquivo 'referencias_sem_marcas.txt' criado com sucesso!")

if __name__ == "__main__":
    main() 