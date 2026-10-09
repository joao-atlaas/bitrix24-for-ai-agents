# Automação externa: n8n, Make ou código próprio

As regras de automação do Bitrix24 resolvem muito: mudar responsável, criar tarefa, mandar e-mail, esperar um prazo. A automação externa entra quando a regra não alcança:
- relógio em horário útil e fila em rodízio;
- consulta a outro sistema e enriquecimento na web;
- IA que lê e escreve no card;
- mudança em lote.

O que segue é o padrão que aguenta produção.

## Sumário

1. O padrão: webhook na regra, conferência periódica e trava
2. Ler e escrever pelo n8n
3. Horário útil, filas e relógios
4. O que a automação escreve no card
5. Lista de "não contatar"
6. Mudança em lote com um fluxo temporário
7. Testar sem efeito colateral
8. Pegadinhas

## 1. O padrão: webhook na regra, conferência periódica e trava

**Como o evento chega:**
- Na regra de automação da etapa, use a ação de webhook de saída apontando para o seu endpoint, com o ID no endereço: `https://seu-servidor/caminho-secreto?id={=Document:ID}`.
- O Bitrix24 manda um POST em `application/x-www-form-urlencoded`, com `document_id[2]` no formato `LEAD_123` ou `DEAL_456`. Tire os não dígitos para ter o ID.
- A chamada da regra não traz token de autenticação, só `domain` e `member_id`. Proteja o caminho como segredo e confira o `domain`.
- Se, em vez da regra, você usar o webhook de saída do portal (por evento), ele traz `auth[application_token]`: confira contra o token mostrado na criação. Os dois não repetem o envio quando o seu servidor falha.

**Três cuidados que separam o fluxo que funciona do que perde evento:**
1. **A regra também dispara quando a etapa muda pela API**, inclusive pela sua própria automação. Se o seu fluxo muda a etapa, ele vai receber o evento de volta. Pense no laço antes de ligar.
2. **Webhook se perde.** Pode ser o portal no limite, o seu servidor fora do ar ou a fila cheia. Sempre ponha uma conferência periódica, a cada 15 a 30 minutos. Ela lê o histórico de etapas (`crm.stagehistory.list`) desde o último evento tratado e processa o que faltou.
3. **Cada evento é tratado uma vez só.** Guarde numa tabela o ID do evento (o ID do histórico de etapa, ou o ID do registro mais a etapa) antes de processar. Na reserva, vale o menor ID entre os vivos; a reserva velha (por exemplo, 15 minutos) é liberada; a tabela é limpa depois de alguns dias. Assim o webhook e a conferência não fazem o mesmo trabalho duas vezes.

**Responda 200 na hora** e processe depois. O portal não espera.

## 2. Ler e escrever pelo n8n

- **Credencial:** o endereço do webhook de entrada vai numa credencial ou num nó de configuração, e nunca no texto de um nó que se compartilha. Um app OAuth age como o usuário que o instalou.
- **Paginação:** no nó HTTP Request, use a paginação por resposta. O parâmetro `start` recebe `$response.body.next`, e a paginação para quando `next` não vier.
- **Lote:**
  - num nó Code, monte os comandos do `batch`, 50 por item;
  - mande para `batch.json` num HTTP Request, com 1 item a cada 600 ms;
  - no `batch`, a chave com sinal (`=ownerType`) precisa ser codificada.
- **O nó Code pode não ter rede,** conforme a instalação. Faça as chamadas nos nós HTTP, e não dentro do Code.
- **Fluxo em espera retoma com o código da versão em que começou.** Mudar o fluxo não muda as execuções que já estão esperando.

## 3. Horário útil, filas e relógios

- **Horário útil e feriados** ficam no código, com a lista de feriados até uma data definida, e alguém responsável por renovar. Fora do horário, o relógio para.
- **Fila em rodízio:**
  - uma lista de IDs de usuário e um ponteiro guardado;
  - cada entrada vai para o próximo da fila, com uma atividade de prazo curto;
  - sem resposta no prazo, a atividade fecha como não executada e o card passa para o próximo.
- **Relógio por atividade:** a atividade com prazo é o relógio que a pessoa vê. Os avisos (aos 10, 15, 30 minutos, por exemplo) vão pela notificação, e não por comentário.
- **Concluir antes de mover:** se a pessoa move o card antes de concluir a atividade, o fluxo perde a resposta. Escreva isso no treinamento.

## 4. O que a automação escreve no card

A linha do tempo cheia de comentário automático esconde o que as pessoas escreveram. A regra que funciona:

- **A automação escreve em dois lugares só:**
  1. **Uma ficha estruturada** num campo de texto (o Comentário do card, por exemplo), com rótulos fixos que a equipe completa: o que a empresa faz, com quem falar, o que motivou o contato, como está a qualificação.
  2. **Um comentário fixado na linha do tempo**, com seções (Empresa, Contato, Origem, Técnico, Atualizações). Cada fluxo completa o mesmo comentário, sem repetir linha e sem apagar o que já está lá, e fixa de novo.
- **O resto vai para o lugar próprio:**
  - data e link em campos;
  - tarefa e prazo em atividades;
  - alerta em notificação;
  - a mudança de etapa já fica no histórico.
- **IA que completa a ficha precisa de trava.** Ela só preenche linha vazia. Antes de gravar, o código confere que nenhuma linha antiga sumiu ou mudou; se mudou, não grava e anota o motivo.
- **Emoji de 4 bytes vira texto** em vários campos. Use símbolos simples (◆ ▶ ✓ ⏱).
- **Autoria:**
  - o comentário sai sempre como o dono do webhook ou do app, e o `AUTHOR_ID` é ignorado;
  - a tarefa aceita `CREATED_BY` de outra pessoa;
  - a notificação pessoal sai do dono do webhook, e a do sistema sai sem remetente.

  Para sair em nome de alguém, só com um webhook dessa pessoa.

## 5. Lista de "não contatar"

- **O que é a lista:** os próprios cards na etapa de perda, com o motivo "Não contatar".
- **Na entrada:** todo card novo com o mesmo telefone ou e-mail vai direto para perda com esse motivo (`crm.duplicate.findbycomm` na entrada).
- **Nunca exclua esses cards:** sem eles, o bloqueio some.

## 6. Mudança em lote com um fluxo temporário

Para mover etapa ou atualizar campo em centenas ou milhares de registros, um fluxo temporário é mais rápido e mais seguro que chamada por chamada.

**Os seis passos de references/modificar.md valem igual:**
1. ler os registros e as regras da etapa;
2. fazer o backup;
3. mostrar o plano e esperar o "pode";
4. testar em um registro;
5. rodar;
6. conferir.

O fluxo só substitui o passo 5:
1. Gatilho manual, e o nome começando com "TEMP ·" e a data.
2. Listar com paginação, montar os comandos e mandar em lotes.
3. Rodar, conferir o resultado lendo o portal e arquivar o fluxo.

Uma referência de escala: 372 atualizações em cerca de 16 segundos.

## 7. Testar sem efeito colateral

- Teste com dados fixos nos nós que tocam o mundo (Bitrix24, e-mail, WhatsApp, tabelas): no n8n, os dados fixados.
- Card de teste com "TESTE" no título, e nunca com telefone ou e-mail de cliente.
- Antes de testar mudança de etapa, leia as automações daquela etapa: o teste pode mandar mensagem de verdade.
- Depois do teste, o card de teste vai para uma etapa de encerramento, com a descrição "teste". Antes de mover, leia as regras dessa etapa (ir para perda também dispara automação), ou use uma etapa neutra sem regra. Excluir fica com quem administra o portal.

## 8. Pegadinhas

- **Criar dezenas de registros de uma vez estoura o limite** (QUERY_LIMIT_EXCEEDED): os webhooks de saída das regras falham na hora, e só a conferência periódica recupera. Espace as criações (1 a cada 2 ou 3 segundos).
- **Ir para perda ou converter fecha sozinho as atividades abertas**, com status de concluída e sem trocar o título, antes de o seu fluxo ver. Trate a atividade fechada no mesmo segundo da mudança de etapa como "fechada pelo sistema", e não como "respondida".
- **O histórico de etapas de Lead devolve `STATUS_ID`;** o de Negócio e de Smart Process devolve `STAGE_ID`.
- **`crm.timeline.item.pin` pode devolver `result: null` sem erro.** Confira lendo o comentário de volta.
- **`crm.timeline.comment.update` funciona dentro do `batch`** e mantém o comentário fixado.
