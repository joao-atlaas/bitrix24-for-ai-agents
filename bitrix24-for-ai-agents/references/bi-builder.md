# BI no Bitrix24 (BI Builder: Superset + Trino)

Regras para qualquer projeto de BI sobre Bitrix24, em qualquer segmento: restrição da plataforma, limite estrutural do modelo de dados e armadilha que já custou caro. Leia **antes** de prometer um painel: a seção 8 muda o escopo do projeto.

## 1 · O que é o BI Builder (e o que isso implica)

Apache Superset com engine **Trino** por baixo, embarcado no Bitrix24. Consequências imediatas:

- Dataset "virtual" é uma **query salva no Superset**, não tabela física. O SQL Lab fala direto com o Trino, então `SELECT * FROM meu_dataset` retorna `NO_TABLE`. Para validar um dataset, envolva o SQL inteiro numa subquery.
- Toda tabela exige prefixo de schema: `bitrix24.crm_deal`, `bitrix24.crm_deal_uf`, `bitrix24."user"` (aspas obrigatórias em `user`: palavra reservada).
- SQL Lab executa **uma instrução por vez**. Query anterior sobrando no editor gera `mismatched input 'WITH'`. Limpe o editor antes de colar.
- Alguns wrappers de dataset não aceitam `WITH` no início. Se der erro de parse, converta os CTEs em subqueries aninhadas: funciona sempre.
- **O dashboard tem dois lados e eles NÃO são o mesmo objeto.** O painel do portal (`/bi/dashboard/`, módulo biconnector: status, grupos, compartilhamento, período) embrulha um dashboard Superset (`b<conta>.bi.bitrix24.com`). Dashboard criado direto no Superset **não aparece no portal e não pode ser compartilhado**. Fluxo certo: criar o painel pelo criador do portal (+ Criar) e depois popular o dashboard Superset correspondente. **Charts e datasets são reaproveitáveis** entre dashboards: só o objeto dashboard precisa nascer no portal (seção 11).

## 2 · Armadilhas de SQL no Trino

| Problema | Sintoma | Solução |
|---|---|---|
| Divisão inteira | Taxa sempre `0` | `CAST(SUM(a) AS DOUBLE) / NULLIF(SUM(b),0)` |
| Formato D3 `.1%` | Valor 100× inflado (3.676,5%) | O formato já multiplica por 100. **Não** multiplique no SQL |
| Campos de data em `*_uf` | Erro ao comparar com timestamp | São `varchar`: `TRY_CAST(NULLIF(TRIM(x),'') AS timestamp)` |
| Datas lixo (1970, 2099) | Escala do gráfico destruída | `CASE WHEN year(...) BETWEEN <primeiro ano do negócio> AND year(current_date) + 1 THEN ... END` |
| Usuário/departamento formatado | `[6] Maria Souza` como dimensão | `regexp_replace(x,'^\[\d+\]\s*','')` + `TRIM` |
| Valor de X na linha de max/min Y | Subquery complicada | `max_by(campo, id)` / `min_by(campo, data)` |
| Tags em texto `[A] [B] [C]` | Parse manual | `regexp_extract_all(t,'\[([^\]]+)\]',1)` + `contains(...)` / `element_at(...,1)` |
| Data de entrada posterior ao evento | Card reentrou no funil | `LEAST(data_do_historico, data_criacao)` |

Funções que valem memorizar: `count(*) FILTER (WHERE ...)`, `max_by`, `min_by`, `element_at`, `contains`, `TRY_CAST`, `NULLIF`, `LEAST`.

## 3 · Modelo de dados do Bitrix: o que quebra a análise

### 3.1 `crm_deal` guarda apenas o estado ATUAL
Sem histórico de responsável, funil ou etapa. O que está na linha é o agora.

**Consequência gravíssima:** cards **movem** entre funis, não duplicam. Em processo com funis sequenciais (captação → atendimento → proposta → fechamento), o funil atual **não** diz por onde o card passou. Medir "entrou no funil X" pelo funil atual subconta massivamente: já houve caso em que mais da metade dos leads rastreados apareceu como "sem lead de origem".

**Solução:** `crm_deal_stage_history` tem o nome do funil. Agregue por deal para reconstruir a passagem:

```sql
MAX(CASE WHEN category_name = 'Funil A' THEN 1 ELSE 0 END) AS passou_a,
MIN(CASE WHEN category_name = 'Funil A' THEN date_create END) AS dt_entrada_a
```

Sempre `COALESCE` com o funil atual, para o card que ainda não gerou histórico.

### 3.2 Responsável não tem histórico: limite estrutural
Card transferido sobrescreve o responsável anterior. **Não existe forma de reconstruir quem atendeu antes.** Isso mata qualquer métrica de produtividade individual na etapa inicial do processo.

O que dá para medir: por **equipe** em qualquer ponto (derivando equipe do cadastro atual do usuário, ela se auto-atualiza) · por **pessoa** só nas etapas finais (quem tem o card agora) · por pessoa na etapa inicial **apenas para cards que ainda estão nela**: e isso precisa estar escrito no título do gráfico.

Se o cliente exige atribuição individual histórica, a única saída é gravar o responsável em campo próprio no momento da transferência, via automação. **Levante na primeira reunião**, não depois de montar o painel.

### 3.3 Um cliente = N cards
Jornadas reais geram múltiplos cards (reentrada, duplicata, funis paralelos). Análise de funil precisa de **chave de jornada** com cadeia de fallback: `ID externo da integração → contact_id → deal_id`. Prefixe os fallbacks (`C123`, `D456`) para não colidir com o ID externo.

### 3.4 Poluição obrigatória de excluir
- **Cards importados de outro CRM**: sem rastro de origem, destroem qualquer taxa de conversão. Marque na migração (`UF_..._IMPORTADO = 'Y'` + ID no CRM antigo) e exclua no dataset. Um único importado com 500 eventos vira outlier que achata o gráfico inteiro.
- **Etapas técnicas** de automação ("Disparar manualmente", filas internas).
- **Títulos de teste**: `lower(title) NOT LIKE '%teste%'` e as variantes que a equipe usou.

### 3.5 Campos de lista (`enumeration`)
- Escrita via REST exige o **ID numérico do item**, não o rótulo. Leia com `crm.deal.userfield.list` filtrando por `FIELD_NAME` para obter os IDs.
- `MANDATORY: Y` é validado **só na interface**. O REST grava sem o campo: tornar obrigatório na UI não protege a integração (nem a quebra).
- Valores órfãos acontecem (IDs que não existem na lista). Audite a distribuição antes de confiar no campo.

### 3.6 Propriedades de produto no catálogo
Sintaxe que funciona: `PROPERTY_{ID}: "valor"` como chave plana em `fields`. Formatos aninhados (`PROPERTY_VALUES`, `{"VALUE":...}`, `{"n0":{"VALUE":...}}`) falham **silenciosamente**: retornam sucesso e não gravam.

### 3.7 Fuso
O display do Bitrix pode estar em fuso diferente do dado bruto. Confira uma data conhecida antes de fechar qualquer análise de horário.

## 4 · Desenho do dataset

### 4.1 Um dataset, não dois
Tentador separar "grão de jornada" e "grão de card". **Não faça.** Filtros nativos do dashboard se ligam a um dataset; com dois, o filtro de período/equipe não alcança metade dos gráficos. Escolha um grão e carregue o resto como coluna.
**Grão recomendado:** uma linha por jornada, com `qtd_cards` e `id_do_card_de_entrada` como colunas. Cobre funil, taxas e tabela de detalhe.

### 4.2 Padrão de flags booleanas
Modele cada evento como `0/1` na linha da jornada (`f_entrou, f_agendou, f_realizou, f_avancou, f_fechou, f_perdido_a, f_perdido_b`). Ganho: toda métrica vira `SUM(flag)` e toda taxa vira razão de somas: compõe com qualquer dimensão sem reescrever SQL.

### 4.3 Desfecho: coluna única, não N booleanas
Booleanas de desfecho agregadas com `max()` produzem linhas **ganhas E perdidas ao mesmo tempo** (o card ganhou num funil, perdeu noutro). Derive uma categórica única do estado do card mais recente:

```sql
CASE WHEN f_fechou = 1 THEN 'Fechado'
     WHEN etapa_do_ultimo_card = 'Perdido A' THEN 'Perdido - A'
     WHEN etapa_do_ultimo_card = 'Perdido B' THEN 'Perdido - B'
     ELSE 'Em andamento' END AS desfecho
```

Se precisar das booleanas para métricas, derive-as **do desfecho**: garante exclusividade mútua.

### 4.4 Duas datas, dois significados
- **`dt_entrada`**: quando a jornada começou → "dos leads que entraram no período, quantos converteram?"
- **`dt_evento`** (agendamento, realização, fechamento) → "quantos eventos aconteceram no período?"

São perguntas diferentes e dão números diferentes. Marque as duas como temporais e **escreva o critério no título de cada gráfico**: evita 80% das discussões de "esse número está errado".

### 4.5 Sem filtro de data no SQL
O período vive no dashboard. Dataset com `WHERE data >= X` engessado é retrabalho garantido.

### 4.6 Duplo par de colunas de pessoa/equipe
`responsavel_entrada / equipe_entrada` (`min_by` pela data de entrada) e `responsavel_atual / equipe_atual` (`max_by` pelo id). **Nomeie honestamente:** se `responsavel_entrada` na prática é "quem tem agora" (por causa de 3.2), não chame de "quem recebeu".

### 4.7 Validação obrigatória antes de publicar
```sql
SELECT count(*) AS linhas, count(DISTINCT chave_jornada) AS jornadas FROM (...) t
```
Se diferirem, há join multiplicando linhas: quase sempre a tabela de histórico.

## 5 · Métricas

Defina no **dataset**, nunca por gráfico. Métrica repetida em 8 charts divergem em 8 direções.

```
Entradas       SUM(f_entrou)        Realizados   SUM(f_realizou)
Agendamentos   SUM(f_agendou)       Fechados     SUM(f_fechou)
% A→B          CAST(SUM(f_b) AS DOUBLE) / NULLIF(SUM(f_a),0)     formato .1%
```

- O **nome da taxa tem que conter numerador e denominador**. `% Consult→Visita` e `% Visita agendada→realizada` são coisas diferentes e serão confundidas se o nome não disser.
- Ao refatorar, **apague as métricas antigas**. Deixá-las convivendo quebra charts depois com `Columns missing in dataset: [...]`, e o erro aponta a coluna, não o gráfico culpado.
- Filtros salvos em charts também referenciam colunas: coluna removida do SQL = chart quebrado. Revise os filtros ao trocar o SQL.

## 6 · Configuração de gráficos (Superset)

- **Bar Chart:** a categoria vai no **X-axis**; **Dimensions fica vazio**. Dimensions é a *segunda* quebra (série empilhada). O X-axis é obrigatório e não pode repetir o campo da Dimension.
- **Funil por etapa** = uma dimensão (equipe/pessoa) + N métricas na ordem do processo. Não é série temporal: data no eixo X de um "funil" é o erro mais comum.
- **Table:** modo **Aggregate** para dimensão + métricas; **Raw records** só para listagem.
- **`<NULL>`** aparece como categoria e costuma ser a maior barra. Filtre `campo IS NOT NULL` e diga no título que o gráfico considera só registros preenchidos.
- **Orientação horizontal** para qualquer dimensão com rótulo textual longo.
- Marque as colunas temporais como *Is temporal* / *Default datetime*, senão o filtro de período não aparece.

## 7 · Escrita de dados (quando o BI depende de corrigir a origem)

- **Idempotência** por campo de ID externo. Todo backfill deve poder rodar de novo sem duplicar efeito: filtre por "campo destino vazio".
- **Nunca sobrescreva preenchimento manual.** Padrão: ler o registro antes do update e remover o campo do payload se já tiver valor. Registre no retorno o que foi preservado, para auditoria.
- **Bitrix limita taxa de escrita.** Depois de ~1.000 updates o webhook entra em throttle e *todas* as chamadas passam a arrastar: parece travamento, não é. Jobs em lote: rodar em background, log com flush, e medir progresso consultando o estado real no CRM em vez de confiar no log.
- **Teste de tipo antes do lote:** escreva num único registro, leia de volta, restaure. Confirma que o formato do valor é aceito (crítico em campos de lista).
- Fallback conservador: se a leitura do registro falhar, **não** escreva.

## 8 · Limites que vão para o cliente na PRIMEIRA reunião

Levantar antes de prometer painel: isto é escopo de venda, não detalhe técnico:

1. **Atribuição individual histórica**: impossível sem automação que grave o responsável na transferência (seção 3.2).
2. **Status por evento** (realizado / não realizado / remarcado, com múltiplas ocorrências): exige objeto separado (Smart Process), **depende do plano**. Alternativa sem upgrade: funil dedicado onde cada evento é um card ligado ao registro principal. Campo único no card não guarda histórico de N ocorrências.
3. **Campos não obrigatórios** viram buraco no BI. Ordem correta: automatizar o preenchimento → validar → só então tornar obrigatório.
4. **Registros de origem "natural"**: toda operação tem entradas que nascem no meio do processo (prospecção própria, indicação, carteira). Legitimamente não têm etapa inicial e ficam fora do funil. Se não for dito, o funil parece furado.
5. **Data de corte de confiabilidade**: antes da migração/integração o dado não é comparável. Defina e comunique.

## 9 · Sequência de trabalho

1. **Diagnóstico read-only**: nada é alterado enquanto se investiga. Evidência primeiro.
2. Validar hipótese com **SQL agregado** antes de escrever dataset.
3. Construir o dataset e rodar a checagem `linhas vs jornadas` (seção 4.7).
4. Criar as métricas no dataset.
5. Ajustar charts **por aba**, um de cada vez.
6. **Comparar número novo × número antigo** e explicar cada divergência antes de publicar.
7. Publicar; só então esconder os gráficos antigos.
8. Escrever o critério no título de cada gráfico.

Rollback definido antes de qualquer publicação.

## 10 · Anti-padrões: conferência rápida

- [ ] Criar dashboard direto no Superset e esperar que apareça no portal (seção 1 e seção 11)
- [ ] Medir passagem por funil usando o funil atual do card
- [ ] Dois datasets no mesmo dashboard
- [ ] `SUM()/SUM()` sem `CAST AS DOUBLE`
- [ ] `*100` no SQL junto com formato `%`
- [ ] Booleanas de desfecho agregadas com `max()` (gera ganho + perda na mesma linha)
- [ ] Métrica definida no chart em vez do dataset
- [ ] Métrica antiga sobrevivendo ao refactor
- [ ] Data no eixo X de um gráfico chamado "funil"
- [ ] Cards importados/de teste dentro do dataset
- [ ] `<NULL>` como maior barra do gráfico
- [ ] Gráfico sem dizer se o período filtra entrada ou evento
- [ ] Nome de coluna que promete mais do que o dado entrega
- [ ] Backfill sem filtro de idempotência
- [ ] Automação sobrescrevendo campo preenchido à mão
- [ ] Campo obrigatório antes da automação de preenchimento

## 11 · Automação pela API interna (Superset + portal), validada em produção

**Antes de qualquer gravação por esta via, o mesmo protocolo de references/modificar.md:**
- o plano do que vai ser criado ou mudado, e o "pode" do usuário;
- um GET do objeto guardado antes de cada PUT, para poder voltar;
- nunca mexer no painel em uso: o novo nasce em paralelo;
- excluir painel, gráfico ou dataset fica com a pessoa, pela tela.

A UI do BI Builder não é o único caminho. A **API REST interna do Superset** aceita a sessão do navegador logado, e o portal expõe managers JS. Montar 5 dashboards com 44 gráficos levou minutos, em vez de horas arrastando componente.

**Autenticação (Superset, domínio `b<conta>.bi.bitrix24.com`):**
- GET funciona direto com a sessão. POST/PUT exigem header `X-CSRFToken`, obtido em `/api/v1/security/csrf_token/` **com `X-Requested-With: XMLHttpRequest`**: sem esse header o endpoint responde 403.
- Executar tudo via `fetch` dentro de uma aba no próprio domínio. **Nunca imprimir o token** no output (filtros de segurança bloqueiam a resposta inteira). O estado do `window` morre a cada navegação: manter uma **aba dedicada só para API**.

**Fluxo de construção 100% API:**
1. SQL de descoberta: `POST /api/v1/sqllab/execute/` `{database_id, sql, runAsync: false}`: retorna dados inline.
2. Dataset virtual: `POST /api/v1/dataset/` `{database, schema, table_name, sql}` → `PUT /api/v1/dataset/{id}/refresh` (sincroniza colunas; timestamps já saem `is_dttm`) → `PUT /api/v1/dataset/{id}` `{metrics, main_dttm_col}`.
3. Chart: `POST /api/v1/chart/` `{slice_name, datasource_id, datasource_type: 'table', viz_type, params: JSON, dashboards: [ids]}`. Antes de inventar `params`, **copiar de um chart de sistema** do mesmo `viz_type` (GET `/api/v1/chart/{id}`): o formato muda por versão.
4. Layout: `PUT /api/v1/dashboard/{id}` `{position_json, json_metadata}`. `position_json` v2: ROOT → GRID → ROW → CHART (`meta: {chartId, width (12 col), height (~8px/un)}`). Filtros nativos em `json_metadata.native_filter_configuration`. Ao mexer em dashboard criado pelo portal, **preservar o `json_metadata` existente** e só mesclar o que mudou.

**Pegadinhas de `params` (ECharts):**
- `x_axis_sort` compara com o **`metric_name`** do form_data, não com o `verbose_name`. Com `orientation: horizontal`, `x_axis_sort_asc: true` põe a maior barra **no topo**.
- `stack` é a string `'Stack'`, não boolean. Barra categórica: `x_axis` + `xAxisForceCategorical: true` (Dimensions continua sendo a 2ª quebra, seção 6).
- Métrica salva entra como string (`metric_name`); adhoc como `{expressionType: 'SQL', sqlExpression, label}`.

**Lado portal (domínio do cliente, JS na página `/bi/dashboard/`):**
- Criar painel: botão **+ Criar** abre slider (`biconnector.apachesuperset.dashboard.edit`, iframe same-origin). Preencher `#dashboard-title-field` e chamar `BX.BIConnector.SupersetDashboardEditManager.Instance.onClickSave()`. **Cada chamada salva um painel novo**: chamadas repetidas em cima do mesmo formulário criam duplicatas silenciosas; confirmar o retorno do ajax (`data.dashboard.id`) antes de repetir.
- O dashboard Superset do painel é criado com o mesmo título; mapear pelo diff de `GET /api/v1/dashboard/` antes/depois.
- Grid manager: `BX.BIConnector.SupersetDashboardGridManager.Instance` → `publish(id, {id, publish: true})` (RASCUNHO→PRONTO), `deleteDashboard`, `showSharePopup`. Excluir painel: `BX.ajax.runAction('biconnector.dashboard.delete', {data: {id}})`.
- **O período do painel (ex.: "Últimos 30 dias") é injetado pelo wrapper no filtro nativo de tempo** do dashboard. Métrica de snapshot (carteira, abertos) fica cortada pela data de criação; o usuário troca o período no viewer, mas o padrão engana. Configurar o período do painel de acordo com o que os cartões medem.
- Compartilhamento é **link + senha** por painel (popup do grid). Envolve senha: fazer **manualmente**, não automatizar.
