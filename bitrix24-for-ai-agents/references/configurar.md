# Configurar um portal Bitrix24

O método de implantação, tirado de projetos reais em imobiliária, corretora de seguros, indústria, contabilidade, administradora de condomínios, construtora, clínica e instituição financeira. São regras que já custaram retrabalho para serem aprendidas.

**Sobre fuso:** vários números abaixo vêm de portais com servidor em UTC+3 e usuários em UTC-3, uma diferença de 6 h. Confira o fuso do seu portal (`server.time` e o fuso do perfil do usuário) antes de copiar qualquer deslocamento.

## Sumário

1. Como conduzir uma implantação
2. Descoberta e desenho
3. Escolher a estrutura: Lead, Negócio ou Smart Process
4. Funis e etapas
5. Campos
6. Obrigatório por etapa
7. Robôs, gatilhos e processos de negócio
8. O que a API faz e o que só a tela faz
9. Validar, ativar e desfazer
10. Registrar

## 1. Como conduzir uma implantação

- **Levantamento só leitura antes de tudo.**
  - **O que ler:** plano e limites, administradores, funis, etapas, campos, Smart Processes, automações, dados existentes, idioma, fuso, moeda, horário de trabalho, feriados, apps, webhooks, Drive e grupos.
  - **Por quê:** o desenho se adapta ao que já existe.
- **Ciclo fixo por parte:**
  1. plano escrito, com o portal só em leitura;
  2. aprovação explícita do dono do projeto;
  3. execução;
  4. testes com registros [TESTE];
  5. documentação;
  6. relatório.

  Nada roda antes da aprovação.
- **"Só leitura" é literal.** Se o pedido é análise, nenhuma chamada de escrita, nem de teste.
- **Fidelidade ao material do cliente.**
  - Configure só o que o material define (apresentação, procedimento, desenho do funil).
  - Não renomeie etapa e não invente opção de lista, peso ou regra.
  - O que falta vira pergunta, e a configuração fica provisória até a resposta.
- **Não mexer no que já existe.**
  - Funis, campos, robôs e registros do cliente ficam intactos.
  - O novo nasce em paralelo, é mostrado e só depois o antigo sai.
  - Depois de configurar, confira que os cartões dos funis antigos não ganharam os campos novos.
- **Nenhum convite durante a construção.**
  - Cadastrar usuário (`user.add`) já dispara o convite.
  - Use a conta de administrador como responsável provisório.
  - Liste cada troca para o "dia dos convites": aprovadores, destinatários de avisos, responsáveis por etapa, chefes, perfis de acesso, remoção dos [TESTE] e revogação do webhook.
- **Nada sai do portal durante a implantação.**
  - Sem e-mail, SMS, link público ou assinatura para fora.
  - Contatos de teste sem e-mail e sem telefone.
  - Automações de envio nascem desligadas.
- **Sem integração na primeira onda.**
  - O passo feito no ERP continua manual. No Bitrix24 fica o controle: a etapa ou o item de checklist que confirma o passo, com o número de referência (pedido, NF).
  - Anote cada um como candidato a integração.

## 2. Descoberta e desenho

- **Cada passo do procedimento vira um controle:**
  - cada atividade vira etapa, tarefa, item de checklist, aprovação, campo obrigatório, anexo ou prazo;
  - cada desvio vira uma pergunta com critério escrito;
  - cada evento de tempo vira prazo e automação, com aviso e escalonamento;
  - cada saída para outro processo vira uma ligação, ou uma ponte provisória.

  **Critério de aceite:** o dono percorre o processo de ponta a ponta no portal, com dado real.
- **Agrupe processos em ondas**, nesta ordem:
  - mesma estrutura vai junto;
  - cadeia contínua (o fim de um é o gatilho do outro) vai junto;
  - mesma equipe vai junto;
  - quem cria o registro-pai entra antes;
  - pontos de convergência (compras, fiscal) entram depois de quem os alimenta.
- **Ponte provisória.** A saída para um processo ainda não implantado vira tarefa para a área de destino. Quando o destino entrar, a ponte vira ligação de verdade.
- **Perguntas ao cliente:** numa conversa rápida, uma pergunta por vez. Num projeto de configuração, junte as decisões numa lista:
  - com código estável (D1, D2, ou F-01, C-01);
  - uma coisa por pergunta, com uma sugestão de resposta;
  - as decisões numa lista única, usada por todas as entregas.
- **Pedido de mudança se avalia antes de fazer.**
  - Liste as divergências numeradas (D1, D2), e o cliente responde item a item.
  - Pedido de parecer recebe parecer, e não plano de execução.
- **Não afirme capacidade sem conferir.**
  - Todo método, campo, limite ou recurso é conferido na documentação ou num teste antes de entrar no plano.
  - No comparativo de planos, anote de qual coluna saiu o número. Já houve limite lido na coluna do plano gratuito.
- **Portal herdado: diagnóstico.**
  - Meça o volume.
  - Procure:
    - campos com rótulo repetido (até três campos para o mesmo dado);
    - funis e Smart Processes sem uso;
    - formulários antigos ativos;
    - processos de negócio parados há anos;
    - negócios sem atualização há mais de 90 dias;
    - tarefas vencidas;
    - nomes de usuário fora do padrão, que contaminam relatório por pessoa.
- **Herança de outro parceiro:**
  - Inventarie no painel webhooks, aplicativos, handlers de evento e placements antes de qualquer corte. Desinstalar um app apaga os handlers dele sem aviso, e o webhook de entrada não consegue listar nada disso.
  - Peça ao parceiro: o IP de saída, as URLs de callback cadastradas nos fornecedores, o código, o dump do banco e o usuário com que as rotinas gravam. O banco dele costuma guardar a correlação entre ID externo e ID do Bitrix24, que não se reconstrói.
  - Rotacione as chaves só depois da reimplantação validada.
- **Migração: audite a base antes de prometer prazo.**
  - O esforço depende da qualidade, e não do volume.
  - Audite:
    - a completude contra a contagem prévia;
    - a integridade (o dono e o pai de cada registro existem);
    - as datas e o fuso, os anexos e o histórico;
    - a duplicidade e a chave estável.
  - Classifique cada bloco:
    - verde: carga direta;
    - amarelo: carga com tratamento declarado;
    - vermelho: fora do cronograma automático.
- **Importação de carteira:**
  - compare com o que já existe e faça o relatório dos registros sem correspondência;
  - os órfãos vão para um responsável de reserva definido;
  - no fim, conte por responsável.

## 3. Escolher a estrutura: Lead, Negócio ou Smart Process

- **Lead** quando há qualificação antes da venda (marketing, MQL). A conversão nativa cria o negócio.
- **Negócio** para o fluxo comercial: venda e renovação, um funil (categoria) por processo comercial.
- **Smart Process (SPA)** quando o objeto tem ciclo próprio e não é venda: obra, contrato, apólice, colaborador, chamado.
  - A carteira fica numa SPA separada do funil ativo.
  - Os processos de bastidor (endosso, cancelamento, inadimplência) viram funis de uma mesma SPA.
- **Registro não é usuário.** Colaborador, por exemplo, é item de SPA, e não usuário do portal: evita convite e licença.
- **Uma SPA, vários funis, um cartão por funil.** Cada funil com o próprio layout: o usuário vê só os campos do módulo em que está.
- **Unifique automações por tipo.** Em vez de N funis quase iguais, use:
  - uma etapa;
  - um campo de lista "Tipo";
  - um robô com ramos por tipo.
- **Mover o mesmo card entre funis.** Dentro da mesma entidade, `crm.item.update` com `categoryId` e `stageId` leva o card inteiro: vínculos, histórico e tarefas. É melhor que criar cópia.
- **Supervisor é o chefe do departamento.**
  - "Gerente" nos fluxos é o chefe do departamento do responsável, subindo na estrutura até achar alguém diferente do próprio responsável. Não crie campo "Supervisor".
  - Uma conta técnica do sistema pode estar como chefe e receber tarefas. Corrigir a estrutura é pré-requisito de robô por chefe e de permissão.
- **Fundação antes dos processos.** Ela é a base de todo prazo em dias úteis:
  - departamentos;
  - empresas próprias e moeda base;
  - calendário, com fim de semana e feriados nacionais, locais e móveis. O padrão pode vir com feriados de outro país;
  - horário de trabalho.

**Um desenho de Kanban de Leads que funciona** (exemplo de time de pré-vendas):
- **Poucas etapas, cada uma com um dono e uma saída clara:** por exemplo, entrada, pesquisa, tentativa de contato, conversa com quem decide, reunião marcada, convertido e perdido.
- **Poucos campos personalizados:**
  - a data da reunião, obrigatória só na etapa de reunião;
  - o motivo de perda e a descrição, obrigatórios na perda.
- **Motivos de perda genéricos e fechados**, com "Outro (descrever)". "Não contatar" vira a lista de bloqueio (references/automacao-externa.md, seção 5).
- **A linha do tempo é das pessoas.** A automação escreve numa ficha e num comentário fixado (references/automacao-externa.md, seção 4).

## 4. Funis e etapas

- **Etapa de passagem.** Uma etapa "Enviar para X" funciona como gatilho manual: o robô dela chama o fluxo externo que move o card.
- **Etapa neutra antes de limpar.** Mover cards para uma etapa com automação ativa dispara os robôs dela. Para limpeza e carga, crie uma etapa sem robô.
- **Etapa de entrada para importados.**
  - A importação por CSV não liga o item ao pai, não dispara regras e respeita os obrigatórios por etapa.
  - Crie uma etapa "Nova (conferir)" e um campo com a referência do pai. Uma regra na etapa seguinte faz o vínculo.
- **Perda com motivo que decide a etapa.**
  - Duas etapas de perda (por exemplo, nutrição e descarte), e a lista de motivos decide para qual vai.
  - Motivo obrigatório só na perda. Onde a regra preenche o motivo sozinha, não exija.
- **Aprovação sem o módulo de RPA.** A ação "Aprovar ou recusar" é exclusiva do RPA. O padrão nativo que funcionou:
  1. Campos "Decisão" (lista: Aprovado, Recusado) e "Comentário" no cartão.
  2. Ao entrar na etapa, uma atividade para o aprovador e um aviso de prazo se a decisão seguir vazia.
  3. Um gatilho de campo move o item: aprovado avança, recusado volta (permita a volta no gatilho).
  4. As regras da etapa de destino gravam a decisão no histórico e limpam os campos para o próximo ciclo.

  **Para alçada por valor e delegação:** use processo de negócio. Na nuvem, o limite é de 2 processos simultâneos por item.
- **Campo "Dados completos" para item que já nasce pronto.** Gatilho só reage a alteração, então o item criado já preenchido não anda. A primeira etapa marca um campo de controle, e o gatilho observa esse campo.
- **Contadores e carimbos para indicador.**
  - Regras somam as voltas (reprovações) e gravam as datas de marco.
  - Para a data de conclusão, use a hora da última mudança de etapa (`MOVED_TIME`), sem criar campo.
- **Campos técnicos** para estado de integração: ID externo, assinatura do último envio, JSON de sincronia. Ficam fora da lista e do cartão (`SHOW_IN_LIST = N`), com "(técnico)" no rótulo.
- **O kanban não pinta o card por campo.** Mostre o status com um símbolo num campo visível e crie filtros salvos ("Atrasados", "Críticos").
- **Etapa final encerra pendências.** Ao chegar numa etapa final (ganho ou perda), o Bitrix24 encerra as atividades e tarefas abertas do item, sem opção de desligar. A tarefa que precisa continuar aberta é criada na própria etapa final.
- **Smart Process sem funis.** Com `isCategoriesEnabled = N`, `crm.category.add` devolve `ENTITY_TYPE_NOT_SUPPORTED`: ligue os funis antes.
- **Funil nasce sem acesso.** Com `isSetOpenPermissions = N`, o funil novo nasce sem acesso para a equipe. Permissão por funil é decisão do cliente e se configura na tela.
- **Ordem das etapas.** Não dá para criar etapa com ordem maior que a da etapa final. Crie ou reordene as finais primeiro.
- **Funil de negócio com ID de dois dígitos.** O código da etapa padrão sai truncado (por exemplo, `C10:PREPAYMENT_INVOIC`). Scripts precisam reconhecer o caso. Remova as etapas padrão que sobram antes de existir item no funil.

## 5. Campos

- **Antes de criar um campo, procure um que já guarde o dado:**
  - entre os nativos (`SOURCE_ID` é a origem, `TYPE_ID` o tipo, `COMMENTS` o comentário);
  - entre os personalizados, inclusive os de rótulo parecido.

  Campo duplicado é a doença mais comum de portal antigo.
- **Nome do código:** siga o padrão que o portal já usa. Sem padrão, um prefixo por projeto (`UF_CRM_<PROJETO>_<NOME>`) facilita achar e filtrar.
- **Criar campo de lista no CRM clássico** (Lead, Negócio, Contato, Empresa):

  ```json
  crm.deal.userfield.add {"fields": {
    "FIELD_NAME": "ORIGEM_LEAD", "USER_TYPE_ID": "enumeration", "MULTIPLE": "N",
    "EDIT_FORM_LABEL": {"br": "Origem do lead", "en": "Lead source"},
    "LIST_COLUMN_LABEL": {"br": "Origem do lead"}, "LIST_FILTER_LABEL": {"br": "Origem do lead"},
    "SHOW_FILTER": "Y",
    "LIST": [{"VALUE": "Site", "XML_ID": "SITE", "SORT": 10},
             {"VALUE": "Indicação", "XML_ID": "INDICACAO", "SORT": 20}]}}
  ```

  - O prefixo `UF_CRM_` entra sozinho.
  - As chaves de idioma dos rótulos (`br`, `en`...) copie de um campo que já existe no portal.
  - Depois de criar, releia com `crm.deal.userfield.list` para pegar os IDs das opções.
- **Lista com código legível.** Defina um `XML_ID` explícito em cada opção ao criar (`APROVADO`, `VIAVEL`).
  - As condições e gravações de robô usam o código.
  - A REST usa o ID numérico.
  - Com o ID num robô, a condição nunca é verdadeira e o campo fica vazio.
- **O campo é da entidade, e não do funil.**
  - O campo novo aparece para todos os funis. Aplique o layout explicitamente nos funis antigos e confira.
  - Reaproveite um campo existente quando o rótulo serve aos dois.
- **Texto livre com variações vira lista:** faça o de-para nos registros abertos e o relatório dos não mapeados. Opção "Outra" mais um campo de texto. "Outra exige o nome" não é nativo: valide por fora.
- **Regras de criação:**
  - O booleano de Smart Process só aceita `Y` e `N`; 1 ou 0 grava `N` em silêncio.
  - O decimal sem `settings.PRECISION` nasce com zero casas.
  - `multiple` não muda depois de criado.
  - Nome de campo com dígito no fim quebra a chave camelCase da API: prefira nomes por extenso.
  - Arquivo obrigatório num formulário de entrada trava a criação de qualquer item: nunca exija anexo na primeira etapa.
- **Campo de Smart Process:** o `typeId` não é o `entityTypeId`.
  - `userfieldconfig.add` usa `entityId: CRM_{typeId}` e um `fieldName` começando com `UF_CRM_{typeId}_`.
  - Com o `entityTypeId`, o erro é "You are not allowed to create custom fields".
- **Opções de lista depois de criado.**
  - `userfieldconfig.update` só com as opções novas é ignorado sem erro.
  - O que funcionou: mandar o campo inteiro, com as opções antigas acompanhadas do `id`.
  - Na criação, as opções vão no parâmetro `enum`.
  - Se não persistir, crie pela tela.
- **Máscara de campo** (`SETTINGS.REGEXP`) é ignorada pela API: só pela tela.
- **Módulo Listas** serve como tabela de referência (cargos, catálogos).
  - `lists.element.update` apaga as propriedades não reenviadas: mande todas.
  - Sem código único, `lists.element.add` falha com "Element already exists".

## 6. Obrigatório por etapa

- **Como funciona:**
  - Vale da etapa indicada em diante, até o ganho, salvo nas perdas.
  - Trava o cartão: o item que pula etapas não salva se o campo é exigido onde ele está.
  - A checagem é feita no cartão e no kanban. **A mudança por gatilho ou pela API não passa por ela.**
- **Não vem no `.fields` da API.** Para ler, abra o cartão e leia a configuração do editor (references/ler.md, seção 7).
- **Configure só na ativação.** Antes, ele trava a equipe durante a validação.
- **Automatize primeiro, valide, e só então torne obrigatório:** campo obrigatório sem automação vira buraco no BI e atrito na equipe.
- **Obrigatório herdado atrapalha carga.** Se o cliente já exige um campo em todas as etapas, os registros importados sem ele pedem o campo em qualquer edição. Avise antes.

## 7. Robôs, gatilhos e processos de negócio

### Ler e documentar

- **A REST não lista os robôs de etapa.**
  - `bizproc.robot.list` só traz robôs de aplicativo.
  - `bizproc.workflow.template.list` só traz os processos clássicos.
  - **Dois caminhos para ler:**
    - a página de automação do funil, no navegador logado. No HTML do iframe, cada `DOCUMENT_STATUS` vem seguido dos robôs da etapa em JSON (`Type`, `Properties`, `Activated`);
    - exportar o modelo (`.bpt`) e ler com `scripts/bpt.py resumo`.
- **Documente em tabela por etapa:** os robôs (o que fazem, quando, condição), os gatilhos que trazem o item e o que já era do cliente (modelo em assets/registro-de-configuracao.md).

### Gravar

- **Robô nativo não se grava pela REST** (`bizproc.robot.add` é para robô de aplicativo). Os caminhos que funcionaram:
  - o designer, à mão, ou com o usuário guiado passo a passo;
  - no navegador logado e com autorização, a API JavaScript do editor (`Robot.copyTo`, `setProperty`, `setDelayInterval`, `setCondition`), conferindo com a página recarregada;
  - a rotina de gravação da própria tela: no componente `BX.Bizproc.Automation.Designer.getInstance().component`, um POST no `getAjaxUrl()` com `ajax_action=save_automation` e `document_signed`.
    - Vão as etapas alteradas, com a lista `ROBOTS` completa de cada uma, e a lista completa de `triggers`.
    - Serialize com `BX.Bizproc.Automation.Helper.toJsonPayload`: com `JSON.stringify`, o servidor ignora.
- **`save_automation` não apaga gatilho que ficou de fora.** Ele duplica, e o antigo continua valendo. Reenvie os antigos com `DELETED: 'Y'`.
- **Estrutura de um robô:**
  - `Type`, `Name`, `Activated`, `Properties`;
  - `Delay {type: 'after'|'before', value, valueType: 'i'|'h'|'d', basis, workTime}`;
  - `ExecuteAfterPrevious: 0|1`;
  - `Condition {type: 'mixed', items: [[{object: 'Document', field, operator, value}, 'AND']]}`.

  Gatilho de campo: `CODE: 'FIELD_CHANGED'`, `APPLY_RULES {fields, ALLOW_BACKWARDS, Condition}`.
- **O "Salvar" do rodapé grava a automação inteira do funil,** inclusive uma regra aberta só para olhar. Para consultar, feche sem salvar e recarregue. Depois de salvar, releia.
- **Robô novo herda a espera e o modo do anterior.** Confira "Em paralelo" e "Imediatamente", e grave a espera zero explícita.
- **Gravações longas:** no máximo 20 regras por vez, conferindo o estado depois de cada uma.

### Ordem e disparo

- **"Executar depois da anterior" espera também a espera da regra anterior.** A regra que deve rodar na hora não vem depois de uma regra com espera.
- **A mudança de etapa cancela as regras pendentes da etapa.** A regra que muda a etapa, ou grava o campo do gatilho, é a última.
- **Espera curta não serve para ordenar.** Uma espera de 1 minuto passou de 7 sem rodar.
- **Para mover, use um gatilho, e não "Alterar etapa".**
  - "Alterar etapa" não move o item quando roda na mesma gravação da mudança de etapa, nem na criação.
  - Use um gatilho de campo. "Modificar campos" no próprio item dispara o gatilho daquele campo, inclusive na criação.
- **Robô com espera é cancelado quando o item muda de etapa.** Por isso, alerta de X dias só dispara se o item continuar parado, o que serve de SLA.
- **Robô novo não roda para quem já estava na etapa.** Para esses, mova em lote pela lista (a ação em lote dispara as regras) ou trate por fluxo externo.
- **A primeira etapa roda também para itens criados por outra regra ou pela API** (`crm.item.add`). A importação por CSV é a exceção.
- **Régua de mensagens:** use execução em paralelo (`ExecuteAfterPrevious = 0`). "Aguardar a anterior" atrasa cada envio atrás do outro.

### Condições, valores e datas

- **Operadores:**
  - "Diferente de" funciona em regras e gatilhos;
  - "Contém" funciona em lista múltipla;
  - para "campo vazio", use o operador de vazio da tela.

  Confira no designer do portal, porque a lista de operadores varia por tipo de campo.
- **Fórmulas** como `=if(A <= B, "APROVADO", "")` funcionam em "Modificar campos". Resultado vazio não altera o campo e não dispara gatilho.
- **Texto:**
  - `{=Document:CAMPO > printable}` mostra o rótulo da opção;
  - os números saem sem separador de milhar (formate com `numberformat`).
- **Fuso nas regras, quando servidor e usuário estão em fusos diferentes:**
  - a data e hora de campo usada para agendar pode entrar deslocada (corrige com `dateadd(x, "-Nh")`);
  - a espera "até a data de um campo" conta da 0h local;
  - `dateadd` e `settime` contam da 0h do servidor;
  - `{=System:Date}` é a data do servidor: à noite, já pode ser o dia seguinte.

  Teste uma regra de data antes de replicar.
- **Dias úteis:** `addworkdays` respeita os feriados cadastrados e aceita valor negativo. Cadastre os feriados antes de confiar em prazos.

### Ações específicas

- **"Solicitação" (`CrmCreateRequestActivity`) não cria a atividade em Smart Process.** Use "Planejar atividade" (`CrmCreateToDoActivity`). Em Negócio, funciona.
- **"Editar item" (`CrmUpdateDynamicActivity`) só vale para Smart Process.** Acha o item por filtro e grava, e a alteração dispara os gatilhos do outro processo.
- **Criar item ligado:** `BindToCurrentElement = Y` não gravou o vínculo.
  - Grave o campo pai explicitamente: `PARENT_ID_<entityTypeId> = {=Document:ID}`.
  - O campo pai vazio desfaz o vínculo.
- **"Obter dados do item vinculado"** (`CrmGetRelationsInfo`): as regras que usam o resultado precisam rodar depois dela.
- **"Criar documento" com a espera da conversão em PDF ligada:** não dá erro, mas as regras seguintes não rodam. Desligue a espera.
- **Robô de tarefa:**
  - o criador sempre pode mudar o prazo; fixe o criador por ID (`user_N`), diferente do responsável;
  - o resumo obrigatório só é cobrado na tela da tarefa; concluir pelo card ou pela API passa sem resumo.
- **Robô webhook de saída:**
  - sempre POST;
  - o contexto vai na URL (`?id={=Document:ID}`);
  - o corpo traz `document_id[2]`.
- **Robô de e-mail:**
  - o remetente precisa estar conectado e liberado para quem configura;
  - o corpo fica em `Properties.MessageText` como `base64,` + HTML, com `MessageTextEncoded = 1`;
  - CSS inline;
  - o anexo condicionado a campo não sai se o card for movido antes.

### Modelos `.bpt`

- **Formato:** é o PHP serializado e comprimido com zlib. `scripts/bpt.py` lê e grava. Antes de editar por código, rode `bpt.py confere modelo.bpt`: se a ida e volta não reproduzir o arquivo byte a byte, não edite por código. O `bpt.py json` também avisa.
- **Estrutura do modelo:**
  - topo: `VERSION`, `TEMPLATE`, `PARAMETERS`, `VARIABLES`, `CONSTANTS`, `DOCUMENT_FIELDS`;
  - `TEMPLATE[0]` é `SequentialWorkflowActivity`;
  - nos robôs de etapa: `ParallelActivity` > um `SequenceActivity` por robô > a ação;
  - cada nó: `Type`, `Name`, `Activated`, `Properties`, `Children`.
- **Tarefa (`Task2Activity`):**
  - os campos ficam em `Properties['Fields']`: `TITLE`, `CREATED_BY`, `RESPONSIBLE_ID`, `AUDITORS`, `DEADLINE`, `REQUIRED_RESULT`;
  - escrever em `Properties['TITLE']` cria chave falsa e a etapa importa vazia.
- **Condições:**
  - o formato moderno é `mixedcondition`, e o ramo "senão" é `truecondition: '1'`;
  - o valor de opção de lista na condição é um código próprio, nem o ID nem um hash derivável: exporte um modelo que já use a condição e copie de lá;
  - teste 1 ramo importado antes do arquivo completo.
- **Importar:** na tela de regras da etapa, opção Importar. Espere o editor carregar antes de clicar.
- **Processo que trava:**
  - **campo excluído ainda referenciado:** trava e deixa instâncias presas. O Bitrix24 não guarda histórico de campo excluído;
  - **campo de decisão vazio:** faz nenhum ramo rodar, sem erro;
  - **faixas com `>` e `<`:** deixam os limites descobertos. Use `>=` e `<=`.

## 8. O que a API faz e o que só a tela faz

| Tarefa | Pela API | Só pela tela (ou rotina interna da tela, no navegador logado) |
|---|---|---|
| Criar e renomear funil | `crm.category.add`, `.update` | |
| Criar e ordenar etapa | `crm.status.add`, `.update` (com o `ENTITY_ID` certo) | |
| Criar campo e opções de lista | `crm.<entidade>.userfield.add`, `userfieldconfig.add` | máscara, e às vezes as opções depois de criado |
| Criar Smart Process e ligar pai e filho | `crm.type.add`, `crm.type.update` | |
| Layout do cartão | `crm.<entidade>.details.configuration.set`, por funil | |
| Obrigatório por etapa | (sem método público) | cartão > campo > "Requerido na etapa" |
| Robôs e gatilhos de etapa | (só robô de aplicativo, `bizproc.robot.*`) | designer de automação |
| Processo de negócio | importar ou trocar o modelo (`bizproc.workflow.template.add`), só com aplicativo local | designer |
| Disparar o gatilho "Webhook" de uma etapa | a URL pronta que a tela gera (chama `crm.automation.trigger` com `target` e `code`), inclusive pelo webhook de entrada | criar o gatilho na etapa |
| Gatilho próprio de aplicativo | `crm.automation.trigger.add` e `.execute`, só com aplicativo local | ligar na etapa |
| Permissões e papéis | | Configurações do CRM > Permissões |
| Formulários do site | `crm.webform.list` (ler) | configurar |
| Canais abertos, telefonia, horário e feriados | ler parte | configurar |

Quando a resposta é "só pela tela", entregue ao usuário o caminho exato e o que preencher, ou use o navegador dele com autorização expressa para cada gravação.

## 9. Validar, ativar e desfazer

- **Checklist de validação com ID estável.** Cada item traz:
  - um ID (`v01`, `r01`);
  - o bloco;
  - o que conferir e onde no portal;
  - o resultado esperado;
  - o status: OK, Divergente ou Não conferido.
- **Modo teste antes do modo produção:**
  - robôs que mandam algo para fora (e-mail, SMS, WhatsApp, assinatura) nascem desligados;
  - robôs internos (tarefa, aviso, campo) nascem ligados, com a condição extra "título contém [TESTE]";
  - fluxos externos com uma marca `MODO_TESTE = true`;
  - a mudança em fluxo de produção fica em rascunho até validar.

  **Para ativar:** troque a marca, tire a condição dos robôs, publique o rascunho e configure os obrigatórios.
- **Dados de teste:**
  - "[TESTE]" no título, sem e-mail e telefone reais, com os IDs anotados;
  - itens criados em cadeia por regras podem nascer sem [TESTE] no título: liste à parte;
  - mover para uma etapa com notificação avisa pessoas reais: combine antes.
- **Registros parados para demonstração:** deixe alguns itens de teste em etapas de decisão, para mostrar ao vivo.
- **Pasta de rollback por entrega:**
  - um LEIAME, com o que muda e a ordem de publicação e de desfazer (inversa);
  - os arquivos "antes" e "depois";
  - o backup da definição de campo antes de excluir;
  - o layout antes de alterar;
  - a lista de registros afetados antes de mudança em massa;
  - o log de cada gravação.
- **Escrita em massa só com autorização explícita.** Teste antes num lote pequeno. Se uma permissão bloquear o agente, pare e peça: não contorne por outra ferramenta.
- **Credencial:**
  - o webhook fica só na variável de ambiente da sessão, e é revogado no fim da implantação;
  - o agente não digita senha, token nem chave em campo nenhum;
  - o webhook de integração fica em nome de um usuário técnico, e não de um funcionário: se o funcionário sai, tudo para.
- **Produção crítica:** use bloqueio de escrita em código. O `scripts/b24.py` já bloqueia todo método que não é de leitura sem `--confirmar`.

## 10. Registrar

- **Registro técnico interno, separado do material do cliente.**
  - **No registro:**
    - o que foi criado, com os IDs;
    - como (API ou tela);
    - o que não foi alterado;
    - os testes e os defeitos corrigidos;
    - os dados de teste;
    - o que muda no dia dos convites;
    - o registro datado.
  - **Para o cliente:** as pendências e o guia de operação.
  - Modelo em assets/registro-de-configuracao.md.
- **Um arquivo de contexto por cliente, versionado.**
  - Traz as regras do cliente, a situação com data, os IDs, as lições e as pendências.
  - Credencial nunca entra: use um marcador como `TOKEN_DO_WEBHOOK`. Antes de cada commit, procure `/rest/<id>/`, token, senha e chave.
- **Entregas geradas por script:** o guia da equipe, as pendências e o documento técnico saem de um gerador que lê os documentos de trabalho. As decisões provisórias ficam numa lista única.
