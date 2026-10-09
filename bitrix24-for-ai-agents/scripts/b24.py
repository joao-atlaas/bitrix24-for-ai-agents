#!/usr/bin/env python3
"""Cliente de linha de comando para a API REST do Bitrix24, feito para agentes de IA.

Só usa a biblioteca padrão do Python. Conecta por webhook de entrada (o jeito mais simples e
o recomendado). O endereço do webhook vem da variável de ambiente BITRIX24_WEBHOOK, nunca de um
argumento, para não ficar no histórico do terminal nem aparecer na conversa.

    export BITRIX24_WEBHOOK="https://SEU-PORTAL.bitrix24.com.br/rest/1/xxxxxxxx/"

Comandos:
    ping                                   confere a conexão, o usuário e os escopos do webhook
    fields ENTIDADE                        campos de lead, deal, contact, company ou de um entityTypeId
    call METODO [PARAMS] [--confirmar]     chama um método e mostra o resultado
    list METODO [PARAMS] [--max N] [--saida ARQ.jsonl] [--por-id]
                                           lista todos os registros, página por página
    backup METODO [PARAMS] --saida ARQ.jsonl
                                           o mesmo que list, obrigatório antes de alterar em lote
    batch ARQUIVO.json [--confirmar]       roda comandos em lotes de 50

PARAMS é um JSON, por exemplo '{"filter": {"STATUS_ID": "NEW"}, "select": ["ID", "TITLE"]}'.

Segurança:
- Todo método que não está na lista de leitura (get, list, fields e afins) é tratado como escrita e
  só roda com --confirmar; alguns "get" que criam algo (link público) também. Método que apaga
  (delete, remove, terminate) pede também --confirmar-exclusao.
- Escrita não é repetida depois de timeout ou erro sem código: ela pode já ter sido aplicada.
- O endereço do webhook nunca é impresso; em mensagens de erro ele sai mascarado.
- Respeita o limite de taxa: no máximo 2 chamadas por segundo, espera crescente quando o Bitrix24
  responde QUERY_LIMIT_EXCEEDED (503) e espera a janela do método no OPERATION_TIME_LIMIT (429).
  No OVERLOAD_LIMIT para na hora: é bloqueio manual do portal.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

INTERVALO_MINIMO = 0.5  # segundos entre chamadas (2 por segundo)
TENTATIVAS = 7
LOTE = 50  # máximo de comandos por batch e de itens por página

# Sufixos e nomes de método que só leem. O resto é escrita (lista de permissão, e não de bloqueio).
LEITURA_SUFIXOS = ("get", "list", "fields", "getfields", "getlist", "count", "search", "find",
                   "findbycomm", "info", "current", "describe", "version", "getlistall", "getbyfilter",
                   "getsettings", "getavailable", "types", "instances", "items", "statistic")
LEITURA_EXATOS = {"scope", "methods", "profile", "app.info", "user.current", "server.time",
                  "user.search", "crm.stagehistory.list", "voximplant.statistic.get",
                  "crm.duplicate.findbycomm", "crm.multifield.fields", "crm.enum.fields",
                  "crm.enum.ownertype", "crm.enum.activitytype", "crm.enum.contenttype",
                  "crm.enum.activitystatus", "crm.enum.activitydirection", "crm.enum.addresstype",
                  "crm.enum.settings.mode", "department.get"}
EXCLUSAO = re.compile(r"(^|\.)(delete|remove|terminate|kill|clear|purge)", re.I)
# Métodos com nome de leitura que criam ou mudam alguma coisa: tratados como escrita.
ESCRITA_DISFARCADA = {"disk.file.getexternallink", "disk.folder.getexternallink", "im.disk.file.commit",
                      "crm.automation.trigger"}

ENTIDADES = {"lead": "crm.lead.fields", "deal": "crm.deal.fields", "contact": "crm.contact.fields",
             "company": "crm.company.fields", "quote": "crm.quote.fields", "product": "crm.product.fields",
             "activity": "crm.activity.fields", "task": "tasks.task.getfields", "user": "user.fields"}


class ErroB24(Exception):
    pass


def eh_leitura(metodo):
    # Só o nome do método conta: num comando de batch, o que vem depois do "?" são parâmetros.
    m = metodo.strip().split("?", 1)[0].lower()
    if m in ESCRITA_DISFARCADA:
        return False
    if m in LEITURA_EXATOS:
        return True
    if EXCLUSAO.search(m):
        return False
    ultimo = m.rsplit(".", 1)[-1]
    return ultimo in LEITURA_SUFIXOS or ultimo.startswith("get") or ultimo.startswith("list")


def eh_exclusao(metodo):
    return bool(EXCLUSAO.search(metodo.strip().split("?", 1)[0].lower()))


def montar_query(params, prefixo=""):
    """Converte um dicionário para a query no estilo do PHP (filter[STAGE_ID]=NEW), usada no batch.
    Chaves com sinal (=, >, %, !) são codificadas, como o Bitrix24 exige dentro do batch."""
    partes = []
    if isinstance(params, dict):
        itens = params.items()
    elif isinstance(params, (list, tuple)):
        itens = enumerate(params)
    else:
        return [(prefixo, params)]
    for chave, valor in itens:
        nome = f"{prefixo}[{chave}]" if prefixo else str(chave)
        if isinstance(valor, (dict, list, tuple)):
            if not valor:
                partes.append((nome, ""))
            partes.extend(montar_query(valor, nome))
        else:
            if isinstance(valor, bool):
                valor = "Y" if valor else "N"
            partes.append((nome, "" if valor is None else valor))
    return partes


def query_texto(params):
    return "&".join(urllib.parse.quote(str(k), safe="[]") + "=" + urllib.parse.quote(str(v), safe="")
                    for k, v in montar_query(params or {}))


class Cliente:
    def __init__(self, webhook, intervalo=INTERVALO_MINIMO, verboso=True):
        if not webhook:
            raise ErroB24("Defina a variável BITRIX24_WEBHOOK com o endereço do webhook de entrada "
                          "(https://SEU-PORTAL/rest/ID_DO_USUARIO/CODIGO/).")
        self.base = webhook if webhook.endswith("/") else webhook + "/"
        self.intervalo = intervalo
        self.verboso = verboso
        self._ultima = 0.0
        self._ultimo_tempo = None
        self.chamadas = 0

    def mascarar(self, texto):
        texto = str(texto).replace(self.base, "<webhook>/")
        return re.sub(r"/rest/\d+/[A-Za-z0-9]+/", "/rest/<id>/<codigo>/", texto)

    def log(self, msg):
        if self.verboso:
            print(msg, file=sys.stderr)

    def chamar(self, metodo, params=None, repetir_se_incerto=None):
        """Chama um método e devolve o corpo da resposta (dict com result, next, total...).

        Leitura é repetida em qualquer falha passageira. Escrita só é repetida quando o portal recusou
        antes de executar (QUERY_LIMIT_EXCEEDED, OPERATION_TIME_LIMIT): depois de timeout ou erro 5xx sem
        código, a escrita pode ter sido aplicada, e repetir duplicaria registro ou aviso."""
        if repetir_se_incerto is None:
            repetir_se_incerto = eh_leitura(metodo)
        url = self.base + metodo + ".json"
        if params and "start" in params:
            # Alguns métodos (crm.item.list) só paginam com o start no endereço.
            url += "?start=" + urllib.parse.quote(str(params["start"]))
        corpo = json.dumps(params or {}).encode()
        espera = 1.0
        for tentativa in range(1, TENTATIVAS + 1):
            pausa = self.intervalo - (time.time() - self._ultima)
            if pausa > 0:
                time.sleep(pausa)
            self._ultima = time.time()
            self.chamadas += 1
            req = urllib.request.Request(url, data=corpo, method="POST",
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    dados = json.loads(r.read().decode() or "{}")
            except urllib.error.HTTPError as e:
                try:
                    dados = json.loads(e.read().decode() or "{}")
                except ValueError:
                    dados = {"error": f"HTTP_{e.code}", "error_description": e.reason}
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if not repetir_se_incerto:
                    raise ErroB24(self.mascarar(f"A conexão caiu durante uma escrita ({e}). Ela pode ter sido "
                                                "aplicada: leia o estado no portal antes de repetir."))
                if tentativa == TENTATIVAS:
                    raise ErroB24(self.mascarar(f"Sem conexão com o portal: {e}"))
                self.log(f"  conexão falhou ({self.mascarar(e)}); nova tentativa em {espera:.0f}s")
                time.sleep(espera)
                espera = min(espera * 2, 60)
                continue
            erro = dados.get("error")
            descricao = str(dados.get("error_description", ""))
            if erro == "OVERLOAD_LIMIT":
                raise ErroB24("OVERLOAD_LIMIT: o portal bloqueou as chamadas deste acesso. Não repita: "
                              "fale com o suporte do Bitrix24.")
            if str(erro).startswith("HTTP_5") and not repetir_se_incerto:
                raise ErroB24(f"{erro}: o portal falhou durante uma escrita. Ela pode ter sido aplicada: leia o "
                              "estado no portal antes de repetir.")
            if erro in ("QUERY_LIMIT_EXCEEDED", "OPERATION_TIME_LIMIT") or str(erro).startswith("HTTP_5"):
                if tentativa == TENTATIVAS:
                    raise ErroB24(f"{erro}: o portal continuou recusando por limite. Espere alguns minutos "
                                  "e rode de novo, ou diminua o volume.")
                pausa_extra = espera
                if erro == "OPERATION_TIME_LIMIT":
                    # Limite de tempo acumulado do método (janela de 10 minutos): esperar a cesta sair.
                    reset = (self._ultimo_tempo or {}).get("operating_reset_at")
                    pausa_extra = max(5.0, min(600.0, float(reset) - time.time())) if reset else 60.0
                self.log(f"  {erro}: esperando {pausa_extra:.0f}s (tentativa {tentativa})")
                time.sleep(pausa_extra)
                espera = min(espera * 2, 60)
                continue
            if erro:
                if "only by subscription" in descricao or "only on commercial plans" in descricao or \
                        "only available on" in descricao:
                    raise ErroB24("O portal não libera a API REST neste plano. Desde 2026, a API só vem nos "
                                  "planos Vibe+ (o Essentials não tem). Ver references/planos-e-licencas.md.")
                raise ErroB24(self.mascarar(f"{erro}: {descricao}"))
            self._ultimo_tempo = dados.get("time") or self._ultimo_tempo
            return dados
        raise ErroB24("Falha sem resposta do portal.")

    def listar(self, metodo, params=None, maximo=None, por_id=False):
        """Gera os itens de um método de lista, página por página (50 por vez)."""
        params = dict(params or {})
        total_lido = 0
        if por_id:
            # Para listas grandes: ordena por ID e pede só o que vem depois do último lido, sem contar o
            # total (start = -1). É o caminho que a documentação recomenda para milhares de registros.
            # crm.item.* filtra e ordena por "id"; tasks.task.list e os métodos antigos, por "ID".
            chave = "id" if metodo.startswith("crm.item.") else "ID"
            params["order"] = {chave: "ASC"}
            filtro = dict(params.get("filter") or {})
            ultimo = 0
            while True:
                filtro[f">{chave}"] = ultimo
                params["filter"] = filtro
                params["start"] = -1
                dados = self.chamar(metodo, params)
                itens = extrair_itens(dados.get("result"))
                if not itens:
                    return
                for item in itens:
                    yield item
                    total_lido += 1
                    if maximo and total_lido >= maximo:
                        return
                novo = int(itens[-1].get("id") or itens[-1].get("ID") or 0)
                if novo <= ultimo:
                    raise ErroB24(f"{metodo} ignorou o filtro por ID (o último ID não avançou). Use a paginação "
                                  "comum, sem --por-id.")
                ultimo = novo
                if len(itens) < LOTE:
                    return
        start = params.pop("start", 0)
        while True:
            params["start"] = start
            dados = self.chamar(metodo, params)
            itens = extrair_itens(dados.get("result"))
            if start == 0 and "total" in dados:
                self.log(f"  {metodo}: {dados['total']} registros no total")
            for item in itens:
                yield item
                total_lido += 1
                if maximo and total_lido >= maximo:
                    return
            if "next" not in dados or not itens:
                return
            start = dados["next"]

    def lote(self, comandos):
        """Roda comandos em lotes de 50. comandos = lista de (chave, metodo, params)."""
        saida = {"result": {}, "result_error": {}, "result_total": {}, "result_next": {}}
        for i in range(0, len(comandos), LOTE):
            parte = comandos[i:i + LOTE]
            cmd = {chave: metodo + ("?" + query_texto(params) if params else "")
                   for chave, metodo, params in parte}
            so_leitura = all(eh_leitura(metodo) for _, metodo, _ in parte)
            dados = self.chamar("batch", {"halt": 0, "cmd": cmd}, repetir_se_incerto=so_leitura)
            r = dados.get("result") or {}
            for campo in saida:
                valor = r.get(campo) or {}
                if isinstance(valor, dict):
                    saida[campo].update(valor)
            self.log(f"  lote {i // LOTE + 1}: {len(parte)} comandos, {len(r.get('result_error') or {})} com erro")
        return saida


def extrair_itens(resultado):
    """Os métodos de lista devolvem a lista direto, ou dentro de items, tasks, users..."""
    if isinstance(resultado, list):
        return resultado
    if isinstance(resultado, dict):
        for chave in ("items", "tasks", "users", "workflows", "templates", "result"):
            if isinstance(resultado.get(chave), list):
                return resultado[chave]
        listas = [v for v in resultado.values() if isinstance(v, list)]
        if len(listas) == 1:
            return listas[0]
        if resultado and all(isinstance(v, dict) for v in resultado.values()):
            return list(resultado.values())
    return []


def ler_params(texto):
    if not texto:
        return {}
    if texto.startswith("@"):
        with open(texto[1:], encoding="utf-8") as f:
            return json.load(f)
    try:
        return json.loads(texto)
    except ValueError as e:
        raise ErroB24(f"PARAMS não é um JSON válido: {e}")


def exigir_confirmacao(metodos, args):
    escrita = sorted({m for m in metodos if not eh_leitura(m)})
    exclusao = sorted({m for m in escrita if eh_exclusao(m)})
    if escrita and not args.confirmar:
        raise ErroB24("Estes métodos alteram o portal e não rodaram: " + ", ".join(escrita)
                      + ". Mostre ao usuário o que vai mudar, faça o backup e rode de novo com --confirmar.")
    if exclusao and not args.confirmar_exclusao:
        raise ErroB24("Estes métodos apagam dados e não rodaram: " + ", ".join(exclusao)
                      + ". Excluir é irreversível pela API: só com pedido explícito do usuário, com "
                        "--confirmar --confirmar-exclusao.")


def gravar_jsonl(itens, caminho):
    """Grava num arquivo temporário e só troca pelo definitivo no fim: se a leitura falhar no meio,
    não fica para trás um arquivo vazio ou pela metade que pareça um backup completo."""
    n = 0
    temporario = caminho + ".parcial"
    try:
        with open(temporario, "w", encoding="utf-8") as f:
            for item in itens:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                n += 1
    except BaseException:
        if os.path.exists(temporario):
            os.remove(temporario)
        raise
    os.replace(temporario, caminho)
    return n


def ler_comandos(caminho):
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    if isinstance(dados, dict) and "cmd" in dados:
        dados = dados["cmd"]
    comandos = []
    if isinstance(dados, dict):
        for chave, valor in dados.items():
            metodo, params = (valor[0], valor[1] if len(valor) > 1 else {}) if isinstance(valor, list) \
                else (valor.get("method"), valor.get("params", {}))
            comandos.append((str(chave), metodo, params))
    else:
        for i, valor in enumerate(dados):
            metodo, params = (valor[0], valor[1] if len(valor) > 1 else {}) if isinstance(valor, list) \
                else (valor.get("method"), valor.get("params", {}))
            comandos.append((f"c{i}", metodo, params))
    return comandos


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["ping", "fields", "call", "list", "backup", "batch"])
    ap.add_argument("alvo", nargs="?", help="método, entidade ou arquivo de comandos")
    ap.add_argument("params", nargs="?", help="JSON com os parâmetros, ou @arquivo.json")
    ap.add_argument("--max", type=int, help="máximo de registros na lista")
    ap.add_argument("--saida", help="grava a lista em JSON Lines (um registro por linha)")
    ap.add_argument("--por-id", action="store_true", help="lista grande: pagina pelo ID, sem contar o total")
    ap.add_argument("--confirmar", action="store_true", help="autoriza método que altera o portal")
    ap.add_argument("--confirmar-exclusao", action="store_true", help="autoriza método que apaga dados")
    ap.add_argument("--intervalo", type=float, default=INTERVALO_MINIMO, help="segundos entre chamadas")
    ap.add_argument("--silencioso", action="store_true", help="não mostra o andamento")
    args = ap.parse_args(argv)

    try:
        b24 = Cliente(os.environ.get("BITRIX24_WEBHOOK", ""), args.intervalo, not args.silencioso)
        if args.comando == "ping":
            perfil = b24.chamar("profile").get("result", {})
            escopos = b24.chamar("scope").get("result", [])
            hora = b24.chamar("server.time").get("result")
            fuso = None
            try:
                atual = b24.chamar("user.current").get("result") or {}
                fuso = atual.get("TIME_ZONE") or None
            except ErroB24:
                pass
            print(json.dumps({"usuario": {k: perfil.get(k) for k in ("ID", "NAME", "LAST_NAME", "ADMIN")},
                              "fuso_do_usuario": fuso or "não informado (vale o fuso do portal)",
                              "escopos": escopos, "hora_do_servidor": hora}, ensure_ascii=False, indent=2))
            return 0
        if not args.alvo:
            raise ErroB24("Falta o método, a entidade ou o arquivo.")
        if args.comando == "fields":
            alvo = args.alvo.lower()
            if alvo.isdigit():
                res = b24.chamar("crm.item.fields", {"entityTypeId": int(alvo)})
            elif alvo in ENTIDADES:
                res = b24.chamar(ENTIDADES[alvo])
            else:
                raise ErroB24("fields aceita " + ", ".join(sorted(ENTIDADES)) + " ou o número de um entityTypeId.")
            print(json.dumps(res.get("result"), ensure_ascii=False, indent=2))
            return 0
        if args.comando == "call":
            params = ler_params(args.params)
            if args.alvo.lower() == "batch":
                # O batch é julgado pelos comandos que ele leva dentro.
                cmds = (params.get("cmd") or {}).values() if isinstance(params.get("cmd"), dict) \
                    else (params.get("cmd") or [])
                exigir_confirmacao([str(c).split("?", 1)[0] for c in cmds] or ["batch"], args)
            else:
                exigir_confirmacao([args.alvo], args)
            res = b24.chamar(args.alvo, params)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if args.comando in ("list", "backup"):
            if not eh_leitura(args.alvo):
                raise ErroB24(f"{args.alvo} não é um método de leitura. Para listar, use um método .list.")
            if args.comando == "backup" and not args.saida:
                raise ErroB24("O backup precisa de --saida ARQUIVO.jsonl.")
            itens = b24.listar(args.alvo, ler_params(args.params), args.max, args.por_id)
            if args.saida:
                n = gravar_jsonl(itens, args.saida)
                b24.log(f"  {n} registros gravados em {args.saida} ({b24.chamadas} chamadas)")
                print(json.dumps({"registros": n, "arquivo": args.saida}, ensure_ascii=False))
            else:
                lista = list(itens)
                b24.log(f"  {len(lista)} registros ({b24.chamadas} chamadas)")
                print(json.dumps(lista, ensure_ascii=False, indent=2))
            return 0
        if args.comando == "batch":
            comandos = ler_comandos(args.alvo)
            exigir_confirmacao([m for _, m, _ in comandos], args)
            res = b24.lote(comandos)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 1 if res["result_error"] else 0
    except ErroB24 as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
