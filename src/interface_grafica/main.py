"""
Lançador principal do Fiscal Parquet Analyzer refatorado.
Utiliza as melhores práticas de execução de pacotes Python.
"""
import sys
from PySide6.QtWidgets import QApplication
from src.config import inicializar_diretorios
from src.interface_grafica.main_window import MainWindow

def main() -> int:
    # Refatoração 1: Inicializa a estrutura de pastas antes de subir a UI
    inicializar_diretorios()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Fiscal Parquet Analyzer")
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    # Nota: Executar sempre como 'python -m src.interface_grafica.main' na raiz
    sys.exit(main())
