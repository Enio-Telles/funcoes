from __future__ import annotations

import json

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def refresh_logs(window) -> None:
    logs = [json.dumps(log) for log in window.servico_agregacao.ler_linhas_log()]
    window.log_view.setPlainText("\n".join(logs))


def open_cnpj_folder(window) -> None:
    if not window.state.current_cnpj:
        window.show_error("CNPJ não selecionado", "Selecione um CNPJ para abrir a pasta.")
        return

    target = window.parquet_service.cnpj_dir(window.state.current_cnpj)
    if not target.exists():
        window.show_error("Pasta inexistente", f"A pasta {target} ainda não foi criada.")
        return

    QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
