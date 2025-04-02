-- Apaga a tabela se ela existir
DROP TABLE IF EXISTS marcas CASCADE;

-- Cria a tabela de marcas com id, nome, tipo_veiculo e referencia_id
CREATE TABLE marcas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo_veiculo VARCHAR(20) NOT NULL,
    referencia_id INTEGER NOT NULL,
    FOREIGN KEY (referencia_id) REFERENCES referencias(id),
    UNIQUE(nome, tipo_veiculo, referencia_id)
); 