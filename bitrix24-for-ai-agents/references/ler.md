# Ler: consultar, exportar e auditar

## Sumário

1. Filtro, select e ordem
2. O mapa do portal
3. Listas grandes
4. Receitas de leitura
5. Muitas consultas de uma vez: batch
6. Datas e fuso
7. O que a API não mostra (e como ler mesmo assim)
8. Ligações e gravações
9. Entregar a leitura

## 1. Filtro, select e ordem

**Filtro:** a chave do filtro leva um prefixo que diz a comparação.

| Prefixo | Significa | Exemplo (API antiga) | Exemplo (crm.item) |
|---|---|---|---|
| (nenhum) ou `=` | igual | `{"STAGE_ID": "NEW"}` (funil 0) ou `"C3:NEW"` (funil 3) | `{"stageId": "C3:NEW"}` |
| `!` | diferente | `{"!STATUS_ID": "JUNK"}` | `{"!stageId": "C3:LOSE"}` |
| `>`, `>=`, `<`, `<=` | maior, menor | `{">=DATE_CREATE": "2026-09-01T00:00:00-03:00"}` | `{">=createdTime": "2026-09-01T00:00:00-03:00"}` |
| `%` | contém | `{"%TITLE": "teste"}` | `{"%title": "teste"}` |
| `@` | está na lista | `{"@ASSIGNED_BY_ID": [5, 7]}` | `{"@assignedById": [5, 7]}` |
| `!@` | não está na lista | `{"!@STAGE_ID": ["WON", "LOSE"]}` | |

- **Select:** peça só o que vai usar.
  - Na API antiga, `["*", "UF_*"]` traz tudo, inclusive os campos personalizados.
  - No `crm.item.list`, `["*"]` traz tudo, e o telefone e o e-mail (`fm`) só vêm assim.
- **Ordem:** `"order": {"ID": "ASC"}` na API antiga, e `{"id": "ASC"}` na universal.
- **Booleano personalizado no `crm.item.list`:** filtre com 1 ou 0, e não com Y ou N.
- **Permissão:** itens que o usuário do webhook não pode ver somem do resultado sem aviso. Se o número parecer baixo, confira de quem é o webhook.

## 2. O mapa do portal

**Pergunta simples de leitura:** o mapa mínimo basta. São o `ping`, os funis e as etapas da entidade em questão, os campos dela e os usuários.

**Antes de modificar ou configurar:** o mapa completo, abaixo.

**Onde guardar:** numa pasta de trabalho, um JSON por chamada, por exemplo `bitrix24-trabalho/<portal>/mapa/`.
- O mapa só tem estrutura (funis, etapas, campos, nomes de usuário), e pode ficar com o projeto.
- O backup e as exportações têm dado de cliente. Ficam fora de controle de versão e são apagados quando o trabalho acaba.
- Nenhum dos dois guarda o webhook.

Num portal novo, antes de qualquer outra coisa, leia e guarde:

```
python3 scripts/b24.py ping
python3 scripts/b24.py call crm.type.list
python3 scripts/b24.py call crm.category.list '{"entityTypeId": 2}'
python3 scripts/b24.py call crm.status.list
python3 scripts/b24.py fields lead
python3 scripts/b24.py fields deal
python3 scripts/b24.py list crm.deal.userfield.list '{}'     # list, e não call: portal antigo passa de 50 campos
python3 scripts/b24.py list user.get '{}'      # todos, inclusive inativos: o responsável antigo precisa de nome
python3 scripts/b24.py call department.get
```

Para cada Smart Process, rode também:
- `crm.category.list` com o `entityTypeId` dele;
- `fields <entityTypeId>`.

**O mapa responde:**
- **Entidades:** quais estão em uso, e quantos registros cada uma tem. O `total` sai da primeira página de um `list` com `select: ["ID"]`.
- **Funis e etapas:** o nome, o código e o tipo (`SEMANTICS`) de cada um.
- **Campos personalizados:** o código, o rótulo, o tipo e as opções de lista com os IDs.
- **Pessoas:** os usuários ativos e os departamentos.
- **Plano:** se a API respondeu, o plano tem REST.

Use os nomes e os códigos do mapa em todo o trabalho, e nunca adivinhe um código de etapa ou de campo.

## 3. Listas grandes

- **Até alguns milhares de registros:** `b24.py list METODO PARAMS --saida arquivo.jsonl`. O script segue o `next` página por página, de 50 em 50.
- **Acima disso:** use `--por-id`. Ele ordena por ID e pede o que vem depois do último ID lido, sem calcular o total (`start = -1`).
  - É o caminho que a documentação recomenda.
  - No exemplo da própria documentação, 2,39 milhões de itens: 49,9 s por página com a contagem, e 0,097 s sem.
- **Nunca pare numa página fixa.** Leia até não vir mais `next`. O 151º registro some sem aviso quando alguém "lê só as 3 primeiras páginas".
- **Grande e recorrente demais para a API:** para análise de volume grande, o próprio Bitrix24 aponta o BI Builder, e não a REST (references/bi-builder.md).

## 4. Receitas de leitura

| Pergunta | Como responder |
|---|---|
| Quantos registros há num filtro | `call` no `.list` com `select: ["ID"]`, e ler o `total` |
| Quem está parado há mais de N dias | **Padrão:** a última mudança de etapa (`MOVED_TIME`), com o corte `<` (hora do servidor, de `server.time`, menos N dias) e só etapas de andamento (pelo `SEMANTICS`). A última alteração do card (`DATE_MODIFY`) muda com qualquer escrita, inclusive de automação. Diga o critério na resposta e, se o usuário quiser, mostre o outro |
| O que mudou de etapa num período | `crm.stagehistory.list` com `>=CREATED_TIME` e `<=CREATED_TIME`, e o `entityTypeId` |
| Por onde um card passou | `crm.stagehistory.list` filtrado pelo `OWNER_ID`. O funil atual não diz por onde ele passou |
| Quantos por responsável e etapa | `list` com `select` de responsável e etapa, e agrupar do seu lado |
| Quem está sem próxima atividade | `crm.activity.list` com `COMPLETED: "N"` e `OWNER_TYPE_ID`, e cruzar com os registros abertos |
| Atividades vencidas | `crm.activity.list` com `<DEADLINE` de agora e `COMPLETED: "N"` |
| Tarefas atrasadas de um grupo | `tasks.task.list` com `GROUP_ID` (em maiúsculas: `groupId` é ignorado e devolve tudo) e `REAL_STATUS` |
| Duplicados por telefone ou e-mail | `crm.duplicate.findbycomm`, com até 20 valores por chamada. Documento (CNPJ) em campo personalizado não entra na busca nativa |
| Comentários de um registro | `crm.timeline.comment.list` com `ENTITY_ID` e `ENTITY_TYPE` em minúsculas (`deal`) |
| Produtos de um negócio | `crm.item.productrow.list` com `=ownerType` e `=ownerId`. No `batch`, codifique o `=` da chave (o script já faz isso) |
| Observadores de um negócio | `crm.item.get` com `entityTypeId: 2`. O `crm.deal.get` não traz |
| Processos de negócio rodando | `bizproc.workflow.instances` (exige administrador) |

**Antes de responder "quanto", diga o critério.** "Parado" pela última atividade é diferente de "parado" pela última mudança de etapa, e as duas leituras dão números diferentes.

## 5. Muitas consultas de uma vez: batch

- **Até 50 comandos numa chamada,** e o lote conta como uma requisição no limite de taxa.
- **Arquivo para o `b24.py batch`:**

  ```json
  {
    "lead10": ["crm.lead.get", {"id": 10}],
    "lead11": ["crm.lead.get", {"id": 11}]
  }
  ```

- **Referência entre comandos:** `$result[nome][campo]`. Exemplo: `department.get?ID=$result[usuario][UF_DEPARTMENT][0]`.
- **Com `halt: 0`** (o padrão do script), o lote roda tudo e junta os erros em `result_error`.
- **Não rodam dentro do batch:** upload e download de arquivo, e batch dentro de batch.

## 6. Datas e fuso

- **Mande as datas com o fuso explícito:** `2026-10-09T00:00:00-03:00`.
- **O portal tem um fuso, e cada usuário tem o seu.** Sem o fuso explícito, vale o do perfil do usuário do webhook.
- **Confira com `server.time` e com uma data conhecida** antes de fechar uma análise por horário.
- **No BI Builder,** as datas do sistema vêm no fuso do servidor e os campos de data personalizados vêm como texto (references/bi-builder.md).

## 7. O que a API não mostra (e como ler mesmo assim)

| O que | Pela REST | Como ler |
|---|---|---|
| Regras de automação (robôs) de uma etapa | Não: `bizproc.workflow.template.list` exclui esses modelos de propósito | **(a)** Pedir ao usuário que abra o funil > Regras de automação e diga quais regras há na etapa. **(b)** Exportar o modelo da etapa e ler com `scripts/bpt.py resumo`. **(c)** No navegador logado, com autorização: na página de automação do funil, o HTML do iframe traz, depois de cada `DOCUMENT_STATUS`, os robôs da etapa em JSON (`Type`, `Properties`, `Activated`). Pelo designer: `BX.Bizproc.Automation.Designer.getInstance().component.templateManager.templatesData` |
| Obrigatório por etapa | Não aparece no `.fields` | No navegador logado: abra o cartão (ele carrega num iframe) e leia o `BX.Crm.EntityEditor`, em `getScheme()` > elementos > `getData().attrConfigs`. O `typeId` 3 é obrigatório; o `phaseGroupTypeId` 2 são as etapas do funil e o 3 as de perda, com a etapa inicial e a final |
| Seções do cartão | Sim | `crm.deal.details.configuration.get` (`scope: "C"`, `extras.dealCategoryId`), ou `crm.item.details.configuration.get` |
| Permissões e papéis | Não | Tela: Configurações do CRM > Permissões |
| Formulários do site | Só a lista (`crm.webform.list`) | Tela |
| Webhooks, apps e handlers de evento instalados | Não pelo webhook | Tela: Aplicações > Recursos para desenvolvedores. Desinstalar um app apaga os handlers dele sem aviso |

**Antes de mudar a etapa de qualquer registro, leia as regras da etapa de destino.** É o que evita mandar mensagem para cliente sem querer.

## 8. Ligações e gravações

- **Estatística de chamadas:** `voximplant.statistic.get`, escopo `telephony`. Exige a permissão de ver a estatística.
  - Filtros como `{">=CALL_DURATION": 240}` funcionam.
  - **Tipos (`CALL_TYPE`):** 1 saída, 2 entrada, 3 entrada redirecionada, 4 retorno, 5 informativa.
- **Gravação:**
  - quando há `RECORD_FILE_ID`, o áudio está no Drive: baixe pelo `DOWNLOAD_URL` do `disk.file.get`;
  - quando só há `CALL_RECORD_URL`, o arquivo está no provedor de telefonia, e pode já ter expirado (404).
- **Baixar muitos arquivos:** faça fora do navegador (script ou fluxo), porque o navegador costuma bloquear download disparado por código.

## 9. Entregar a leitura

- **O número, com o filtro em palavras:** "214 negócios no funil Vendas, em etapas de andamento, sem mudança de etapa desde 01/08".
- **Os registros com link,** até umas 20 linhas no chat. Acima disso, um CSV com a coluna de link. O endereço do portal pode aparecer no link: só o código do webhook é segredo.
- **Formato dos links:**
  - `https://PORTAL/crm/lead/details/ID/` (e `deal`, `contact`, `company`);
  - em Smart Process, `https://PORTAL/crm/type/{entityTypeId}/details/ID/`.
- **O que ficou de fora e por quê:** sem permissão, registros de teste, importados ou campos vazios.
- **Arquivo de exportação:** CSV com separador `;` e codificação UTF-8 com BOM, para abrir certo no Excel em português.
