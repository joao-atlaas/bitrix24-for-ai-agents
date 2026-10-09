# Modificar dados com segurança

Escrever no Bitrix24 é fácil. Escrever sem quebrar a operação de alguém pede método: a API devolve sucesso e ignora a gravação em vários casos, e a mudança de etapa dispara automações que mandam mensagem para pessoas reais.

## Sumário

1. O protocolo em seis passos
2. O que pode disparar junto
3. Receitas de escrita
4. Lote
5. Ler de volta: quando a API mente
6. Desfazer
7. Excluir
8. Carga de dados

## 1. O protocolo em seis passos

1. **Ler.**
   - Liste os registros que vão mudar, com os campos que vão mudar.
   - Leia as automações das etapas envolvidas (references/ler.md, seção 7). Se não houver como ler (sem navegador e sem o modelo exportado), peça ao usuário, na mesma mensagem do plano, para dizer o que há na coluna da etapa de destino.
   - Se o destino é uma etapa final, conte as atividades e as tarefas abertas que vão fechar:
     - `crm.activity.list` com `COMPLETED: "N"`, `OWNER_TYPE_ID` e `@OWNER_ID`;
     - `tasks.task.list` com o vínculo `UF_CRM_TASK`.
   - Confira o fuso do usuário do webhook, se houver data (o `ping` mostra).
2. **Backup.** `b24.py backup METODO PARAMS --saida backup-AAAA-MM-DD.jsonl`, com todos os campos que vão mudar no `select`.
   - É só leitura, então pode vir antes do "pode".
   - Se o "pode" demorar (horas, outro dia), refaça antes de aplicar.
   - O arquivo tem dado de cliente: fora de controle de versão.
3. **Mostrar o plano e esperar o "pode".** Use este formato:

   ```
   Vou alterar 214 negócios do funil Vendas que estão em "Proposta" há mais de 60 dias:
   | Campo | Hoje | Depois |
   |---|---|---|
   | Etapa | Proposta (PREPARATION) | Perdido (LOSE) |
   | Motivo de perda | vazio | "Sem retorno" |
   Efeitos: a etapa Perdido tem 1 regra (e-mail "Sentimos sua falta" ao contato) e fecha as
   atividades abertas. Backup: backup-negocios-2026-10-09.jsonl. Posso aplicar?
   ```

   Se a etapa de destino manda mensagem ao cliente, diga isso em destaque. Ofereça o caminho sem disparo: uma etapa neutra, ou desligar a regra antes, com o dono do processo.
4. **Teste em um registro.** Grave, leia de volta e compare campo a campo. Isso confirma que o formato do valor foi aceito, o que é crítico em lista, data e arquivo. Esse registro sai do lote principal, para não gravar duas vezes.
5. **Lote.** `b24.py batch comandos.json --confirmar`.
6. **Conferir.**
   - Leia de novo o estado real (e não o log) e compare com o plano.
   - Informe: quantos mudaram, quantos falharam e por quê, onde está o backup e o comando de desfazer.

## 2. O que pode disparar junto

- **Mudar de etapa roda as regras da etapa de destino.** Isso vale quando a mudança vem pela API, por outra regra ou pelo seu fluxo externo. As regras podem mandar e-mail, SMS ou WhatsApp, criar tarefa, trocar o responsável ou chamar um webhook.
- **Criar pela API roda as regras da primeira etapa.** A importação por CSV é a exceção.
- **Etapa final** (ganho ou perda) e **converter o Lead** fecham sozinhos as atividades e as tarefas abertas, sem opção de desligar.
- **Gatilho de campo:** gravar um campo que é gatilho de outra etapa move o card.
- **Fluxo externo ligado à etapa:** se ele também grava no card, cuidado com o laço (references/automacao-externa.md).
- **Autoria:**
  - tudo o que você grava fica com o usuário do webhook em `MODIFY_BY_ID`;
  - quem moveu de etapa fica em `MOVED_BY_ID`;
  - nunca registre o usuário do webhook como autor de um evento humano.
- **Notificação para gente de verdade.** Mover um card de teste para uma etapa com aviso avisa o gestor real. Combine antes.

## 3. Receitas de escrita

| Quero | Como |
|---|---|
| Mudar campos de Lead, Contato, Empresa ou Negócio | `crm.lead.update {"id": 10, "fields": {"TITLE": "...", "UF_CRM_X": "..."}}`, com as chaves em MAIÚSCULAS |
| Mudar campos de Smart Process (ou de qualquer entidade, pela API universal) | `crm.item.update {"entityTypeId": 1036, "id": 5, "fields": {"title": "...", "ufCrm12_Campo": "..."}}`, com as chaves em camelCase |
| Mover etapa de Lead | `crm.lead.update` com `STATUS_ID` |
| Mover etapa de Negócio no mesmo funil | `crm.deal.update` com `STAGE_ID`; fora do funil 0, a etapa tem prefixo: `C3:NEW` |
| Trocar o funil de um Negócio | `crm.item.update {"entityTypeId": 2, "id": N, "fields": {"categoryId": 3, "stageId": "C3:NEW"}}`. O `crm.deal.update` com `CATEGORY_ID` responde sucesso e ignora |
| Trocar o responsável | `ASSIGNED_BY_ID` (Lead, Negócio) ou `assignedById` (item). Confira se há regra de "responsável alterado" |
| Observadores | `crm.item.update` com `observers: [ids]`. O `crm.deal.get` não traz observadores e o `crm.deal.add` não aceita |
| Campo de lista | Pela API, o ID numérico da opção (leia com `crm.<entidade>.userfield.list`). Em robô, o código (`XML_ID`) |
| Telefone e e-mail (multicampo) | API antiga: `"PHONE": [{"VALUE": "+55...", "VALUE_TYPE": "WORK"}]` acrescenta; com o `ID` do valor, troca; com o `ID` e `VALUE` vazio, remove. Universal: campo `fm`, chave nova `n0` acrescenta, `id` troca, `id` com valor vazio remove (modelo-de-dados.md, seção 6) |
| Data e hora | Com o fuso explícito (`2026-10-09T14:00:00-03:00`). Sem o fuso, vale o fuso do perfil do usuário do webhook: uma carga já saiu 10 h deslocada por isso |
| Arquivo num campo do CRM | Único: `["nome.pdf", "BASE64"]`. Múltiplo: `[["a.pdf", "..."], ["b.pdf", "..."]]`. No formato errado, grava vazio sem erro. Para o Drive, `disk.folder.uploadFile` com `fileContent`. Upload não roda dentro do `batch` |
| Comentário na linha do tempo | `crm.timeline.comment.add {"fields": {"ENTITY_ID": 10, "ENTITY_TYPE": "lead", "COMMENT": "..."}}` (`fields` em minúsculo; Smart Process: `DYNAMIC_{entityTypeId}`). O autor é sempre o dono do webhook (`AUTHOR_ID` é ignorado). Fixar: `crm.timeline.item.pin`, no máximo 3 por registro |
| Atividade com prazo (a fazer) | `crm.activity.todo.add` com `ownerTypeId`, `ownerId`, `deadline` e a descrição; lembretes em `pingOffsets`. O `crm.activity.add` é obsoleto e, para chamada ou e-mail, exige `COMMUNICATIONS` |
| Tarefa ligada ao CRM | `tasks.task.add {"fields": {"TITLE": "...", "RESPONSIBLE_ID": 5, "CREATED_BY": 7, "DEADLINE": "...", "UF_CRM_TASK": ["D_123"]}}`. Prefixos: `L_` Lead, `D_` Negócio, `C_` Contato, `CO_` Empresa |
| Aviso no sino | `im.notify.system.add` (sem remetente) ou `im.notify.personal.add` (sai como o dono do webhook) |
| Produtos do Negócio | `crm.item.productrow.set` ou `crm.deal.productrows.set` **substituem todas as linhas**: mande a lista inteira |
| Propriedade de produto | `PROPERTY_{ID}: "valor"` direto em `fields`. Os formatos aninhados falham em silêncio |
| Vínculo com item pai (Smart Process) | o campo nativo `parentId{entityTypeId}`; campo UF não popula a aba do cartão |

**Ordem de gravação no Negócio:**
1. `crm.deal.update` para datas e campos UF.
2. `crm.item.update` só para o funil e a etapa. O `crm.item.update` já deslocou datetime em alguns portais.

Para gravar o pai e a etapa juntos sem perder um dos dois, use dois `crm.item.update` no mesmo `batch`.

## 4. Lote

- **Arquivo de comandos para o `b24.py`:**

  ```json
  {
    "d101": ["crm.deal.update", {"id": 101, "fields": {"STAGE_ID": "LOSE"}}],
    "d102": ["crm.deal.update", {"id": 102, "fields": {"STAGE_ID": "LOSE"}}]
  }
  ```

- **Como o script envia:** 50 comandos por chamada, com espera entre os lotes. Ele devolve `result` e `result_error` por chave.
- **Ritmo:** acima de umas mil escritas seguidas, o portal entra em freio e tudo arrasta. Parece travamento, e não é.
  - Rode em segundo plano.
  - Meça o progresso pelo estado real do portal, e não pelo log.
- **Volume grande e recorrente** vai para um fluxo externo (references/automacao-externa.md, seção 6).
- **Dentro do `batch`, um comando pode usar o resultado de outro:** `$result[chave]`, como em `crm.timeline.comment.add?fields[ENTITY_ID]=$result[novo]`. O script não resolve isso por você: escreva a referência no parâmetro.

## 5. Ler de volta: quando a API mente

A API do Bitrix24 devolve `true` e ignora a escrita em vários casos. Depois de cada tipo de gravação, releia um registro e compare. Casos já vistos:
- **`CATEGORY_ID`** no `crm.deal.update`.
- **Opções de lista mandadas só com as novas** no `userfieldconfig.update`.
- **Campo de Smart Process com nome terminado em número:** a chave camelCase é ignorada. Use `ufCrm_<typeId>_<NOME>`.
- **Arquivo em formato errado:** grava vazio.
- **Propriedade de produto em formato aninhado:** não grava.
- **`SHOW_FILTER`** diferente de `"Y"` no `crm.deal.userfield.*`: é ignorado.
- **`SETTINGS.REGEXP`** (máscara): é ignorado.
- **`UF_EMPLOYMENT_DATE`** no `user.update`: é ignorado.

**`MANDATORY: Y` só vale na tela.** A REST grava sem o campo obrigatório. Tornar um campo obrigatório não protege nem quebra a integração.

## 6. Desfazer

O desfazer sai do backup, e só dos campos que a alteração mexeu. Assim não se apaga o que outras pessoas mudaram depois.

```
python3 scripts/restaurar.py backup.jsonl --metodo crm.deal.update --campos STAGE_ID,ASSIGNED_BY_ID \
    --saida restaurar.json [--ids 101,102]
python3 scripts/b24.py batch restaurar.json --confirmar
```

**Voltar para a etapa antiga roda de novo as regras daquela etapa.** Avise antes de desfazer uma mudança de etapa.

**O que não volta:**
- as mensagens que as regras mandaram;
- as atividades que a etapa final fechou;
- os campos excluídos (o Bitrix24 não guarda histórico de campo excluído);
- o valor sobrescrito sem backup.

Diga isso no plano (passo 3), antes de aplicar.

## 7. Excluir

- **A exclusão pela API não tem garantia de passar pela lixeira.** Prefira uma etapa de encerramento, um campo de status ou arquivar.
- **Exclusão só com pedido explícito e com backup completo** (todos os campos, `select: ["*", "UF_*"]`). O script pede `--confirmar --confirmar-exclusao`.
- **Registros de teste:** quem administra o portal manda para a lixeira pela tela, onde dá para restaurar.
- **Campo:** `crm.<entidade>.userfield.delete` usa o `id` numérico, e não o nome. Guarde o `get` do campo antes, porque os dados dele somem junto.

## 8. Carga de dados

- **Carregue antes de ligar os robôs,** ou carregue numa etapa neutra, sem regra. Senão a carga dispara as automações em massa.
- **A carga só preenche o vazio**, para nunca sobrescrever o que alguém preencheu à mão. Leia o registro antes e tire do payload o campo que já tem valor.
- **Idempotência.** Uma chave externa (o ID do sistema de origem num campo técnico) deixa rodar de novo sem duplicar. Um script de implantação confere antes de criar (o campo, a etapa ou o funil já existe?).
- **Ordem do teste:** um registro, depois um lote pequeno, depois a carga.
- **No fim:** releia 100% e compare os totais com a planilha de origem, por campo e por grupo.
- **Marque os importados** num campo (por exemplo, `UF_CRM_IMPORTADO = Y`, mais o ID no sistema antigo). Eles distorcem taxa de conversão no BI e precisam poder sair da conta.
