import requests
from bs4 import BeautifulSoup
import psycopg2
import time
import logging
from typing import Dict, List, Optional
import json

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fipe_scraper.log'),
        logging.StreamHandler()
    ]
)

class FipeScraper:
    def __init__(self, db_config: Dict):
        self.base_url = "https://veiculos.fipe.org.br/"
        self.session = requests.Session()
        self.db_config = db_config
        self.conn = None
        self.cur = None

    def connect_db(self):
        """Conecta ao banco de dados PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cur = self.conn.cursor()
            logging.info("Conexão com o banco de dados estabelecida")
        except Exception as e:
            logging.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def close_db(self):
        """Fecha a conexão com o banco de dados"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            logging.info("Conexão com o banco de dados fechada")

    def get_referencias(self, tipo_veiculo: str) -> List[Dict]:
        """Obtém a lista de referências (meses/anos) disponíveis"""
        try:
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontra o select de referências baseado no tipo de veículo
            select_id = f"selectTabelaReferencia{tipo_veiculo}"
            select = soup.find('select', {'id': select_id})
            
            if not select:
                raise Exception(f"Select de referências não encontrado para {tipo_veiculo}")
            
            referencias = []
            for option in select.find_all('option'):
                if option.get('value'):
                    referencias.append({
                        'codigo': int(option['value']),
                        'mes_ano': option.text.strip()
                    })
            
            return referencias
        except Exception as e:
            logging.error(f"Erro ao obter referências para {tipo_veiculo}: {e}")
            return []

    def get_marcas(self, tipo_veiculo: str, referencia: int) -> List[Dict]:
        """Obtém a lista de marcas para um tipo de veículo e referência específicos"""
        try:
            url = f"{self.base_url}api/veiculos/ConsultarMarcas"
            payload = {
                "codigoTabelaReferencia": referencia,
                "codigoTipoVeiculo": 1 if tipo_veiculo == "carro" else 3 if tipo_veiculo == "caminhao" else 2
            }
            
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                raise Exception(f"Erro na requisição: {response.status_code}")
            
            return response.json()
        except Exception as e:
            logging.error(f"Erro ao obter marcas para {tipo_veiculo} e referência {referencia}: {e}")
            return []

    def get_modelos(self, tipo_veiculo: str, referencia: int, marca: int) -> List[Dict]:
        """Obtém a lista de modelos para uma marca específica"""
        try:
            url = f"{self.base_url}api/veiculos/ConsultarModelos"
            payload = {
                "codigoTabelaReferencia": referencia,
                "codigoTipoVeiculo": 1 if tipo_veiculo == "carro" else 3 if tipo_veiculo == "caminhao" else 2,
                "codigoMarca": marca
            }
            
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                raise Exception(f"Erro na requisição: {response.status_code}")
            
            return response.json()
        except Exception as e:
            logging.error(f"Erro ao obter modelos para marca {marca}: {e}")
            return []

    def get_anos(self, tipo_veiculo: str, referencia: int, marca: int, modelo: int) -> List[Dict]:
        """Obtém a lista de anos/combustíveis para um modelo específico"""
        try:
            url = f"{self.base_url}api/veiculos/ConsultarAnoModelo"
            payload = {
                "codigoTabelaReferencia": referencia,
                "codigoTipoVeiculo": 1 if tipo_veiculo == "carro" else 3 if tipo_veiculo == "caminhao" else 2,
                "codigoMarca": marca,
                "codigoModelo": modelo
            }
            
            response = self.session.post(url, json=payload)
            if response.status_code != 200:
                raise Exception(f"Erro na requisição: {response.status_code}")
            
            return response.json()
        except Exception as e:
            logging.error(f"Erro ao obter anos para modelo {modelo}: {e}")
            return []

    def save_referencia(self, mes_ano: str, codigo: int) -> int:
        """Salva uma referência no banco de dados e retorna o ID"""
        try:
            self.cur.execute(
                "INSERT INTO referencias (mes_ano, codigo_fipe) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id",
                (mes_ano, codigo)
            )
            result = self.cur.fetchone()
            if result:
                return result[0]
            
            self.cur.execute(
                "SELECT id FROM referencias WHERE mes_ano = %s AND codigo_fipe = %s",
                (mes_ano, codigo)
            )
            return self.cur.fetchone()[0]
        except Exception as e:
            logging.error(f"Erro ao salvar referência {mes_ano}: {e}")
            raise

    def save_marca(self, nome: str, codigo: int, tipo_veiculo: str) -> int:
        """Salva uma marca no banco de dados e retorna o ID"""
        try:
            self.cur.execute(
                "INSERT INTO marcas (nome, codigo_fipe, tipo_veiculo) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING RETURNING id",
                (nome, codigo, tipo_veiculo)
            )
            result = self.cur.fetchone()
            if result:
                return result[0]
            
            self.cur.execute(
                "SELECT id FROM marcas WHERE nome = %s AND codigo_fipe = %s AND tipo_veiculo = %s",
                (nome, codigo, tipo_veiculo)
            )
            return self.cur.fetchone()[0]
        except Exception as e:
            logging.error(f"Erro ao salvar marca {nome}: {e}")
            raise

    def save_modelo(self, marca_id: int, nome: str, codigo: int) -> int:
        """Salva um modelo no banco de dados e retorna o ID"""
        try:
            self.cur.execute(
                "INSERT INTO modelos (marca_id, nome, codigo_fipe) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING RETURNING id",
                (marca_id, nome, codigo)
            )
            result = self.cur.fetchone()
            if result:
                return result[0]
            
            self.cur.execute(
                "SELECT id FROM modelos WHERE marca_id = %s AND nome = %s AND codigo_fipe = %s",
                (marca_id, nome, codigo)
            )
            return self.cur.fetchone()[0]
        except Exception as e:
            logging.error(f"Erro ao salvar modelo {nome}: {e}")
            raise

    def save_variacao(self, modelo_id: int, referencia_id: int, ano: str, combustivel: str):
        """Salva uma variação (ano/combustível) no banco de dados"""
        try:
            self.cur.execute(
                "INSERT INTO variacoes (modelo_id, referencia_id, ano, combustivel) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (modelo_id, referencia_id, ano, combustivel)
            )
        except Exception as e:
            logging.error(f"Erro ao salvar variação {ano} {combustivel}: {e}")
            raise

    def scrape_tipo_veiculo(self, tipo_veiculo: str):
        """Executa o scraping completo para um tipo de veículo"""
        try:
            logging.info(f"Iniciando scraping para {tipo_veiculo}")
            
            # Obtém as referências
            referencias = self.get_referencias(tipo_veiculo)
            logging.info(f"Encontradas {len(referencias)} referências para {tipo_veiculo}")
            
            for ref in referencias:
                try:
                    referencia_id = self.save_referencia(ref['mes_ano'], ref['codigo'])
                    logging.info(f"Processando referência: {ref['mes_ano']}")
                    
                    # Obtém as marcas
                    marcas = self.get_marcas(tipo_veiculo, ref['codigo'])
                    logging.info(f"Encontradas {len(marcas)} marcas para {ref['mes_ano']}")
                    
                    for marca in marcas:
                        try:
                            marca_id = self.save_marca(marca['Label'], marca['Value'], tipo_veiculo)
                            logging.info(f"Processando marca: {marca['Label']}")
                            
                            # Obtém os modelos
                            modelos = self.get_modelos(tipo_veiculo, ref['codigo'], marca['Value'])
                            logging.info(f"Encontrados {len(modelos)} modelos para {marca['Label']}")
                            
                            for modelo in modelos:
                                try:
                                    modelo_id = self.save_modelo(marca_id, modelo['Label'], modelo['Value'])
                                    
                                    # Obtém os anos/combustíveis
                                    anos = self.get_anos(tipo_veiculo, ref['codigo'], marca['Value'], modelo['Value'])
                                    
                                    for ano in anos:
                                        try:
                                            # Separa o ano e o combustível
                                            ano_combustivel = ano['Label'].split(' ')
                                            ano_valor = ano_combustivel[0]
                                            combustivel = ' '.join(ano_combustivel[1:])
                                            
                                            self.save_variacao(modelo_id, referencia_id, ano_valor, combustivel)
                                        except Exception as e:
                                            logging.error(f"Erro ao processar ano {ano['Label']}: {e}")
                                            continue
                                    
                                    self.conn.commit()
                                except Exception as e:
                                    logging.error(f"Erro ao processar modelo {modelo['Label']}: {e}")
                                    continue
                                
                                time.sleep(1)  # Delay para não sobrecarregar o servidor
                        except Exception as e:
                            logging.error(f"Erro ao processar marca {marca['Label']}: {e}")
                            continue
                        
                        time.sleep(1)  # Delay para não sobrecarregar o servidor
                except Exception as e:
                    logging.error(f"Erro ao processar referência {ref['mes_ano']}: {e}")
                    continue
                
                time.sleep(1)  # Delay para não sobrecarregar o servidor
        except Exception as e:
            logging.error(f"Erro ao processar tipo de veículo {tipo_veiculo}: {e}")
            raise

def main():
    # Configuração do banco de dados
    db_config = {
        'dbname': 'fipe_db',
        'user': 'seu_usuario',
        'password': 'sua_senha',
        'host': 'localhost',
        'port': '5432'
    }
    
    scraper = FipeScraper(db_config)
    
    try:
        scraper.connect_db()
        
        # Executa o scraping para cada tipo de veículo
        for tipo in ['carro', 'caminhao', 'moto']:
            scraper.scrape_tipo_veiculo(tipo)
            
    except Exception as e:
        logging.error(f"Erro durante a execução: {e}")
    finally:
        scraper.close_db()

if __name__ == "__main__":
    main() 