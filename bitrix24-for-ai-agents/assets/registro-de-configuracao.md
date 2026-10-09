# Registro de configuração do portal

Modelo para documentar como um portal Bitrix24 está configurado e por quê. Preencha ao desenhar, atualize a cada mudança e guarde junto do projeto. Sem ele, a próxima pessoa (ou o próximo agente) mexe às cegas.

Não escreva aqui o código de nenhum webhook nem senha: só quem criou, os escopos e para onde aponta.

## 1. O portal

| Item | Valor |
|---|---|
| Endereço | `https://_____.bitrix24.___` |
| Plano | Essentials ou Vibe+, e qual faixa |
| Fuso do portal | |
| Idioma | |
| Responsável do lado do cliente | nome e papel |
| Data deste registro | dd/mm/aaaa |

## 2. O objetivo

Em 3 a 5 linhas: o que o portal precisa fazer pela operação, e como saber que deu certo (o número que o dono vai olhar).

## 3. As entidades em uso

| Entidade | entityTypeId | Para que serve aqui | Quem usa |
|---|---|---|---|
| Leads | 1 | | |
| Negócios | 2 | | |
| Smart Process "_____" | | | |

## 4. Funis e etapas

Uma tabela por funil.

**Funil "_____"** (entityTypeId __, categoria __)

| Ordem | Código da etapa | Nome | Tipo (andamento, ganho, perda) | Quem move para cá | Obrigatório para entrar | Automações da etapa |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## 5. Campos personalizados

| Código (UF_CRM_...) | Nome na tela | Tipo | Entidade | Obrigatório em | Quem preenche (pessoa ou automação) |
|---|---|---|---|---|---|
| | | | | | |

**Listas:** para cada campo de lista, os valores e os IDs (a API grava pelo ID, e não pelo texto).

| Campo | ID do item | Valor |
|---|---|---|
| | | |

## 6. Regras de automação e processos de negócio

| Onde (funil e etapa) | Gatilho ou entrada | O que faz | Condição | Atrasa ou espera | Dono |
|---|---|---|---|---|---|
| | | | | | |

**Processos de negócio:** nome, quando roda (manual, ao criar, ao mudar) e o arquivo `.bpt` exportado, com a data.

## 7. Integrações

| Integração | Tipo (webhook de entrada, de saída, app, conector) | Escopos | Criada por (usuário) | Para onde aponta ou quem chama | O que faz |
|---|---|---|---|---|---|
| | | | | | |

## 8. Pessoas, filas e permissões

- Departamentos e quem chefia cada um.
- Filas de distribuição (quem recebe o quê, em que ordem).
- Papéis de acesso ao CRM e o que cada um vê.

## 9. Formulários, canais e telefonia

Formulários do site (em que funil e etapa caem), canais abertos (WhatsApp, Instagram, chat do site), números de telefone e gravação de chamadas.

## 10. Decisões

| Data | Decisão | Por quê | Quem decidiu |
|---|---|---|---|
| | | | |

## 11. Como desfazer

Para cada mudança relevante, como voltar ao estado anterior: o backup (arquivo e data), o que remover e em que ordem.

## 12. Histórico de mudanças

| Data | O que mudou | Quem | Validado com |
|---|---|---|---|
| | | | |
