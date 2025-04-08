from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import logging

logger = logging.getLogger(__name__)

class FipeScraper:
    def selecionar_marca(self, marca):
        """Seleciona uma marca no dropdown."""
        try:
            # Aguarda o dropdown de marcas estar visível
            marca_select = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "selectMarcacarro"))
            )
            
            # Clica no dropdown para abrir as opções
            marca_select.click()
            time.sleep(1)  # Aguarda o dropdown abrir
            
            # Encontra a opção da marca
            marca_option = marca_select.find_element(By.XPATH, f".//option[contains(text(), '{marca}')]")
            marca_option.click()
            
            # Aguarda o carregamento
            time.sleep(2)
            
            logger.info(f"Marca '{marca}' selecionada com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao selecionar marca '{marca}': {str(e)}")
            return False

    def get_modelos(self):
        """Extrai os modelos da marca selecionada."""
        try:
            # Aguarda o dropdown de modelos estar visível
            modelo_select = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "selectAnoModelocarro"))
            )
            
            # Clica no dropdown para abrir as opções
            modelo_select.click()
            time.sleep(1)  # Aguarda o dropdown abrir
            
            # Encontra todas as opções de modelo
            modelo_options = modelo_select.find_elements(By.TAG_NAME, "option")
            
            # Extrai os textos das opções (ignorando a primeira opção que é vazia)
            modelos = [option.text for option in modelo_options[1:]]
            
            logger.info(f"Encontrados {len(modelos)} modelos")
            return modelos
            
        except Exception as e:
            logger.error(f"Erro ao extrair modelos: {str(e)}")
            return [] 