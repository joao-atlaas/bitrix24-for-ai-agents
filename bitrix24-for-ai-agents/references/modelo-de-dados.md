# O modelo de dados do CRM

O que é preciso saber antes da primeira consulta num portal. Conferido na documentação oficial em outubro de 2026.

## Sumário

1. Duas APIs para o mesmo CRM
2. Entidades e entityTypeId
3. Funis (categorias)
4. Etapas
5. Campos
6. Telefone e e-mail (multicampos)
7. Vínculos entre registros
8. Linha do tempo, atividades e tarefas
9. Histórico de etapas
10. Produtos
11. Usuários e estrutura
12. Arquivos

## 1. Duas APIs para o mesmo CRM

- **A API universal, `crm.item.*`:** é a recomendada.
  - Um método para todas as entidades, com o `entityTypeId`.
  - Os campos vêm em camelCase: `title`, `stageId`, `assignedById`, `ufCrm5_Campo`.
  - O resultado de lista vem em `result.items`.
- **A API antiga por entidade** (`crm.lead.*`, `crm.deal.*`, `crm.contact.*`, `crm.company.*`):
  - campos em MAIÚSCULAS (`TITLE`, `STAGE_ID`, `ASSIGNED_BY_ID`, `UF_CRM_...`);
  - está marcada como obsoleta na documentação, mas continua funcionando e aparece em muito material e fluxo existente.
- **Ao trocar de uma para a outra, mude os nomes dos campos.**
  - Na universal, `useOriginalUfNames: "Y"` devolve os campos personalizados no formato `UF_CRM_...`.
  - Na universal, telefone e e-mail (`fm`) só vêm com `select: ["*"]`.
- **Quando a antiga ainda é útil:** quando o fluxo existente já usa os nomes em MAIÚSCULAS, e para alguns campos que se comportam melhor nela. Por exemplo, as datas e os campos UF do Negócio: veja references/modificar.md, seção 3.
- **O CRM não está na REST 3.0** (o endereço `/rest/api/`), que por enquanto cobre tarefas, estrutura e outros módulos.

## 2. Entidades e entityTypeId

| Entidade | entityTypeId | Código curto |
|---|---|---|
| Lead | 1 | L |
| Negócio | 2 | D |
| Contato | 3 | C |
| Empresa | 4 | CO |
| Fatura antiga | 5 | I |
| Orçamento | 7 | Q |
| Requisito (dados cadastrais) | 8 | |
| Fatura nova | 31 | SI |
| Smart Process (SPA) | 128 a 192, ou par a partir de 1030 | T + o número em hexadecimal minúsculo (128 vira T80) |

- **Descobrir os Smart Processes:** `crm.type.list`. Cada um tem dois números:
  - o `entityTypeId`, usado nos itens;
  - o `id` do tipo, usado nos campos (`userfieldconfig`).

  Confundir os dois é erro comum.
- **Os códigos curtos aparecem** no vínculo de tarefa (`UF_CRM_TASK`: `D_123`), nas linhas de produto (`ownerType`) e em campos de vínculo.

## 3. Funis (categorias)

- **Listar:** `crm.category.list {"entityTypeId": 2}`. O funil padrão de Negócio tem `id` 0.
- **Criar:** `crm.category.add`. Não se apaga o funil padrão nem funil com itens.
- **Smart Process com funis desligados:** `isCategoriesEnabled = N` dá `ENTITY_TYPE_NOT_SUPPORTED` ao criar funil. Ligue antes (`crm.type.update`).
- **Lead não tem funis:** tem uma lista única de etapas (status).
- **`crm.dealcategory.*` é obsoleto.**

## 4. Etapas

**Onde estão:** `crm.status.list` com filtro por `ENTITY_ID`:

| Entidade | ENTITY_ID | Código da etapa no registro |
|---|---|---|
| Lead | `STATUS` | `NEW`, `IN_PROCESS`, `CONVERTED`, `JUNK`... (em `STATUS_ID`) |
| Negócio, funil 0 | `DEAL_STAGE` | `NEW`, `PREPARATION`, `WON`, `LOSE`... (em `STAGE_ID`) |
| Negócio, outro funil | `DEAL_STAGE_{idFunil}` | `C{idFunil}:CODIGO` |
| Smart Process | `DYNAMIC_{entityTypeId}_STAGE_{idFunil}` | `DT{entityTypeId}_{idFunil}:CODIGO` |

**Leia também:**
- **Tipo da etapa:** o campo `SEMANTICS` diz se é andamento (vazio ou `P`), ganho (`S`) ou perda (`F`). Nunca deduza pelo nome.
- **Filtro:** `%ENTITY_ID` devolve tudo. Filtre do seu lado.
- **Criar etapa:** `crm.status.add` com `ENTITY_ID`, `STATUS_ID`, `NAME`, `SORT`, `COLOR` e `SEMANTICS`.
  - Em funil não padrão, o prefixo `C{id}:` entra sozinho.
  - O `SORT` acima da etapa de ganho dá erro: crie ou reordene as finais primeiro.
  - O `STATUS_ID` tem até 21 ou 22 caracteres: letras latinas, números, hífen e sublinhado.
  - Exige administrador do CRM.
- **Funil de Negócio com ID de dois dígitos:** o código da etapa padrão pode sair truncado (`C10:PREPAYMENT_INVOIC`).
- **Outras listas no `crm.status`:** `SOURCE` (fontes), `CONTACT_TYPE`, `COMPANY_TYPE`, `INDUSTRY`, entre outras. O `crm.status.entity.types` lista todas.

## 5. Campos

- **Descrever:** `crm.item.fields {"entityTypeId": N}`, ou o `.fields` da entidade (`crm.deal.fields`).
  - Traz o tipo, se é obrigatório, se é múltiplo, se é só leitura e o título.
  - O `b24.py fields deal` é o atalho.
- **Campos personalizados (UF):**
  - **Formato:** `UF_CRM_...` na API antiga, e `ufCrm...` ou `ufCrm{typeId}_...` na universal.
  - **Criar no CRM clássico:** `crm.deal.userfield.add` (e os de lead, contact, company).
    - O prefixo entra sozinho.
    - O nome tem até 50 caracteres.
    - Exige administrador.
  - **Criar em Smart Process:** `userfieldconfig.add`, com `entityId: CRM_{idDoTipo}`.
- **Campo de lista (`enumeration`):**
  - As opções têm um `ID` numérico e um código (`XML_ID`).
  - **Pela API:** grave o ID. Leia as opções em `crm.deal.userfield.list` (o `LIST` de cada campo).
  - **Em regras de automação:** use o código.
- **Obrigatório:**
  - O `isRequired` do `.fields` é o obrigatório geral, que só a tela cobra.
  - O obrigatório por etapa não aparece na API (references/ler.md, seção 7).
- **Campo com rótulo repetido é comum em portal antigo,** com dois ou três campos para o mesmo dado. Antes de usar um campo, confira qual deles tem dado.

## 6. Telefone e e-mail (multicampos)

- **Na API antiga,** os campos `PHONE`, `EMAIL`, `WEB` e `IM` são listas: `[{"ID": "12", "VALUE": "+5511...", "VALUE_TYPE": "WORK"}]`.
  - Sem `ID`, o valor é acrescentado.
  - Com `ID`, é atualizado.
  - Com `ID` e `VALUE` vazio, é removido.
- **Na universal,** o campo é `fm`: `[{"typeId": "PHONE", "valueType": "WORK", "value": "+55..."}]`.
  - Para atualizar, use o `id` do valor.
  - Para acrescentar, use uma chave nova (`n0`).
  - Para remover, mande o `id` com valor vazio.
- **Procurar por telefone ou e-mail:** `crm.duplicate.findbycomm`, com até 20 valores por chamada. Acha Lead, Contato e Empresa.

## 7. Vínculos entre registros

- **Contato e Empresa:** `crm.contact.company.items.get` e `.set`. Negócio e contatos: `crm.deal.contact.items.get` e `.set`.
- **Smart Process:** o vínculo nativo é o campo `parentId{entityTypeId}` (por exemplo, `parentId2` liga ao Negócio). É ele que aparece na aba do cartão. Campo UF não faz isso.
  - As relações pai e filho entre tipos se configuram no `crm.type.update`.
- **Conversão de Lead:** cria Negócio, Contato e Empresa pela tela, ou pela automação de conversão do portal.

## 8. Linha do tempo, atividades e tarefas

- **Comentário:** `crm.timeline.comment.add`, `.update` e `.list`.
  - Os `fields` vão em minúsculo, e `ENTITY_TYPE` é `lead`, `deal`, `contact`, `company` ou `DYNAMIC_{entityTypeId}`.
  - O autor é sempre o dono do webhook.
- **Fixar:** `crm.timeline.item.pin`. Cada registro aceita no máximo 3 itens fixados.
- **Atividades:**
  - `crm.activity.list` lista;
  - a atividade universal "a fazer" é `crm.activity.todo.add`, com `ownerTypeId`, `ownerId`, `deadline` e lembretes em `pingOffsets`;
  - `crm.activity.add` é obsoleto e exige `COMMUNICATIONS` para chamada e e-mail.
  - **Filtros:** `>=DEADLINE` com data ISO e `%SUBJECT` funcionam em `crm.activity.list`.
- **Tarefas:** `tasks.task.*`.
  - O vínculo com o CRM fica em `UF_CRM_TASK` (`["D_123", "L_45"]`).
  - O filtro vai em MAIÚSCULAS, e a resposta vem em camelCase.
  - O `REAL_STATUS` (2 aguardando, 3 em andamento, 4 aguardando controle, 5 concluída, 6 adiada) é diferente do `STATUS`, que inclui estados calculados como atrasada.
- **Etapa final e conversão** fecham as atividades e as tarefas abertas do registro.

## 9. Histórico de etapas

- **`crm.stagehistory.list {"entityTypeId": 2, "filter": {...}}`.** O resultado vem em `result.items`.
  - O `TYPE_ID` diz: 1 criação, 2 etapa intermediária, 3 etapa final, 5 troca de funil.
  - Lead traz `STATUS_ID`; Negócio e Smart Process trazem `STAGE_ID` e `CATEGORY_ID`.
- **O registro guarda só o estado atual.** O responsável não tem histórico: quem atendia antes de uma transferência se perde. O funil por onde o card passou só se reconstrói pelo histórico de etapas.
- **Quem moveu de etapa:** `MOVED_BY_ID`, e quando: `MOVED_TIME`. O `MODIFY_BY_ID` muda com qualquer escrita.

## 10. Produtos

- **Catálogo:** `catalog.product.*`, com `iblockId` no filtro e `id` e `iblockId` no `select`. O `crm.product.*` é obsoleto.
- **Linhas de produto do registro:**
  - `crm.item.productrow.list`, com `filter: {"=ownerType": "D", "=ownerId": 123}`, os dois obrigatórios;
  - `crm.item.productrow.set` **substitui todas as linhas**.
- **Propriedade de produto:** `PROPERTY_{ID}` direto em `fields`.

## 11. Usuários e estrutura

- **`user.get`:**
  - filtra por `ACTIVE`, `UF_DEPARTMENT` e `USER_TYPE`;
  - não traz bots nem usuários de canal aberto;
  - com `ACTIVE: false`, mistura funcionários e extranet: filtre o `USER_TYPE`.
- **`department.get`:** os departamentos e o chefe (`UF_HEAD`).
  - "Gerente" nas regras de automação é o chefe do departamento.
  - Uma conta técnica do sistema pode aparecer como chefe e não sair no `user.get`.
- **Nomes de usuário fora do padrão** (caixa alta, espaço duplo) contaminam os relatórios por pessoa.

## 12. Arquivos

- **Campo de arquivo do CRM:** `["nome.pdf", "BASE64"]` (único) ou uma lista desses (múltiplo). Para limpar, use `''`.
- **Drive:** `disk.folder.uploadFile` com `fileContent: ["nome", "BASE64"]` e `data: {"NAME": "..."}`.
- **Imagem do catálogo:** `{"fileData": ["nome", "BASE64"]}`.
- **Baixar:**
  - no campo do CRM, use o `urlMachine`;
  - no Drive, o `DOWNLOAD_URL` do `disk.file.get`.

  O link expira: guarde o ID, e não o link.
- **Upload e download não rodam dentro do `batch`.**
