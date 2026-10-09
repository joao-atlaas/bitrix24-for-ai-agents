# Bitrix24 for AI Agents

[![Licença: CC BY 4.0](https://img.shields.io/badge/licen%C3%A7a-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/deed.pt_BR)

Uma skill para agentes de IA lerem, modificarem e configurarem um portal Bitrix24 com método e segurança. Funciona com o Claude Code, com o Claude.ai e com qualquer agente que leia arquivos e rode Python.

*A skill (in Portuguese) that teaches AI agents to read, change and configure Bitrix24 portals safely: read first, back up, show the plan and wait for approval, test on one record, apply in batches, verify, and know how to undo.*

## Por que ela existe

O Bitrix24 aceita quase tudo pela API REST, e é por isso que um agente pode causar estrago rápido:
- Mudar a etapa de 2 mil negócios dispara 2 mil vezes as automações daquela etapa, e algumas mandam mensagem ao cliente.
- A API responde "sucesso" e ignora a gravação em vários casos.
- Metade da configuração (regras de automação, obrigatório por etapa, permissões) nem aparece na API.

Esta skill dá ao agente o método de um consultor experiente:
1. lê o portal antes de mexer;
2. faz backup;
3. mostra o que vai mudar e espera o "pode";
4. testa em um registro;
5. aplica em lote;
6. confere o resultado real;
7. sabe desfazer.

## O que o agente passa a fazer

Exemplos de pedidos que a skill resolve:

| Pedido | O que o agente faz |
|---|---|
| "Quantos negócios estão parados há mais de 60 dias, por vendedor?" | Mapeia o portal, lê com o critério certo (a última mudança de etapa, na hora do servidor) e responde com o critério escrito, a tabela e os links |
| "Move para Perdido os negócios parados com o motivo Sem retorno" | Lê os registros e as automações da etapa de destino, faz backup, monta o lote de teste, o lote principal e o de desfazer, e para com a pergunta "posso aplicar?" |
| "Cria um campo de lista e deixa obrigatório a partir da etapa Proposta" | Separa o que dá pela API (o campo) do que só dá pela tela (o obrigatório por etapa e as regras) e entrega o passo a passo da tela |
| "Exporta todos os contatos com telefone" | Pagina do jeito que a documentação recomenda para volume e entrega um CSV que abre certo no Excel |
| "Monta um painel de conversão no BI Builder" | Avisa os limites estruturais antes de prometer, como o responsável sem histórico e o card que muda de funil, e desenha o dataset certo |
| "Liga o Bitrix24 ao n8n para avisar quando o lead entrar em tal etapa" | Usa o padrão que aguenta produção: webhook na regra da etapa, conferência periódica e trava contra processar duas vezes |
| "O que muda para nós com os planos Essentials e Vibe+?" | Explica o que muda para a API, para a IA e para as integrações, e como explicar a mudança ao dono da empresa |

## O que tem dentro

```
bitrix24-for-ai-agents/
├── SKILL.md                         as regras fixas, os três modos de trabalho e o mapa das referências
├── LICENSE.txt                      CC BY 4.0
├── references/
│   ├── acesso.md                    webhook, app OAuth, eventos, MCP do portal, Vibecode, navegador, escopos
│   ├── modelo-de-dados.md           entidades, funis, etapas, campos, multicampos, vínculos, histórico
│   ├── ler.md                       filtros, mapa do portal, listas grandes, receitas, o que a API não mostra
│   ├── modificar.md                 o protocolo de seis passos, efeitos colaterais, receitas, lote, desfazer
│   ├── configurar.md                o método de implantação e o que é API e o que é tela
│   ├── automacao-externa.md         n8n, Make ou código: o padrão que aguenta produção
│   ├── bi-builder.md                Superset e Trino sobre o CRM: limites, SQL, dataset, painéis
│   ├── planos-e-licencas.md         Essentials e Vibe+ para a API, e como explicar a mudança ao dono
│   └── pegadinhas.md                a lista de conferência antes de entregar
├── scripts/
│   ├── b24.py                       cliente da API REST: ping, fields, call, list, backup, batch
│   ├── restaurar.py                 monta o lote que desfaz uma alteração, a partir do backup
│   └── bpt.py                       lê e grava os modelos de processo de negócio (.bpt)
└── assets/
    └── registro-de-configuracao.md  modelo para documentar a configuração de um portal
testes/
├── teste_b24.py                     27 testes dos scripts contra um portal simulado
└── portal_simulado.py               um portal Bitrix24 de mentira para testar a skill com agentes
```

## Requisitos

- **Python 3.** Os scripts usam só a biblioteca padrão, sem pip.
- **Um portal com API REST.** Desde 01/09/2026, a API REST só vem nos planos **Vibe+**; os planos **Essentials** não têm.
  - Planos mensais e trimestrais antigos perdem a API em 30/11/2026 se não migrarem.
  - Sem a API, a skill ainda orienta o trabalho pela tela, mas não lê nem grava sozinha.
- **Um webhook de entrada do portal,** criado por um usuário com as permissões que a tarefa pede. Para configurar (funil, etapa, campo), esse usuário precisa ser administrador do CRM.

## Instalação

**Claude Code, só para você:**

```
git clone https://github.com/joao-atlaas/bitrix24-for-ai-agents.git
cp -r bitrix24-for-ai-agents/bitrix24-for-ai-agents ~/.claude/skills/
```

**Claude Code, para a equipe:** copie a pasta `bitrix24-for-ai-agents/` para `.claude/skills/` do repositório do projeto.

**Claude.ai:**
1. Baixe o `.zip` da página de [Releases](https://github.com/joao-atlaas/bitrix24-for-ai-agents/releases).
2. Em Configurações > Capacidades, ligue "Execução de código e criação de arquivos".
3. Em Personalizar > Skills, envie o `.zip`.

**Outros agentes** (Codex, Cursor e afins): aponte o agente para o `SKILL.md` e deixe que ele rode os scripts da pasta `scripts/`.

## Primeiros passos

1. **Crie o webhook de entrada no portal:**
   - abra Aplicações > Recursos para desenvolvedores > Cenários prontos > Outros > Webhook de entrada;
   - marque os escopos que a tarefa precisa (`crm` para começar);
   - copie o endereço.

   Se a opção não aparecer, o administrador libera em Configurações > Segurança > "Quem pode criar webhooks de entrada".
2. **Guarde o endereço numa variável de ambiente,** e nunca no chat nem num arquivo:

   ```
   export BITRIX24_WEBHOOK="https://SEU-PORTAL.bitrix24.com.br/rest/ID/CODIGO/"
   ```

3. **Confira a conexão:**

   ```
   python3 scripts/b24.py ping
   ```

   Ele mostra o usuário do webhook, o fuso, os escopos e a hora do servidor.
4. **Peça em linguagem natural.** Por exemplo: "faz o mapa do meu portal Bitrix24" ou "quantos leads entraram este mês por origem?". A skill entra sozinha quando o assunto é Bitrix24.

## Segurança

- **O script não grava sem permissão.**
  - Todo método fora da lista de leitura exige `--confirmar`, e exclusão exige também `--confirmar-exclusao`.
  - A lista de leitura é de permissão, e não de bloqueio: método desconhecido é tratado como escrita, e os poucos "get" que criam algo (como link público) também.
  - No lote, vale o nome de cada método, e não o que vem nos parâmetros.
- **Escrita não é repetida depois de timeout ou erro sem código,** porque ela pode já ter sido aplicada: o script para e pede para conferir no portal. Isso evita registro e aviso duplicados.
- **O endereço do webhook nunca é impresso.** Nas mensagens de erro, ele sai mascarado.
- **O script respeita os limites do portal:**
  - 2 chamadas por segundo, em lotes de até 50;
  - espera crescente no `QUERY_LIMIT_EXCEEDED`;
  - espera pela janela do método no `OPERATION_TIME_LIMIT`;
  - parada imediata no `OVERLOAD_LIMIT`.
- **Backup sem meio-termo:** se a leitura falhar no meio, não fica um arquivo pela metade que pareça completo.
- **A skill manda o agente:**
  - ler as automações da etapa antes de mover registros;
  - avisar o que não volta num desfazer (mensagens enviadas, atividades fechadas);
  - nunca excluir sem pedido explícito;
  - manter o dado do cliente fora de controle de versão.

## Os scripts

```
# conexão, campos e uma chamada
python3 scripts/b24.py ping
python3 scripts/b24.py fields deal
python3 scripts/b24.py call crm.deal.get '{"id": 123}'

# lista inteira e backup (JSON Lines, um registro por linha)
python3 scripts/b24.py list crm.deal.list '{"filter": {"CATEGORY_ID": 0}, "select": ["ID","TITLE","STAGE_ID"]}' --saida negocios.jsonl
python3 scripts/b24.py backup crm.deal.list '{"filter": {"@ID": [101, 102]}, "select": ["ID","STAGE_ID"]}' --saida backup.jsonl

# lote de até 50 comandos por chamada (arquivo {"chave": ["metodo", {params}]})
python3 scripts/b24.py batch comandos.json --confirmar

# desfazer a partir do backup
python3 scripts/restaurar.py backup.jsonl --metodo crm.deal.update --campos STAGE_ID --ids 101,102 --saida desfazer.json
python3 scripts/b24.py batch desfazer.json --confirmar

# processos de negócio exportados (.bpt)
python3 scripts/bpt.py confere processo.bpt     # a ida e volta reproduz o arquivo? só então edite por código
python3 scripts/bpt.py resumo processo.bpt
python3 scripts/bpt.py json processo.bpt > processo.json
python3 scripts/bpt.py bpt processo.json processo-novo.bpt
```

## Testes

```
python3 testes/teste_b24.py
```

**O que os testes cobrem:**
- paginação comum e por ID;
- batch com chaves codificadas;
- bloqueio de escrita e de exclusão;
- espera no limite de taxa;
- máscara do webhook;
- mensagem de plano sem API;
- backup que falha;
- o ciclo de backup, desfazer e lote;
- escrita disfarçada de leitura;
- escrita que não se repete depois de erro.

Tudo roda contra um portal simulado, sem rede.

**Para testar a skill com um agente,** suba o portal simulado e aponte o webhook para ele:

```
python3 testes/portal_simulado.py 8765
export BITRIX24_WEBHOOK="http://127.0.0.1:8765/rest/1/codigoSecreto123/"
```

## O que ela não faz

- **Não cria nem lê as regras de automação padrão pela API**, porque o Bitrix24 não expõe isso. Ela orienta pela tela, ou lê pelo navegador do usuário com autorização dele.
- **Não configura permissões, máscara de campo nem o obrigatório por etapa pela API.** Esses só existem na tela.
- **Não monta painel do BI Builder por API oficial,** porque ela não existe. A referência mostra o caminho pela API interna, com a sessão do navegador.
- **Não trabalha sozinha em portal Essentials,** que não tem API REST.

## Fontes

Escrita a partir de implantações reais de Bitrix24 em vários segmentos: imobiliária, seguros, indústria, contabilidade, administração de condomínios, construção, saúde e crédito. Nenhum dado de cliente entrou: só o método e as pegadinhas.

Os fatos de API foram conferidos na documentação oficial ([apidocs.bitrix24.com](https://apidocs.bitrix24.com) e [helpdesk.bitrix24.com](https://helpdesk.bitrix24.com)) em outubro de 2026. O Bitrix24 muda: quando a documentação disser outra coisa, vale a documentação. Avise por uma issue.

## Licença e créditos

**[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt_BR):** você pode usar, copiar, adaptar e redistribuir, inclusive para fins comerciais, desde que dê o crédito ao autor.

**Como dar o crédito,** em qualquer cópia ou adaptação:

> Bitrix24 for AI Agents, de João Paulo, Atlaas Tecnologia ([atlaas.com.br](https://atlaas.com.br)). Licença CC BY 4.0. Original em github.com/joao-atlaas/bitrix24-for-ai-agents.

Se você mudou alguma coisa, diga que é uma versão adaptada.

## Precisa de ajuda com o Bitrix24?

A skill dá o método. Quando o trabalho pede gente experiente do lado, a **Atlaas Tecnologia** é parceira oficial do Bitrix24 (selo Gold), com mais de 300 empresas atendidas e mais de 80 projetos de Bitrix24. A Atlaas implanta, migra, integra, treina a equipe e acompanha:
- funis;
- automações;
- integração com ERP e WhatsApp;
- BI;
- agentes de IA dentro do Bitrix24.

- Bitrix24 com a Atlaas: [atlaas.com.br/bitrix24](https://atlaas.com.br/bitrix24)
- Falar com a equipe: [atlaas.com.br/contato](https://atlaas.com.br/contato)

## Contribuir

Achou uma pegadinha nova, um método que mudou ou um erro? Abra uma issue ou um pull request.

Nada de dado de cliente nem de endereço de webhook nos exemplos: use nomes genéricos.
