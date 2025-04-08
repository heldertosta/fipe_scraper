import logging
import os

def setup_logging(script_name):
    """
    Configura o logging para usar o mesmo nome base do arquivo de script
    
    Args:
        script_name: Nome do arquivo de script (geralmente __file__)
    """
    # Cria o diretório logs se não existir
    os.makedirs('logs', exist_ok=True)
    
    # Remove a extensão .py e adiciona .log
    base_name = os.path.splitext(os.path.basename(script_name))[0]
    log_file = os.path.join('logs', f"{base_name}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    ) 