from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from fiscal_app.services.pipeline_funcoes_service import ServicoPipelineCompleto


class PipelineWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(
        self,
        service: ServicoPipelineCompleto,
        cnpj: str,
        consultas: list[Path],
        tabelas: list[str],
        data_limite: str | None = None,
    ) -> None:
        super().__init__()
        self.service = service
        self.cnpj = cnpj
        self.consultas = consultas
        self.tabelas = tabelas
        self.data_limite = data_limite

    def run(self) -> None:
        try:
            result = self.service.executar_completo(
                self.cnpj,
                self.consultas,
                self.tabelas,
                self.data_limite,
                progresso=self.progress.emit,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        if result.ok:
            self.finished_ok.emit(result)
        else:
            message = "\n".join(result.erros) if result.erros else "Falha no pipeline oficial."
            self.failed.emit(message or "Falha sem detalhes.")
