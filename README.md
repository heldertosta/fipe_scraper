# FIPE Scraper

Este projeto é um scraper para coletar dados da tabela FIPE (Fundação Instituto de Pesquisas Econômicas) de veículos. Ele coleta referências, marcas, modelos e valores dos veículos disponíveis no site da FIPE.

## Requisitos

- Python 3.8+
- PostgreSQL
- Google Chrome
- ChromeDriver

## Configuração do Ambiente

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd fipe_scraper
```

2. Crie um ambiente virtual Python e ative-o:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```
Edite o arquivo `.env` com suas configurações:
```
# Configurações do PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fipe
DB_USER=seu_usuario
DB_PASSWORD=sua_senha

# Configurações do Selenium
SELENIUM_HEADLESS=True  # True para executar sem interface gráfica
```

## Estrutura do Projeto

- `setup_database.py`: Script para criar a estrutura inicial do banco de dados
- `gerenciar_referencias.py`: Script para coletar e gerenciar referências da tabela FIPE
- `gerenciar_marcas.py`: Script para coletar e gerenciar marcas de veículos
- `limpar_banco.py`: Script para limpar o banco de dados quando necessário
- `config.py`: Configurações do projeto
- `.env`: Variáveis de ambiente (não versionado)
- `.env.example`: Exemplo de variáveis de ambiente
- `requirements.txt`: Dependências do projeto

## Uso

1. Primeiro, crie a estrutura do banco de dados:
```bash
python setup_database.py
```

2. Colete as referências disponíveis:
```bash
python gerenciar_referencias.py
```

3. Colete as marcas para todas as referências:
```bash
python gerenciar_marcas.py
```

Para limpar o banco de dados (se necessário):
```bash
python limpar_banco.py
```

## Estrutura do Banco de Dados

O banco de dados possui as seguintes tabelas:

1. `referencias`:
   - `id`: Identificador único
   - `mes`: Mês da referência
   - `ano`: Ano da referência
   - `mes_ano`: Combinação de mês/ano (ex: "janeiro/2025")

2. `marcas`:
   - `id`: Identificador único
   - `nome`: Nome da marca
   - `tipo_veiculo`: Tipo do veículo (carro, moto, caminhão)
   - `referencia_id`: Referência relacionada

3. `modelos`:
   - `id`: Identificador único
   - `nome`: Nome do modelo
   - `marca_id`: Marca relacionada
   - `referencia_id`: Referência relacionada

4. `anos`:
   - `id`: Identificador único
   - `ano`: Ano do modelo
   - `modelo_id`: Modelo relacionado
   - `referencia_id`: Referência relacionada

5. `valores`:
   - `id`: Identificador único
   - `valor`: Valor do veículo
   - `ano_id`: Ano relacionado
   - `referencia_id`: Referência relacionada

## Logs

Os scripts geram logs detalhados das operações realizadas. Os arquivos de log são criados no diretório do projeto com os seguintes nomes:
- `referencias.log`: Log das operações com referências
- `marcas.log`: Log das operações com marcas

## Observações

- O scraper está configurado para coletar dados de carros por padrão
- As operações são idempotentes, ou seja, não criam duplicatas no banco de dados
- O modo headless do Selenium pode ser configurado através da variável de ambiente `SELENIUM_HEADLESS`
- O sistema trata automaticamente erros de conexão e timeout

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas alterações (`git commit -am 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 