from __future__ import annotations

from PySide6.QtCore import Qt

from fiscal_app.ui.dialogs import DialogoSelecaoConsultas, DialogoSelecaoTabelas


def refresh_cnpjs(window) -> None:
    known = {record.cnpj for record in window.registry_service.list_records()}
    known.update(window.parquet_service.list_cnpjs())
    current = window.state.current_cnpj
    window.cnpj_list.clear()
    for cnpj in sorted(known):
        window.cnpj_list.addItem(cnpj)
    if current:
        matches = window.cnpj_list.findItems(current, Qt.MatchExactly)
        if matches:
            window.cnpj_list.setCurrentItem(matches[0])


def run_pipeline_for_input(window, worker_cls) -> None:
    try:
        cnpj = window.servico_pipeline_funcoes.servico_extracao.sanitizar_cnpj(window.cnpj_input.text())
    except Exception as exc:
        window.show_error("CNPJ inválido", str(exc))
        return

    consultas_disp = window.servico_pipeline_funcoes.servico_extracao.listar_consultas()
    if not consultas_disp:
        window.show_error("Sem consultas", "Nenhum arquivo .sql encontrado em c:\\funcoes\\consultas_fonte")
        return

    dlg_sql = DialogoSelecaoConsultas(consultas_disp, window)
    if not dlg_sql.exec():
        return
    sql_selecionados = dlg_sql.consultas_selecionadas()

    tabelas_disp = window.servico_pipeline_funcoes.servico_tabelas.listar_tabelas()
    dlg_tab = DialogoSelecaoTabelas(tabelas_disp, window)
    if not dlg_tab.exec():
        return
    tabelas_selecionadas = dlg_tab.tabelas_selecionadas()

    if not sql_selecionados and not tabelas_selecionadas:
        return

    window.btn_run_pipeline.setEnabled(False)
    window.status.showMessage(f"Executando pipeline oficial para {cnpj}...")
    data_limite = window.date_input.date().toString("dd/MM/yyyy")
    window.pipeline_worker = worker_cls(
        window.servico_pipeline_funcoes,
        cnpj,
        sql_selecionados,
        tabelas_selecionadas,
        data_limite,
    )
    window.pipeline_worker.finished_ok.connect(window.on_pipeline_finished)
    window.pipeline_worker.failed.connect(window.on_pipeline_failed)
    window.pipeline_worker.progress.connect(window.status.showMessage)
    window.pipeline_worker.start()


def on_pipeline_finished(window, result) -> None:
    window.btn_run_pipeline.setEnabled(True)
    window.registry_service.upsert(result.cnpj, ran_now=True)
    window.status.showMessage(f"Pipeline oficial concluído para {result.cnpj}.")
    window.refresh_cnpjs()
    matches = window.cnpj_list.findItems(result.cnpj, Qt.MatchExactly)
    if matches:
        window.cnpj_list.setCurrentItem(matches[0])
        window.refresh_file_tree(result.cnpj)
        window.atualizar_aba_conversao()

    tabelas_fluxo = [
        item for item in result.arquivos_gerados
        if item in {"produtos_unidades", "produtos", "produtos_agrupados", "produtos_final", "fatores_conversao"}
    ]
    msg = "\n".join(result.mensagens[-10:]) if result.mensagens else "Processado com sucesso."
    window.show_info(
        "Pipeline oficial concluído",
        f"CNPJ {result.cnpj} processado.\n\n"
        f"Fluxo de produtos: {', '.join(tabelas_fluxo) if tabelas_fluxo else 'sem etapas registradas'}\n\n"
        f"Últimas mensagens:\n{msg}",
    )


def on_pipeline_failed(window, message: str) -> None:
    window.btn_run_pipeline.setEnabled(True)
    window.status.showMessage("Falha na execução do pipeline oficial.")
    window.show_error("Falha no pipeline oficial", message)


def on_cnpj_selected(window) -> None:
    item = window.cnpj_list.currentItem()
    if item is None:
        return
    cnpj = item.text()
    window.state.current_cnpj = cnpj
    window.registry_service.upsert(cnpj, ran_now=False)
    window.refresh_file_tree(cnpj)
    window.atualizar_aba_conversao()
    window.recarregar_historico_agregacao(cnpj)
    window.limpar_rastreabilidade()
