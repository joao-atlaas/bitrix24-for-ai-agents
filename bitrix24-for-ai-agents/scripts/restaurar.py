#!/usr/bin/env python3
"""Monta o lote que desfaz uma alteração, a partir do backup feito antes dela.

    python3 restaurar.py BACKUP.jsonl --metodo crm.deal.update --campos STAGE_ID,ASSIGNED_BY_ID \
        --saida restaurar.json [--ids 10,11,12] [--entity-type-id 1036]

- BACKUP.jsonl é o arquivo do `b24.py backup` (um registro por linha).
- --campos são os campos que a alteração mexeu. Só eles voltam, para não apagar o que outras
  pessoas mudaram depois.
- --ids limita aos registros que de fato foram alterados.
- Para crm.item.update, informe --entity-type-id, e os campos vão em camelCase, como no backup
  feito com crm.item.list.

O arquivo de saída roda com: python3 b24.py batch restaurar.json --confirmar
Confira antes: o script mostra quantos registros e um exemplo. Só a biblioteca padrão do Python.
"""
import argparse
import json
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("backup")
    ap.add_argument("--metodo", required=True, help="ex.: crm.deal.update, crm.lead.update, crm.item.update")
    ap.add_argument("--campos", required=True, help="campos a restaurar, separados por vírgula")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--ids", help="só estes IDs, separados por vírgula")
    ap.add_argument("--entity-type-id", type=int, help="obrigatório para crm.item.update")
    a = ap.parse_args(argv)

    campos = [c.strip() for c in a.campos.split(",") if c.strip()]
    ids = {i.strip() for i in a.ids.split(",")} if a.ids else None
    universal = a.metodo.startswith("crm.item.")
    if universal and not a.entity_type_id:
        print("ERRO: crm.item.update precisa de --entity-type-id.", file=sys.stderr)
        return 2

    comandos, faltando = {}, set()
    with open(a.backup, encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            reg = json.loads(linha)
            rid = str(reg.get("ID") or reg.get("id") or "")
            if not rid or (ids and rid not in ids):
                continue
            valores = {}
            for c in campos:
                if c in reg:
                    valores[c] = reg[c] if reg[c] is not None else ""
                else:
                    faltando.add(c)
            if not valores:
                continue
            params = {"id": int(rid), "fields": valores}
            if universal:
                params["entityTypeId"] = a.entity_type_id
            comandos[f"r{rid}"] = [a.metodo, params]

    if not ids:
        print("AVISO: sem --ids, o lote restaura TODOS os registros do backup. Se só uma parte foi alterada, "
              "passe --ids com os IDs alterados.", file=sys.stderr)
    print("AVISO: o lote devolve o valor do backup. Se alguém mudou o mesmo campo depois da alteração, "
          "essa mudança também volta atrás. Confira antes de rodar.", file=sys.stderr)
    if faltando:
        print(f"AVISO: estes campos não estão no backup e não vão voltar: {', '.join(sorted(faltando))}. "
              "O backup precisa ter sido feito com eles no select.", file=sys.stderr)
    with open(a.saida, "w", encoding="utf-8") as f:
        json.dump(comandos, f, ensure_ascii=False, indent=1)
    exemplo = next(iter(comandos.values()), None)
    print(json.dumps({"registros": len(comandos), "arquivo": a.saida, "exemplo": exemplo}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
