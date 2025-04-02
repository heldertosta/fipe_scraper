# Scraper da Tabela FIPE

Este projeto é um scraper para coletar dados da tabela FIPE (Fundação Instituto de Pesquisas Econômicas) e armazená-los em um banco de dados PostgreSQL.

## Estrutura do Banco de Dados

O banco de dados possui as seguintes tabelas:

- `referencias`: Armazena as referências (meses/anos) disponíveis
- `marcas`: Armazena as marcas de veículos
- `modelos`: Armazena os modelos de veículos
- `variacoes`: Armazena as variações (ano/combustível) dos modelos

## Requisitos

- Python 3.8+
- PostgreSQL
- Bibliotecas Python listadas em `requirements.txt`

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual Python:
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
4. Crie o banco de dados PostgreSQL:
   ```sql
   CREATE DATABASE fipe_db;
   ```
5. Execute o script SQL para criar as tabelas:
   ```bash
   psql -U seu_usuario -d fipe_db -f create_tables.sql
   ```

## Configuração

Edite o arquivo `fipe_scraper.py` e atualize as configurações do banco de dados:

```python
db_config = {
    'dbname': 'fipe_db',
    'user': 'seu_usuario',
    'password': 'sua_senha',
    'host': 'localhost',
    'port': '5432'
}
```

## Uso

Execute o script:

```bash
python fipe_scraper.py
```

O script irá:
1. Conectar ao banco de dados
2. Coletar dados para cada tipo de veículo (carros, caminhões e motos)
3. Armazenar os dados no banco de dados
4. Gerar logs de progresso no arquivo `fipe_scraper.log`

## Observações

- O script inclui delays entre as requisições para não sobrecarregar o servidor
- Erros são registrados no arquivo de log
- O script usa `ON CONFLICT DO NOTHING` para evitar duplicatas
- O processo pode levar várias horas dependendo da quantidade de dados 