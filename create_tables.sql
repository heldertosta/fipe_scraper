-- Criação da tabela de referências (meses/anos)
CREATE TABLE referencias (
    id SERIAL PRIMARY KEY,
    mes_ano VARCHAR(20) NOT NULL,
    codigo_fipe INTEGER NOT NULL,
    UNIQUE(mes_ano, codigo_fipe)
);

-- Criação da tabela de marcas
CREATE TABLE marcas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    codigo_fipe INTEGER NOT NULL,
    tipo_veiculo VARCHAR(20) NOT NULL, -- 'carro', 'caminhao', 'moto'
    UNIQUE(nome, codigo_fipe, tipo_veiculo)
);

-- Criação da tabela de modelos
CREATE TABLE modelos (
    id SERIAL PRIMARY KEY,
    marca_id INTEGER REFERENCES marcas(id),
    nome VARCHAR(200) NOT NULL,
    codigo_fipe INTEGER NOT NULL,
    UNIQUE(marca_id, nome, codigo_fipe)
);

-- Criação da tabela de anos/combustíveis
CREATE TABLE variacoes (
    id SERIAL PRIMARY KEY,
    modelo_id INTEGER REFERENCES modelos(id),
    referencia_id INTEGER REFERENCES referencias(id),
    ano VARCHAR(20) NOT NULL, -- Pode ser 'Zero KM' ou um ano específico
    combustivel VARCHAR(50) NOT NULL,
    UNIQUE(modelo_id, referencia_id, ano, combustivel)
); 