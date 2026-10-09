"""Testa o scripts/b24.py contra um portal Bitrix24 simulado (nenhuma chamada sai da máquina).

    python3 testes/teste_b24.py
"""
import json
import os
import subprocess
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "bitrix24-for-ai-agents" / "scripts" / "b24.py"
TOKEN = "codigoSecreto123"
LEADS = [{"ID": str(i), "TITLE": f"Lead {i}", "STATUS_ID": "NEW"} for i in range(1, 121)]
ESTADO = {"chamadas": [], "limite_deal": 1, "atualizados": []}


def lista_paginada(itens, params):
    filtro = params.get("filter") or {}
    if str(params.get("start")) == "-1":
        chave = ">ID" if ">ID" in filtro else ">id"
        depois = int(filtro.get(chave, 0))
        pagina = [x for x in itens if int(x.get("ID", x.get("id"))) > depois][:50]
        return {"result": pagina}
    start = int(params.get("start") or 0)
    pagina = itens[start:start + 50]
    resp = {"result": pagina, "total": len(itens)}
    if start + 50 < len(itens):
        resp["next"] = start + 50
    return resp


def executar(metodo, params):
    ESTADO["chamadas"].append(metodo)
    if metodo == "profile":
        return {"result": {"ID": "1", "NAME": "Teste", "LAST_NAME": "Simulado", "ADMIN": True}}
    if metodo == "scope":
        return {"result": ["crm", "user"]}
    if metodo == "server.time":
        return {"result": "2026-10-09T10:00:00+03:00"}
    if metodo == "crm.lead.list":
        return lista_paginada(LEADS, params)
    if metodo == "crm.deal.list":
        if ESTADO["limite_deal"] > 0:
            ESTADO["limite_deal"] -= 1
            return 503, {"error": "QUERY_LIMIT_EXCEEDED", "error_description": "Too many requests"}
        return {"result": [{"ID": "7"}], "total": 1}
    if metodo == "crm.item.list":
        itens = [{"id": i, "title": f"Item {i}"} for i in range(1, 61)]
        r = lista_paginada(itens, params)
        r["result"] = {"items": r["result"]}
        return r
    if metodo == "crm.lead.get":
        return {"result": LEADS[int(params.get("id") or params.get("ID")) - 1]}
    if metodo == "crm.item.productrow.list":
        filtro = params.get("filter") or {}
        if "=ownerType" not in filtro:
            return 400, {"error": "INVALID_ARG", "error_description": "ownerType obrigatório"}
        return {"result": {"productRows": []}}
    if metodo == "crm.lead.update":
        ESTADO["atualizados"].append(params.get("id"))
        return {"result": True}
    if metodo == "crm.lead.delete":
        return {"result": True}
    if metodo == "crm.lead.add":
        ESTADO["adds"] = ESTADO.get("adds", 0) + 1
        return 502, {"error": "HTTP_502", "error_description": "Bad gateway"}
    if metodo == "crm.sem.plano":
        return 401, {"error": "ACCESS_DENIED", "error_description": "REST is available only by subscription"}
    if metodo == "crm.lead.erro":
        return 400, {"error": "ACCESS_DENIED", "error_description": f"sem acesso em /rest/1/{TOKEN}/crm"}
    return 400, {"error": "ERROR_METHOD_NOT_FOUND", "error_description": metodo}


def ler_query(qs):
    """Reconstrói o dicionário a partir da query no estilo PHP (filter[STAGE_ID]=NEW)."""
    saida = {}
    for chave, valor in urllib.parse.parse_qsl(qs, keep_blank_values=True):
        partes = chave.replace("]", "").split("[")
        alvo = saida
        for p in partes[:-1]:
            alvo = alvo.setdefault(p, {})
        alvo[partes[-1]] = valor
    return saida


class Portal(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        params = json.loads(self.rfile.read(tamanho) or b"{}")
        endereco = urllib.parse.urlparse(self.path)
        for k, v in urllib.parse.parse_qsl(endereco.query):
            params.setdefault(k, v)
        partes = endereco.path.split("/")
        if partes[1:4] != ["rest", "1", TOKEN]:
            return self.responder(401, {"error": "INVALID_CREDENTIALS"})
        metodo = partes[4].removesuffix(".json")
        if metodo == "batch":
            ESTADO["chamadas"].append("batch")
            res, err = {}, {}
            for chave, cmd in params["cmd"].items():
                m, _, qs = cmd.partition("?")
                r = executar(m, ler_query(qs))
                if isinstance(r, tuple):
                    err[chave] = r[1]
                else:
                    res[chave] = r["result"]
            return self.responder(200, {"result": {"result": res, "result_error": err, "result_total": {},
                                                   "result_next": {}}})
        r = executar(metodo, params)
        if isinstance(r, tuple):
            return self.responder(*r)
        self.responder(200, r)

    def responder(self, codigo, corpo):
        dados = json.dumps(corpo).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)


def rodar(*args, stdin=None):
    env = dict(os.environ, BITRIX24_WEBHOOK=f"http://127.0.0.1:{PORTA}/rest/1/{TOKEN}/")
    p = subprocess.run([sys.executable, str(SCRIPT), *args, "--intervalo", "0"], capture_output=True,
                       text=True, env=env)
    return p.returncode, p.stdout, p.stderr


falhas = []


def confere(nome, cond, detalhe=""):
    print(("OK    " if cond else "FALHA ") + nome + ("" if cond else f"  {detalhe}"))
    if not cond:
        falhas.append(nome)


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Portal)
    PORTA = servidor.server_address[1]
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    rc, out, err = rodar("ping")
    confere("ping mostra usuário e escopos", rc == 0 and '"crm"' in out and "Simulado" in out, err)
    confere("ping não imprime o código do webhook", TOKEN not in out + err)

    rc, out, err = rodar("list", "crm.lead.list", '{"select": ["ID", "TITLE"]}')
    confere("list pagina os 120 leads em 3 páginas", rc == 0 and len(json.loads(out)) == 120, err)

    rc, out, err = rodar("list", "crm.lead.list", "{}", "--por-id")
    confere("list --por-id lê os 120 sem contar o total", rc == 0 and len(json.loads(out)) == 120, err)

    rc, out, err = rodar("list", "crm.item.list", '{"entityTypeId": 1036}', "--max", "55")
    confere("list de crm.item.list tira os items e respeita --max", rc == 0 and len(json.loads(out)) == 55, err)

    saida = RAIZ / "testes" / "_backup.jsonl"
    rc, out, err = rodar("backup", "crm.lead.list", "{}", "--saida", str(saida))
    linhas = saida.read_text().splitlines() if saida.exists() else []
    confere("backup grava 120 linhas em JSON Lines", rc == 0 and len(linhas) == 120, err)
    saida.unlink(missing_ok=True)

    rc, out, err = rodar("call", "crm.lead.update", '{"id": 5, "fields": {"TITLE": "x"}}')
    confere("escrita sem --confirmar é barrada", rc == 2 and "não rodaram" in err and not ESTADO["atualizados"], err)
    rc, out, err = rodar("call", "crm.lead.update", '{"id": 5, "fields": {"TITLE": "x"}}', "--confirmar")
    confere("escrita com --confirmar roda", rc == 0 and ESTADO["atualizados"] == [5], err)

    rc, out, err = rodar("call", "crm.lead.delete", '{"id": 5}', "--confirmar")
    confere("exclusão só com --confirmar é barrada", rc == 2 and "apagam" in err, err)
    rc, out, err = rodar("call", "crm.lead.delete", '{"id": 5}', "--confirmar", "--confirmar-exclusao")
    confere("exclusão com as duas confirmações roda", rc == 0, err)

    rc, out, err = rodar("call", "batch", '{"cmd": {"a": "crm.lead.update?id=1&fields[TITLE]=y"}}')
    confere("batch chamado por call também exige --confirmar", rc == 2 and "crm.lead.update" in err, err)

    rc, out, err = rodar("call", "crm.deal.list")
    confere("espera e repete quando o portal responde QUERY_LIMIT_EXCEEDED",
            rc == 0 and "QUERY_LIMIT_EXCEEDED" in err and '"7"' in out, err)

    rc, out, err = rodar("call", "crm.lead.erro", "{}", "--confirmar")
    confere("erro do portal sai com o código do webhook mascarado", rc == 2 and TOKEN not in err
            and "ACCESS_DENIED" in err, err)

    rc, out, err = rodar("call", "crm.lead.add", '{"fields": {"TITLE": "x"}}', "--confirmar")
    confere("escrita não é repetida depois de erro 5xx (evita duplicar)", rc == 2 and ESTADO.get("adds") == 1
            and "pode ter sido aplicada" in err, err + str(ESTADO.get("adds")))

    rc, out, err = rodar("call", "crm.sem.plano", "{}", "--confirmar")
    confere("plano sem API REST gera mensagem clara", rc == 2 and "Vibe+" in err, err)

    cmds = RAIZ / "testes" / "_cmds.json"
    cmds.write_text(json.dumps({f"l{i}": ["crm.lead.get", {"id": i}] for i in range(1, 121)}
                               | {"prod": ["crm.item.productrow.list",
                                           {"filter": {"=ownerType": "D", "=ownerId": 7}}]}))
    antes = ESTADO["chamadas"].count("batch")
    rc, out, err = rodar("batch", str(cmds))
    res = json.loads(out) if out else {}
    confere("batch de 121 comandos vai em 3 lotes", ESTADO["chamadas"].count("batch") - antes == 3, err)
    confere("batch devolve os 121 resultados sem erro", len(res.get("result", {})) == 121
            and not res.get("result_error"), json.dumps(res.get("result_error"))[:300])
    cmds.write_text(json.dumps([["crm.lead.update", {"id": 1, "fields": {"TITLE": "z"}}]]))
    rc, out, err = rodar("batch", str(cmds))
    confere("batch com escrita sem --confirmar é barrado", rc == 2, err)
    cmds.unlink(missing_ok=True)

    falha = RAIZ / "testes" / "_falha.jsonl"
    rc, out, err = rodar("backup", "crm.metodo.inexistente.list", "{}", "--saida", str(falha))
    confere("backup que falha não deixa arquivo pela metade", rc == 2 and not falha.exists()
            and not Path(str(falha) + ".parcial").exists(), err)

    # escrita disfarçada de leitura
    disf = RAIZ / "testes" / "_disf.json"
    disf.write_text(json.dumps([["crm.lead.update?id=5&fields[COMMENTS]=ver site.info", {}]]))
    rc, out, err = rodar("batch", str(disf))
    confere("ponto no valor do batch não faz escrita parecer leitura", rc == 2 and "não rodaram" in err, err)
    disf.unlink(missing_ok=True)
    rc, out, err = rodar("call", "disk.file.getExternalLink", '{"id": 1}')
    confere("getExternalLink é tratado como escrita", rc == 2 and "não rodaram" in err, err)
    rc, out, err = rodar("fields", "crm.lead.delete")
    confere("fields recusa método que não é entidade", rc == 2 and "fields aceita" in err, err)

    rc, out, err = rodar("list", "crm.lead.update", "{}")
    confere("list recusa método que não é de leitura", rc == 2, err)

    # restaurar.py: do backup ao lote de desfazer, e o lote roda pelo b24.py
    bkp = RAIZ / "testes" / "_bkp.jsonl"
    rodar("backup", "crm.lead.list", '{"select": ["ID", "TITLE", "STATUS_ID"]}', "--saida", str(bkp))
    restaurar = RAIZ / "bitrix24-for-ai-agents" / "scripts" / "restaurar.py"
    lote = RAIZ / "testes" / "_restaurar.json"
    p = subprocess.run([sys.executable, str(restaurar), str(bkp), "--metodo", "crm.lead.update", "--campos",
                        "STATUS_ID,TITLE,NAO_EXISTE", "--ids", "3,4", "--saida", str(lote)],
                       capture_output=True, text=True)
    cmds_r = json.loads(lote.read_text()) if lote.exists() else {}
    confere("restaurar monta 2 comandos só com os IDs pedidos", p.returncode == 0 and set(cmds_r) == {"r3", "r4"}
            and cmds_r["r3"][1]["fields"] == {"STATUS_ID": "NEW", "TITLE": "Lead 3"}, p.stderr + p.stdout)
    confere("restaurar avisa o campo que não está no backup", "NAO_EXISTE" in p.stderr, p.stderr)
    ESTADO["atualizados"].clear()
    rc, out, err = rodar("batch", str(lote), "--confirmar")
    confere("o lote de desfazer roda pelo b24.py", rc == 0 and sorted(ESTADO["atualizados"]) == ["3", "4"],
            err + str(ESTADO["atualizados"]))
    bkp.unlink(missing_ok=True)
    lote.unlink(missing_ok=True)

    servidor.shutdown()
    print(f"\n{len(falhas)} falha(s)")
    sys.exit(1 if falhas else 0)
