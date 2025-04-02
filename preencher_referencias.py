from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import psycopg2
import logging
import time
import config

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('referencias.log'),
        logging.StreamHandler()
    ]
)

def processar_data(mes_ano):
    """Converte o texto 'mes/ano' em valores numéricos"""
    try:
        # Mapeamento de meses para números
        meses = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        # Divide o texto em mês e ano
        mes_texto, ano = mes_ano.split('/')
        mes = meses[mes_texto.lower()]
        ano = int(ano)
        
        return mes, ano
    except Exception as e:
        logging.error(f"Erro ao processar data '{mes_ano}': {e}")
        raise

def get_referencias_existentes(cur):
    """Obtém a lista de referências já existentes no banco"""
    try:
        cur.execute("SELECT mes_ano FROM referencias")
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Erro ao obter referências existentes: {e}")
        return []

def get_referencias():
    """Obtém a lista de referências do select da página"""
    try:
        # Configuração do Chrome
        chrome_options = Options()
        if config.SELENIUM_CONFIG['headless']:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Inicializa o driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Acessa a página
        url = "https://veiculos.fipe.org.br/"
        driver.get(url)
        logging.info(f"Acessando a página: {url}")
        
        # Aguarda o carregamento da página
        time.sleep(config.SELENIUM_CONFIG['timeout'])
        
        # Executa o JavaScript para obter as referências
        js_script = """
        return Array.from(document.getElementById("selectTabelaReferenciacarro").options)
            .map(option => option.text.trim())
            .filter(text => text !== '');
        """
        
        referencias = driver.execute_script(js_script)
        logging.info(f"Encontradas {len(referencias)} referências no site")
        
        driver.quit()
        return referencias
    
    except Exception as e:
        logging.error(f"Erro ao obter referências: {e}")
        if 'driver' in locals():
            driver.quit()
        return []

def main():
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Obtém referências existentes
        referencias_existentes = get_referencias_existentes(cur)
        logging.info(f"Encontradas {len(referencias_existentes)} referências no banco")
        
        # Obtém as referências do site
        referencias_site = get_referencias()
        
        if not referencias_site:
            raise Exception("Nenhuma referência encontrada no site")
        
        # Filtra apenas as referências que não existem no banco
        novas_referencias = [ref for ref in referencias_site if ref not in referencias_existentes]
        
        if not novas_referencias:
            logging.info("Não há novas referências para adicionar")
            return
        
        logging.info(f"Encontradas {len(novas_referencias)} novas referências para adicionar")
        
        # Insere as novas referências no banco
        logging.info("Inserindo novas referências no banco de dados...")
        for ref in novas_referencias:
            mes, ano = processar_data(ref)
            cur.execute(
                "INSERT INTO referencias (mes_ano, mes, ano) VALUES (%s, %s, %s)",
                (ref, mes, ano)
            )
        
        conn.commit()
        logging.info("Processo concluído com sucesso!")
        
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