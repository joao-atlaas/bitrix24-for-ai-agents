#!/usr/bin/env python3
"""Lê e grava modelos de processo de negócio do Bitrix24 (arquivos .bpt).

O .bpt é o que o Bitrix24 exporta em Processos de negócio › Exportar: um array do PHP serializado e
comprimido com zlib. Com este script dá para ler o processo sem abrir a tela, comparar duas versões,
mudar um texto e gravar de volta para importar.

    python3 bpt.py resumo processo.bpt            árvore das ações, com o título e o tipo de cada uma
    python3 bpt.py json processo.bpt > p.json     o modelo inteiro em JSON, para ler ou editar
    python3 bpt.py bpt p.json novo.bpt            grava o JSON editado de volta em .bpt
    python3 bpt.py confere processo.bpt           confere se ler e gravar de novo dá o mesmo arquivo

Para importar pela API, o conteúdo do .bpt vai em base64 no campo do arquivo
(bizproc.workflow.template.add ou .update, que exigem contexto de aplicativo: ver references/configurar.md).
Só a biblioteca padrão do Python.
"""
import json
import sys
import zlib


class Leitor:
    """Desserializa o formato do PHP (serialize). Os textos são medidos em bytes."""

    def __init__(self, dados: bytes):
        self.d = dados
        self.i = 0

    def ate(self, marca: bytes) -> bytes:
        fim = self.d.index(marca, self.i)
        trecho = self.d[self.i:fim]
        self.i = fim + len(marca)
        return trecho

    def valor(self):
        tipo = self.d[self.i:self.i + 1]
        self.i += 2  # tipo e ':' (ou ';' no N)
        if tipo == b"N":
            return None
        if tipo == b"b":
            return self.ate(b";") == b"1"
        if tipo == b"i":
            return int(self.ate(b";"))
        if tipo == b"d":
            texto = self.ate(b";").decode()
            return float(texto) if texto not in ("INF", "-INF", "NAN") else texto
        if tipo == b"s":
            tamanho = int(self.ate(b":"))
            self.i += 1  # aspas
            texto = self.d[self.i:self.i + tamanho]
            self.i += tamanho + 2  # aspas e ';'
            return texto.decode("utf-8", errors="surrogateescape")
        if tipo == b"a":
            n = int(self.ate(b":"))
            self.i += 1  # '{'
            itens = [(self.valor(), self.valor()) for _ in range(n)]
            self.i += 1  # '}'
            if [k for k, _ in itens] == list(range(n)):
                return [v for _, v in itens]
            return {str(k): v for k, v in itens}
        if tipo == b"O":
            self.ate(b":")
            classe = self.ate(b":").decode().strip('"')
            n = int(self.ate(b":"))
            self.i += 1
            props = {"__classe__": classe}
            for _ in range(n):
                k = self.valor()
                props[str(k)] = self.valor()
            self.i += 1
            return props
        raise ValueError(f"Tipo desconhecido {tipo!r} na posição {self.i}")


def serializar(v) -> bytes:
    if v is None:
        return b"N;"
    if isinstance(v, bool):
        return b"b:1;" if v else b"b:0;"
    if isinstance(v, int):
        return f"i:{v};".encode()
    if isinstance(v, float):
        return f"d:{repr(v)};".encode()
    if isinstance(v, str):
        b = v.encode("utf-8", errors="surrogateescape")
        return f's:{len(b)}:"'.encode() + b + b'";'
    if isinstance(v, list):
        corpo = b"".join(serializar(i) + serializar(x) for i, x in enumerate(v))
        return f"a:{len(v)}:{{".encode() + corpo + b"}"
    if isinstance(v, dict):
        if "__classe__" in v:
            props = {k: x for k, x in v.items() if k != "__classe__"}
            corpo = b"".join(serializar(k) + serializar(x) for k, x in props.items())
            nome = v["__classe__"]
            return f'O:{len(nome)}:"{nome}":{len(props)}:{{'.encode() + corpo + b"}"
        corpo = b""
        for k, x in v.items():
            chave = int(k) if isinstance(k, str) and k.lstrip("-").isdigit() and str(int(k)) == k else k
            corpo += serializar(chave) + serializar(x)
        return f"a:{len(v)}:{{".encode() + corpo + b"}"
    raise TypeError(f"Não sei serializar {type(v).__name__}")


def descomprimir(caminho):
    bruto = open(caminho, "rb").read()
    try:
        return zlib.decompress(bruto)
    except zlib.error:
        import base64
        return zlib.decompress(base64.b64decode(bruto))


def ler_bpt(caminho):
    return Leitor(descomprimir(caminho)).valor()


def ida_e_volta_igual(caminho):
    """True se ler e gravar de novo reproduz o mesmo conteúdo, byte a byte. Só edite por código
    um modelo que passe nesta conferência."""
    original = descomprimir(caminho)
    return serializar(Leitor(original).valor()) == original


def gravar_bpt(modelo, caminho):
    with open(caminho, "wb") as f:
        f.write(zlib.compress(serializar(modelo)))


def resumo(modelo):
    linhas = [f"Versão do formato: {modelo.get('VERSION')}"]
    for nome in ("PARAMETERS", "VARIABLES", "CONSTANTS"):
        bloco = modelo.get(nome) or {}
        if bloco:
            linhas.append(f"{nome}: " + ", ".join(f"{k} ({(v or {}).get('Name', '')})" for k, v in bloco.items()))

    def andar(ativ, nivel):
        props = ativ.get("Properties") or {}
        titulo = props.get("Title") or ativ.get("Name", "")
        linhas.append("  " * nivel + f"- {titulo} [{ativ.get('Type')}]")
        for filho in ativ.get("Children") or []:
            andar(filho, nivel + 1)

    for raiz in modelo.get("TEMPLATE") or []:
        andar(raiz, 0)
    return "\n".join(linhas)


def main(argv):
    if len(argv) < 2 or argv[0] not in ("resumo", "json", "bpt", "confere"):
        print(__doc__)
        return 2
    if argv[0] == "confere":
        igual = ida_e_volta_igual(argv[1])
        print("OK: a ida e volta reproduz o arquivo byte a byte." if igual else
              "DIFERENTE: este modelo não volta igual. Não edite por código: edite pela tela.")
        return 0 if igual else 1
    if argv[0] == "json" and not ida_e_volta_igual(argv[1]):
        print("AVISO: este modelo não volta igual byte a byte. Leia à vontade, mas não grave de volta "
              "o JSON editado.", file=sys.stderr)
    if argv[0] == "resumo":
        print(resumo(ler_bpt(argv[1])))
    elif argv[0] == "json":
        print(json.dumps(ler_bpt(argv[1]), ensure_ascii=False, indent=2))
    else:
        if len(argv) < 3:
            print("Uso: python3 bpt.py bpt modelo.json saida.bpt")
            return 2
        with open(argv[1], encoding="utf-8") as f:
            gravar_bpt(json.load(f), argv[2])
        print(f"Gravado: {argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
