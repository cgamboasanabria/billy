"""Guarda la API key del tutor en el almacen del SO (keyring).

Uso interactivo (enmascara la entrada):

    python Script/guardar_key.py

La key nunca se escribe en un archivo; queda en el keyring del sistema
(servicio 'billy', usuario 'llm_key'). Si se deja vacia, no se guarda nada.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Script.functions.llm_client import store_api_key


def main() -> None:
    key = getpass.getpass(
        "Pegue la API key del tutor (no se mostrara, Enter para saltar): "
    ).strip()
    if not key:
        print("No se guardo ninguna key.")
        return
    store_api_key(key)
    print("Key guardada en el almacen seguro del sistema.")


if __name__ == "__main__":
    main()
