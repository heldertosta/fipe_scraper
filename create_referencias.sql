-- Apaga a tabela se ela existir
DROP TABLE IF EXISTS referencias CASCADE;

-- Cria a tabela de referências com campos para ordenação
CREATE TABLE referencias (
    id SERIAL PRIMARY KEY,
    mes_ano VARCHAR(20) NOT NULL,
    mes INT NOT NULL,
    ano INT NOT NULL,
    UNIQUE(mes_ano)
); 