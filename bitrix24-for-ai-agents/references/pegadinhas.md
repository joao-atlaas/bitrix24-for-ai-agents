# Pegadinhas: a lista para conferir antes de entregar

Cada item já custou retrabalho em projeto real ou está na documentação oficial. O detalhe de cada um está na referência indicada.

## Acesso e plano

- [ ] **O plano tem API REST?** No Essentials, não tem, desde 2026. Integrações em plano mensal ou trimestral param em 30/11/2026 sem migração para Vibe+ (acesso.md, seção 2).
- [ ] **O webhook age como quem o criou,** com as permissões dessa pessoa. Item sem permissão some da lista sem aviso.
- [ ] **O webhook não faz o que exige aplicativo:** `event.bind`, robô próprio, importar processo de negócio, `biconnector.*` (acesso.md, seção 1).
- [ ] **O webhook de saída e o robô webhook não repetem o envio.** Se o seu servidor cair, o evento se perde: ponha uma conferência periódica.
- [ ] **O endereço do webhook não aparece em chat, arquivo, documento nem fluxo compartilhado.**

## A API que mente

- [ ] **Releia depois de gravar.** A API responde sucesso e ignora a escrita em vários casos (modificar.md, seção 5):
  - `CATEGORY_ID` no `crm.deal.update`;
  - opções de lista enviadas só com as novas;
  - campo de nome terminado em número;
  - arquivo em formato errado;
  - propriedade de produto aninhada;
  - máscara de campo.
- [ ] **No `crm.item.add`, campo com nome errado é ignorado sem erro.**
- [ ] **`MANDATORY: Y` só vale na tela.** A REST grava sem o campo obrigatório.
- [ ] **Os erros do `biconnector` vêm dentro do `result`, com HTTP 200.**

## Etapas e automações

- [ ] **Mudar etapa pela API roda as regras da etapa de destino,** que podem mandar mensagem ao cliente. Leia as regras antes (ler.md, seção 7).
- [ ] **Criar pela API roda as regras da primeira etapa.** A importação por CSV não roda.
- [ ] **Etapa final e conversão fecham as atividades e as tarefas abertas,** sem opção de desligar.
- [ ] **A mudança de etapa cancela as regras ainda pendentes da etapa,** inclusive as que estavam esperando.
- [ ] **"Executar depois da anterior" espera também a espera da anterior.**
- [ ] **"Alterar etapa" não move na mesma gravação da mudança de etapa.** Use um gatilho de campo.
- [ ] **Robô novo não roda para quem já estava na etapa.**
- [ ] **O `save_automation` duplica os gatilhos que ficaram de fora,** em vez de apagar (configurar.md, seção 7).
- [ ] **A REST não lista nem cria os robôs padrão das etapas.**
- [ ] **Em robô, a opção de lista é o código (`XML_ID`); na REST, é o ID numérico.**
- [ ] **"Solicitação" não cria atividade em Smart Process.** Use "Planejar atividade".

## Campos e estrutura

- [ ] **No Smart Process, o `typeId` (campos) é diferente do `entityTypeId` (itens).**
- [ ] **O obrigatório por etapa não aparece na API.** Leia pela tela.
- [ ] **O campo é da entidade:** o campo novo aparece em todos os funis. Ajuste o cartão de cada funil.
- [ ] **O booleano de Smart Process só aceita `Y` e `N`.** O decimal sem `PRECISION` nasce sem casas. O `multiple` não muda depois.
- [ ] **Não dá para criar etapa com ordem maior que a da final.** Funil com ID de dois dígitos trunca o código da etapa padrão.
- [ ] **Smart Process com funis desligados recusa `crm.category.add`.** Funil novo pode nascer sem acesso para a equipe.
- [ ] **Campo de rótulo repetido:** confira qual dos homônimos tem dado.
- [ ] **O `crm.item.productrow.set` substitui todas as linhas de produto.**
- [ ] **No máximo 3 itens fixados na linha do tempo de cada registro.**

## Datas e fuso

- [ ] **Data sem fuso explícito vale o fuso do perfil do usuário do webhook.** Uma carga já saiu 10 h deslocada.
- [ ] **Servidor e usuário em fusos diferentes deslocam as datas nas regras e no BI.** Confira com uma data conhecida.
- [ ] **`{=System:Date}` é a data do servidor:** à noite, pode já ser o dia seguinte.
- [ ] **Cadastre os feriados antes de confiar em prazo de dia útil.**

## Tarefas, atividades e autoria

- [ ] **Comentário na linha do tempo sai sempre como o dono do webhook.** A tarefa aceita `CREATED_BY`.
- [ ] **O resumo obrigatório da tarefa só é cobrado na tela.** Pela API ou pelo card, passa sem resumo.
- [ ] **O criador da tarefa sempre pode mudar o prazo.**
- [ ] **No `tasks.task.list`, o filtro é em MAIÚSCULAS** (`groupId` é ignorado e devolve tudo). O `REAL_STATUS` é diferente do `STATUS`.
- [ ] **O `crm.activity.add` é obsoleto** e exige `COMMUNICATIONS` para chamada e e-mail. Use `crm.activity.todo.add`.
- [ ] **Quem moveu de etapa é `MOVED_BY_ID`.** O `MODIFY_BY_ID` muda com qualquer escrita.

## Integração externa

- [ ] **O fluxo que grava no card que o disparou entra em laço.** Compare antes de gravar.
- [ ] **Criar dezenas de registros de uma vez estoura o limite** e derruba os webhooks de saída. Espace as criações.
- [ ] **Deduplique por chave fixa, e nunca pelo título.**
- [ ] **Emoji de 4 bytes vira texto em vários campos.**
- [ ] **O robô webhook é sempre POST.** O GET dá 404 silencioso em várias ferramentas.

## Limites

- [ ] **Limite de taxa:** 2 requisições por segundo por portal e por IP de origem, com picos até 50 (no Enterprise, 5 por segundo e picos até 250). O `batch` conta como 1.
- [ ] **Há um segundo limite, pelo tempo acumulado de cada método** numa janela de 10 minutos: `OPERATION_TIME_LIMIT` (429). Espere a janela.
- [ ] **`OVERLOAD_LIMIT` é bloqueio manual.** Não repita.
- [ ] **Acima de umas mil escritas seguidas, o portal freia.** Parece travamento, e não é.
- [ ] **Lista de 50 por página.** Para volume, pagine por ID com `start = -1`.

## BI Builder

- [ ] **Painel criado direto no Superset não aparece no portal** (bi-builder.md).
- [ ] **O funil atual do card não diz por onde ele passou,** e o responsável não tem histórico.
- [ ] **Não há API oficial para painéis.** A interna funciona com a sessão do navegador.

## Ferramentas do agente

- [ ] **A saída de JavaScript no navegador pode ser cortada ou bloqueada** quando parece endereço com parâmetros. Devolva JSON e números.
- [ ] **O "Salvar" do rodapé da automação grava tudo o que está aberto.**
- [ ] **O agente não digita senha, não faz login e não exclui pela tela:** isso é da pessoa.
