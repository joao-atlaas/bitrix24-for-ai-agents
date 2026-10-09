"""Um portal Bitrix24 de mentira, para testar a skill sem tocar em portal real.

    python3 testes/portal_simulado.py 8765
    export BITRIX24_WEBHOOK="http://127.0.0.1:8765/rest/1/codigoSecreto123/"

Responde aos métodos mais usados (perfil, mapa do portal, listas com filtro e paginação, histórico
de etapas, batch) e registra as escritas em testes/_escritas.jsonl, sem aplicar nada.
"""
import json
import random
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

TOKEN = "codigoSecreto123"
ESCRITAS = Path(__file__).resolve().parent / "_escritas.jsonl"
random.seed(3)
HOJE = datetime(2026, 10, 9, 10, 0, 0)

USUARIOS = [{"ID": str(i), "NAME": n, "LAST_NAME": s, "ACTIVE": True, "UF_DEPARTMENT": [d],
             "WORK_POSITION": c, "USER_TYPE": "employee"}
            for i, n, s, d, c in [(1, "Ana", "Prado", 1, "Diretora"), (5, "Bruno", "Lima", 2, "Vendedor"),
                                  (7, "Carla", "Reis", 2, "Vendedora"), (9, "Diego", "Moura", 2, "Vendedor"),
                                  (11, "Elisa", "Nunes", 3, "Pós-venda")]]
DEPARTAMENTOS = [{"ID": "1", "NAME": "Empresa", "UF_HEAD": "1"},
                 {"ID": "2", "NAME": "Comercial", "PARENT": "1", "UF_HEAD": "1"},
                 {"ID": "3", "NAME": "Pós-venda", "PARENT": "1", "UF_HEAD": "11"}]
CATEGORIAS = [{"id": 0, "name": "Vendas", "sort": 10, "isDefault": "Y"},
              {"id": 3, "name": "Renovação", "sort": 20, "isDefault": "N"}]
ETAPAS = [
    ("DEAL_STAGE", "NEW", "Novo", 10, ""), ("DEAL_STAGE", "PREPARATION", "Proposta", 20, ""),
    ("DEAL_STAGE", "EXECUTING", "Negociação", 30, ""), ("DEAL_STAGE", "WON", "Ganho", 40, "S"),
    ("DEAL_STAGE", "LOSE", "Perdido", 50, "F"),
    ("DEAL_STAGE_3", "C3:NEW", "A renovar", 10, ""), ("DEAL_STAGE_3", "C3:WON", "Renovado", 20, "S"),
    ("DEAL_STAGE_3", "C3:LOSE", "Não renovou", 30, "F"),
    ("STATUS", "NEW", "Não processado", 10, ""), ("STATUS", "IN_PROCESS", "Em andamento", 20, ""),
    ("STATUS", "CONVERTED", "Convertido", 30, "S"), ("STATUS", "JUNK", "Perdido", 40, "F"),
]
STATUS = [{"ID": str(i + 1), "ENTITY_ID": e, "STATUS_ID": c, "NAME": n, "SORT": o, "SEMANTICS": sem or None}
          for i, (e, c, n, o, sem) in enumerate(ETAPAS)]
USERFIELDS = [{"ID": "301", "ENTITY_ID": "CRM_DEAL", "FIELD_NAME": "UF_CRM_MOTIVO_PERDA", "USER_TYPE_ID": "enumeration",
               "LIST": [{"ID": "41", "VALUE": "Preço", "XML_ID": "PRECO"},
                        {"ID": "42", "VALUE": "Sem retorno", "XML_ID": "SEM_RETORNO"},
                        {"ID": "43", "VALUE": "Concorrente", "XML_ID": "CONCORRENTE"}],
               "EDIT_FORM_LABEL": {"br": "Motivo da perda"}}]


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S+03:00")


DEALS = []
for i in range(1, 301):
    cat = 0 if i <= 240 else 3
    etapas = ["NEW", "PREPARATION", "EXECUTING", "WON", "LOSE"] if cat == 0 else ["C3:NEW", "C3:WON", "C3:LOSE"]
    etapa = random.choice(etapas)
    criado = HOJE - timedelta(days=random.randint(5, 300))
    mudou = min(HOJE, criado + timedelta(days=random.randint(0, 200)))
    DEALS.append({"ID": str(i), "TITLE": f"Negócio {i}", "CATEGORY_ID": str(cat), "STAGE_ID": etapa,
                  "ASSIGNED_BY_ID": random.choice(["5", "7", "9"]), "OPPORTUNITY": str(random.randint(2, 90) * 1000),
                  "DATE_CREATE": iso(criado), "DATE_MODIFY": iso(mudou), "MOVED_TIME": iso(mudou),
                  "UF_CRM_MOTIVO_PERDA": "42" if etapa.endswith("LOSE") else None})
LEADS = [{"ID": str(i), "TITLE": f"Lead {i}", "STATUS_ID": random.choice(["NEW", "IN_PROCESS", "JUNK"]),
          "ASSIGNED_BY_ID": random.choice(["5", "7", "9"]), "DATE_CREATE": iso(HOJE - timedelta(days=i))}
         for i in range(1, 121)]


def bate(reg, filtro):
    for chave, esperado in (filtro or {}).items():
        m = re.match(r"^(!@|@|>=|<=|!=|!|>|<|=|%)?(.+)$", chave)
        op, campo = m.group(1) or "=", m.group(2)
        valor = reg.get(campo, reg.get(campo.upper()))
        if op in ("@", "!@"):
            lista = [str(x) for x in (esperado if isinstance(esperado, list) else esperado.values())]
            if (str(valor) in lista) != (op == "@"):
                return False
            continue
        a, b = str(valor or ""), str(esperado)
        if campo.upper() in ("ID", "ASSIGNED_BY_ID", "CATEGORY_ID", "OPPORTUNITY") and a and b.lstrip("-").isdigit():
            a, b = int(float(a)), int(b)
        ok = {"=": a == b, "!": a != b, "!=": a != b, ">": a > b, "<": a < b, ">=": a >= b, "<=": a <= b,
              "%": str(b).lower() in str(a).lower()}[op]
        if not ok:
            return False
    return True


def listar(itens, params):
    filtrados = [x for x in itens if bate(x, params.get("filter"))]
    ordem = params.get("order") or {}
    if ordem:
        campo, sentido = next(iter(ordem.items()))
        filtrados.sort(key=lambda x: int(x.get(campo, x.get(campo.upper(), 0)) or 0), reverse=sentido.upper() == "DESC")
    sel = params.get("select")
    if sel and "*" not in sel:
        filtrados = [{k: v for k, v in x.items() if k in sel or k == "ID"} for x in filtrados]
    start = int(params.get("start") or 0)
    if start == -1:
        return {"result": filtrados[:50]}
    pagina = filtrados[start:start + 50]
    r = {"result": pagina, "total": len(filtrados)}
    if start + 50 < len(filtrados):
        r["next"] = start + 50
    return r


def executar(metodo, params):
    if metodo == "profile":
        return {"result": {"ID": "1", "NAME": "Ana", "LAST_NAME": "Prado", "ADMIN": True}}
    if metodo == "scope":
        return {"result": ["crm", "user", "department", "task", "im", "bizproc"]}
    if metodo == "server.time":
        return {"result": iso(HOJE)}
    if metodo == "crm.type.list":
        return {"result": {"types": [{"id": 5, "entityTypeId": 1036, "title": "Contratos",
                                      "isCategoriesEnabled": "Y", "isStagesEnabled": "Y"}]}}
    if metodo == "crm.category.list":
        if int(params.get("entityTypeId", 0)) == 2:
            return {"result": {"categories": CATEGORIAS}}
        return {"result": {"categories": [{"id": 7, "name": "Contratos ativos", "isDefault": "Y"}]}}
    if metodo == "crm.status.list":
        return listar(STATUS, params)
    if metodo in ("crm.deal.fields", "crm.lead.fields"):
        campos = {"ID": {"type": "integer"}, "TITLE": {"type": "string"}, "STAGE_ID": {"type": "crm_status"},
                  "ASSIGNED_BY_ID": {"type": "user"}, "DATE_MODIFY": {"type": "datetime"},
                  "MOVED_TIME": {"type": "datetime"}}
        if metodo == "crm.deal.fields":
            campos["UF_CRM_MOTIVO_PERDA"] = {"type": "enumeration", "title": "UF_CRM_MOTIVO_PERDA",
                                             "listLabel": "Motivo da perda", "items": USERFIELDS[0]["LIST"]}
        return {"result": campos}
    if metodo == "crm.deal.userfield.list":
        return {"result": USERFIELDS, "total": len(USERFIELDS)}
    if metodo == "user.get":
        return listar(USUARIOS, params)
    if metodo == "department.get":
        return {"result": DEPARTAMENTOS, "total": 3}
    if metodo == "crm.deal.list":
        return listar(DEALS, params)
    if metodo == "crm.lead.list":
        return listar(LEADS, params)
    if metodo in ("crm.deal.get", "crm.lead.get"):
        base = DEALS if "deal" in metodo else LEADS
        rid = str(params.get("id") or params.get("ID"))
        reg = next((x for x in base if x["ID"] == rid), None)
        return {"result": reg} if reg else (400, {"error": "NOT_FOUND", "error_description": "Not found"})
    if metodo == "crm.stagehistory.list":
        itens = [{"ID": str(i), "OWNER_ID": d["ID"], "STAGE_ID": d["STAGE_ID"], "CATEGORY_ID": d["CATEGORY_ID"],
                  "CREATED_TIME": d["MOVED_TIME"], "TYPE_ID": 2} for i, d in enumerate(DEALS, 1)]
        r = listar(itens, params)
        r["result"] = {"items": r["result"]}
        return r
    if metodo in ("bizproc.workflow.template.list",):
        return {"result": [], "total": 0}
    if metodo.startswith(("crm.", "tasks.", "im.", "bizproc.", "user.", "userfieldconfig.")) and \
            metodo.rsplit(".", 1)[-1] in ("add", "update", "delete", "set", "start"):
        with open(ESCRITAS, "a", encoding="utf-8") as f:
            f.write(json.dumps({"metodo": metodo, "params": params}, ensure_ascii=False) + "\n")
        return {"result": True}
    return 400, {"error": "ERROR_METHOD_NOT_FOUND", "error_description": f"Method not found: {metodo}"}


def ler_query(qs):
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
        bruto = self.rfile.read(tamanho) or b"{}"
        try:
            params = json.loads(bruto)
        except ValueError:
            params = ler_query(bruto.decode())
        endereco = urllib.parse.urlparse(self.path)
        for k, v in urllib.parse.parse_qsl(endereco.query):
            params.setdefault(k, v)
        partes = endereco.path.split("/")
        if partes[1:4] != ["rest", "1", TOKEN]:
            return self.responder(401, {"error": "INVALID_CREDENTIALS"})
        metodo = partes[4].removesuffix(".json")
        if metodo == "batch":
            res, err = {}, {}
            for chave, cmd in (params.get("cmd") or {}).items():
                m, _, qs = cmd.partition("?")
                r = executar(m, ler_query(qs))
                if isinstance(r, tuple):
                    err[chave] = r[1]
                else:
                    res[chave] = r["result"]
            return self.responder(200, {"result": {"result": res, "result_error": err}})
        r = executar(metodo, params)
        if isinstance(r, tuple):
            return self.responder(*r)
        self.responder(200, r)

    do_GET = do_POST

    def responder(self, codigo, corpo):
        dados = json.dumps(corpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    ESCRITAS.unlink(missing_ok=True)
    print(f"Portal simulado em http://127.0.0.1:{porta}/rest/1/{TOKEN}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", porta), Portal).serve_forever()
