# Acesso: como o agente se conecta ao portal

Há cinco jeitos de um agente chegar a um portal Bitrix24. Para ler e mudar dados do CRM, o webhook de entrada resolve quase tudo e é o mais simples. Os outros entram quando o webhook não alcança.

Conferido na documentação oficial em outubro de 2026 (apidocs.bitrix24.com e helpdesk.bitrix24.com).

## Sumário

1. Webhook de entrada (o padrão)
2. O plano precisa ter API REST
3. Aplicativo local com OAuth
4. Webhook de saída e eventos
5. Servidor MCP do portal e Vibecode
6. Sessão do navegador (avançado)
7. Escopos por tarefa
8. Guardar o segredo

## 1. Webhook de entrada (o padrão)

**Como criar,** para explicar ao usuário:
1. No portal, abra Aplicações > Recursos para desenvolvedores > Cenários prontos > Outros > Webhook de entrada.
2. Marque só os escopos que a tarefa precisa (seção 7).
3. Copie o endereço. Ele tem o formato `https://PORTAL/rest/ID_DO_USUARIO/CODIGO/`.
4. Guarde numa variável de ambiente, e nunca cole no chat:

   ```
   export BITRIX24_WEBHOOK="https://PORTAL/rest/ID/CODIGO/"
   ```

   Depois, rode `python3 scripts/b24.py ping`.

**Se a opção não aparece,** o administrador libera em Configurações > Configurações do Bitrix24 > Segurança > Integrações do Bitrix24 > "Quem pode criar webhooks de entrada".

**O que saber:**
- **Ele age como o usuário que o criou,** dentro dos escopos marcados. A API nunca dá mais poder do que esse usuário tem na tela.
  - Para configurar (criar etapa, campo, iniciar processo), o usuário precisa ser administrador do CRM ou do portal.
  - Para integração permanente, crie o webhook em nome de um usuário técnico, e não de um funcionário: se o funcionário sai, tudo para.
- **O código só aparece para quem criou.** Se um administrador edita o webhook de outra pessoa, o código muda e ele vira o dono.
- **Pode ter data de expiração.** Vencido, dá erro de autorização. Na implantação, revogue o webhook no fim.
- **Só HTTPS.** Use POST com JSON, e GET só para teste rápido.
- **O webhook não alcança tudo.** Métodos que exigem contexto de aplicativo respondem `WRONG_AUTH_TYPE` ("Application context required") ou `ACCESS_DENIED`. Exemplos:
  - `event.bind` e `placement.bind`;
  - `bizproc.robot.*` e `bizproc.activity.*`;
  - `bizproc.workflow.template.add`;
  - `crm.automation.trigger.add/list/execute/delete`;
  - `telephony.externalCall.*`;
  - `biconnector.*`, fora os `*.fields`.

  Para esses, use o aplicativo local (seção 3).
- **Escopo faltando dá `insufficient_scope`.** Edite o webhook e marque o escopo.

## 2. O plano precisa ter API REST

Desde 01/09/2026, cada plano pago do Bitrix24 (Basic, Standard, Professional, Enterprise) existe em duas versões:
- **Essentials:** **sem API REST**, sem servidor MCP, com o Market limitado e com IA limitada.
- **Vibe+:** API REST, Market e IA ilimitados, mais o servidor MCP e o Vibecode.

**O erro de plano sem API:** `401 ACCESS_DENIED`, com "REST is available only on commercial plans" ou, pelo webhook, "REST is available only by subscription". O `b24.py` traduz esse erro.

**Para quem já pagava antes de setembro de 2026:**
- **Plano mensal ou trimestral:** tudo segue igual até 30/11/2026. Nessa data, quem não migrou para Vibe+ perde a API REST e o MCP.
- **Anual comprado ou renovado antes de 01/09/2026:** mantém as condições até o fim do período pago.
- **Anual que vence entre 01/09 e 30/11 e é renovado:** condições antigas só até 30/11/2026.

**A consequência para qualquer integração** (n8n, Make, código próprio, o próprio agente): ela depende do plano Vibe+ depois da transição. Antes de prometer automação, confira o plano. Os detalhes estão em references/planos-e-licencas.md.

## 3. Aplicativo local com OAuth

**Quando precisa:**
- receber eventos com `event.bind`, incluindo eventos offline;
- ter robô ou gatilho próprio na tela de automação;
- abrir aba no cartão ou item de menu (placement);
- ter um chatbot;
- importar processo de negócio (`bizproc.workflow.template.add`);
- instalar a mesma solução em vários portais.

**Como:**
- Registre em Aplicações > Recursos para desenvolvedores > Cenários prontos > Outros > Aplicativo local. Quem cria é um administrador, ou quem ele liberou.
- A chamada fica `https://PORTAL/rest/METODO` com `auth=ACCESS_TOKEN`.
- **Tokens:**
  - o `access_token` vale 1 hora, e o `refresh_token`, 180 dias;
  - renove em `https://oauth.bitrix.info/oauth/token/` com `grant_type=refresh_token`;
  - **renove só ao receber `expired_token` (401),** e não a cada chamada nem por agenda: renovar demais pode bloquear o app;
  - o `client_secret` vai só para `oauth.bitrix.info`, e nunca para o portal nem para o navegador.
- **O app age como o usuário dono do token,** dentro dos escopos do app.

## 4. Webhook de saída e eventos

Há dois jeitos de o portal avisar o seu sistema quando algo muda.

**a) Webhook de saída do portal** (eventos de criação, alteração e exclusão).
- **Onde criar:** em Cenários prontos > Outros > Webhook de saída, com a URL e o evento.
- **O que chega:** um POST `application/x-www-form-urlencoded` com `event`, `data[FIELDS][ID]`, `ts` e `auth`. O `auth` traz `domain`, `member_id` e `application_token`.
- **Valide `auth[application_token]`** contra o token mostrado na criação: é o que prova que veio do portal.
- **O evento só traz o ID.** Leia o objeto com `crm.item.get`.
- **Não há segunda tentativa.** Se o seu servidor cai ou responde erro, o evento se perde.
- **Limites:**
  - a URL precisa ser pública, sem localhost e sem SSL autoassinado;
  - não funciona em modo demonstração;
  - só eventos online: a fila offline exige aplicativo.
- **Eventos de Smart Process** (`ONCRMDYNAMICITEMADD`, `...UPDATE`, `...DELETE`) disparam só para Smart Process e faturas novas. Para Lead e Negócio, há os eventos próprios de cada entidade.

**b) A ação de webhook dentro de uma regra de automação** (por etapa).
- É o jeito mais usado para "quando o card entrar nesta etapa, chame meu fluxo".
- **Sempre POST,** com o contexto na URL (`?id={=Document:ID}`). O corpo traz `document_id[2]` (`DEAL_123`).
- **Não traz token de autenticação.** Proteja o caminho como segredo e confira o `domain`.

**Nos dois casos, ponha uma conferência periódica** que recupere o que se perdeu (references/automacao-externa.md).

## 5. Servidor MCP do portal e Vibecode

São três coisas diferentes, e não convém confundir.

- **MCP de dados do portal** (`https://mcp.bitrix24.com/mcp/`).
  - **O que faz:** deixa um assistente de IA agir no portal com as permissões do usuário: tarefas, negócios, calendário, estrutura, arquivos e chats.
  - **Como ligar:** o administrador liga em Configurações > Servidores MCP ("Permitir conexão de IAs externas ao Bitrix24"), que vem desligado.
  - **Como conectar:** por OAuth, ou por um token de conexão (Aplicações > Conexões MCP > Obter token), num conector MCP HTTP.
  - **Limites:** só no Vibe+. A lista oficial de ferramentas não estava publicada em outubro de 2026, e funis, campos personalizados e regras de automação não aparecem na cobertura declarada. Para configurar, a API REST continua sendo o caminho.
- **MCP de documentação** (`https://mcp-dev.bitrix24.com/mcp`, sem autenticação).
  - **O que faz:** busca métodos, eventos e artigos da documentação. Não lê nem altera dado.
  - **No Claude Code:** `claude mcp add --transport http b24-dev-mcp https://mcp-dev.bitrix24.com/mcp`.
  - Use para conferir um método antes de chamá-lo.
- **Vibecode e Vibe API** (`vibecode.bitrix24.com`, só no Vibe+).
  - **O que é:** uma API separada da REST, feita para agentes construírem e publicarem apps. Ela junta páginas e repete em erro temporário.
  - **Chaves:**
    - `vibe_api_...`: age como um usuário, como o webhook;
    - `vibe_app_...`: app com OAuth.

    Existe o modo `READONLY`, que bloqueia escrita com 403.
  - **Limite:** 300 requisições por minuto por chave.
  - **Cobrança:** à parte, em Vibe credits, para servidores, modelos e agentes.
  - **Para começar:** `GET https://vibecode.bitrix24.com/v1/me`, que mostra o que a chave pode.
  - **Há um MCP próprio** (pacote `@bitrix24/mcp-vibecode-api`), com ferramentas de leitura e escrita.

## 6. Sessão do navegador (avançado)

**Quando usar:** quando não há webhook e o usuário está logado no portal no próprio navegador, com ferramenta de navegador e autorização dele para cada ação.

**Como funciona:**
- Dentro da página logada, `BX.rest.callMethod` chama a REST como o usuário da sessão.
- `fetch('/rest/METODO.json?sessid=' + BX.bitrix_sessid(), {method: 'POST', body: JSON.stringify(params)})` também funciona.
- `BX.ajax.runAction` chama as ações internas da tela.

**Serve para o que a REST não alcança:**
- ler as regras de automação de uma etapa;
- ler e configurar o obrigatório por etapa;
- a API interna do BI Builder.

**Cuidados:**
- O agente nunca digita senha nem faz login pelo usuário.
- A saída do JavaScript na página pode ser cortada e bloqueada quando parece endereço com parâmetros (`chave=valor`). Devolva JSON e números.
- O estado da página some a cada navegação. Use uma aba só para isso.
- Notificação do sistema (`im.notify.system.add`) não funciona pela sessão (`WRONG_AUTH_TYPE`).

## 7. Escopos por tarefa

| Tarefa | Escopos |
|---|---|
| Ler e mudar o CRM | `crm` |
| Usuários e departamentos | `user` (ou `user_brief`), `department` |
| Tarefas | `task` (os antigos `tasks` e `tasks_extended` são obsoletos) |
| Avisos no sino e chat | `im` |
| Processos de negócio | `bizproc` |
| Campos de Smart Process | `userfieldconfig` |
| Arquivos | `disk` |
| Ligações e gravações | `telephony` |
| Produtos | `catalog` |

Comece pelo mínimo e acrescente quando aparecer `insufficient_scope`.

## 8. Guardar o segredo

- **O endereço do webhook é uma senha.** Qualquer um que o tenha lê e escreve no portal como aquele usuário.
- **Onde ele fica:** numa variável de ambiente da sessão ou num cofre de credenciais.
- **Onde ele nunca fica:**
  - no chat;
  - num arquivo do projeto;
  - num documento;
  - numa página publicada;
  - no código de um fluxo compartilhado.

  Em arquivo de contexto, use um marcador como `TOKEN_DO_WEBHOOK`.
- **Antes de um commit,** procure por `/rest/<número>/` e por tokens.
- **Vazou?** Gere outro no portal (editar o webhook troca o código) e atualize quem usa.
