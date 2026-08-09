
--Apagar tabela para inserção/atualização dos indicadores se necessário

DROP  TABLE IF EXISTS indicadores;

--Criar tabela de indicadores

CREATE TABLE indicadores (
    nm_indicador TEXT PRIMARY KEY,
    vlr_indicador REAL
);

--Inserção dos dados na tabela de indicadores

INSERT INTO indicadores (nm_indicador, vlr_indicador) 

-- 1. [empresas + cartoes] % de usuários que são simultaneamente cargo de liderança e têm cartão premium (American Express).
-- ESTRATÉGIA: Identificar percentual de usuários que ocupam cargos de liderança e possuem cartão premium. 
-- Um percentual alto indica que o perfil do público-alvo é de alto poder aquisitivo, o que pode justificar determinados tipos de campanhas e produtos voltados para esse público.


select 
    'percentual_usuarios_lideranca_cartao_premium' as nm_indicador,
    ROUND(SUM(case when b.card_type = 'American Express' and (c.title like '%Manager%' or c.title like '%Chief%') then 1 else null end) * 100.0 / count(*), 2) as vlr_indicador
from company c
join bank b on c.user_id = b.user_id


UNION ALL




-- 2. [users + empresas] Idade média de quem ocupa cargo de liderança.
-- ESTRATÉGIA: Identificar perfil de idade da liderança, que ajuda a definir a estratégia de comunicação para esse público.



select 
    'idade_media_usuarios_lideranca' as nm_indicador,
    ROUND(AVG(u.age), 2) as vlr_indicador
from users u
join company c on u.id = c.user_id
where c.title like '%Manager%' or c.title like '%Chief%'

UNION ALL

-- 3. [enderecos + empresas] % de usuários que moram na mesma cidade onde a empresa está sediada.
-- ESTRATÉGIA: Identificar modelo de trabalho do público-alvo, se remoto ou presencial. 
-- O que ajuda a definir o tipo de campanha mais efetiva para esse público, se presencial ou digital.


select 
    'percentual_usuarios_mesmo_cidade_empresa' as nm_indicador,
    ROUND(SUM(case when a.city = c.city then 1 else null end) * 100.0 / count(*), 2) as vlr_indicador
from address a
join company c on a.user_id = c.user_id


UNION ALL

-- 4. [users + cartoes] % de usuários jovens (< 35 anos) com cartão premium.
-- ESTRATÉGIA: Identificar percentual do grupo de alto potencial de crescimento.
-- Um percentual alto indica que o perfil do público-alvo é de alto potencial de crescimento financeiro precoce e consequentemente maior poder de compra no futuro.


select 
    'percentual_usuarios_jovens_cartao_premium' as nm_indicador,
    ROUND(SUM(case when u.age < 35 and b.card_type = 'American Express' then 1 else null end) * 100.0 / count(*), 2) as vlr_indicador
from users u
join bank b on u.id = b.user_id