# Planos e licenças: Essentials e Vibe+

Duas partes:
- **O que o plano muda para um agente de IA:** se a API existe, se dá para ligar automação, se o MCP está disponível.
- **Como explicar a mudança ao dono da empresa.**

Fatos conferidos nas páginas oficiais em outubro de 2026. Preço e prazo mudam: confira na página oficial de preços (bitrix24.com/prices) antes de citar um número.

## 1. O que mudou em 2026

Desde 01/09/2026, cada plano pago (Basic, Standard, Professional, Enterprise) existe em duas versões.

| | Essentials | Vibe+ |
|---|---|---|
| API REST (webhook, app local, n8n, Make, integrações próprias) | **Não tem** | Ilimitada |
| Servidor MCP (assistente de IA agindo no portal) | Não tem | Tem |
| Vibecode e Vibe API (apps feitos por agentes) | Não tem | Tem (com cobrança de uso à parte) |
| Bitrix24 Market | Limite de apps por plano, crescente do Basic ao Enterprise | Ilimitado |
| IA do dia a dia (transcrição, preencher campo, resumo) | Cota diária por usuário | Maior no Basic, ilimitada do Standard para cima |

**O que continua no Essentials:** a telefonia própria, o conector SIP, as integrações nativas do Bitrix24 e os apps gratuitos do próprio Bitrix24, que não contam no limite do Market.

**Transição para quem já era cliente:**
- **Mensal ou trimestral:** tudo igual até 30/11/2026. Nessa data, quem não migrar para Vibe+ fica com os limites do Essentials, ou seja, sem REST e sem MCP.
- **Anual comprado ou renovado antes de 01/09/2026:** mantém as condições até o fim do período pago.
- **Anual que venceu entre 01/09 e 30/11 e foi renovado:** condições antigas só até 30/11/2026.

## 2. O que isso muda para o agente

**Antes de propor qualquer automação, descubra o plano:**
- **Pelo usuário:** em Configurações > Plano.
- **Pelo erro da API:** `ACCESS_DENIED` com "REST is available only by subscription".

**Se o portal é Essentials, ou vai ser depois da transição, o agente não tem API.** Sobram três caminhos:
1. Migrar para Vibe+. É uma decisão do dono, com o custo na mesa.
2. Fazer pela tela, com o usuário: o agente guia passo a passo, ou age no navegador dele com autorização.
3. Ficar no que é nativo: regras de automação, gatilhos e integrações do próprio Bitrix24.

**O gatilho "Webhook" da automação continua no Essentials.**
- Na tela de regras, o gatilho de webhook de entrada gera uma URL pronta, que chama `crm.automation.trigger` com o `target` e o `code`.
- Ela só move o card pela regra, sem tirar nem pôr dado.
- Os métodos `crm.automation.trigger.add` e `.execute` são outra coisa: gatilhos próprios de aplicativo, que exigem contexto de app.

**Integração existente (n8n, Make, sistema próprio) num plano mensal ou trimestral Essentials para de funcionar em 30/11/2026.** Avise o usuário se encontrar esse cenário: é o tipo de coisa que quebra a operação sem ninguém perceber até o primeiro lead não chegar.

## 3. Como explicar a mudança ao dono da empresa

Só com o que é público. Preço, promoção e condições comerciais mudam e variam por mercado: leia na página de preços oficial, ou com o parceiro Bitrix24 de quem o cliente compra, antes de citar qualquer número.

**Comece pelo que muda na operação, e não pelo preço.**
- A pergunta que importa: "alguma coisa da empresa depende da API?" Integração com ERP, site, n8n ou Make, WhatsApp por app, robô próprio, BI externo ou um assistente de IA que mexe no CRM.
- **Se depende,** o plano precisa ser Vibe+. No mensal ou trimestral, decida antes de 30/11/2026, e não depois que a integração parar.
- **Se não depende** (time pequeno, CRM, tarefas e telefonia do próprio Bitrix24), o Essentials atende. Dizer isso gera confiança.

**Três perguntas que mostram se o Vibe+ faz sentido.** Um "sim" em qualquer uma é a conversa:
1. "Vocês gastam tempo com tarefa manual repetida que a IA poderia fazer?"
2. "Tem algum processo que nenhum sistema pronto atendeu direito?"
3. "Vocês já usam o ChatGPT ou o Claude e queriam que eles mexessem direto no CRM?"

**Dúvidas comuns:**

| O cliente diz | A resposta |
|---|---|
| "O que muda para mim?" | Se nada da empresa usa a API, nada muda no Essentials. Se usa, ela só continua no Vibe+ |
| "Não usamos integração. Por que pagar mais?" | Então o Essentials é o certo: a telefonia, o SIP, as integrações nativas e o gatilho por webhook da automação continuam |
| "O limite de apps vai quebrar algo?" | Os apps gratuitos do próprio Bitrix24 não contam no limite. Confira quantos apps pagos estão instalados e quais ainda são usados |
| "Quando isso me afeta?" | Depende do ciclo de pagamento (seção 1). No mensal e no trimestral, a data é 30/11/2026 |
| "A IA vai ficar limitada?" | O Essentials tem uma cota diária por usuário para o uso do dia a dia. O Vibe+ amplia, e libera a IA do Standard para cima |

**Cuidados:**
- **Não chame de aumento de preço:** o Essentials não muda para o que o cliente já tem. O Vibe+ é uma camada com capacidade nova.
- **Diga "Bitrix24 Market"** (e não "Marketplace") e "MCP server".
- **O plano instalado no servidor do cliente (on-premise) é outra linha de produto.** Não misture com Essentials e Vibe+.
- **Produto anunciado e ainda não lançado:** fale só do que já está na página oficial.
