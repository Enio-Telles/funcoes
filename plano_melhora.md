# Plano de Implementação: Otimização da Grid de Dados (Visualização de Tabelas)

Este plano detalha as alterações necessárias para melhorar a usabilidade e a estabilidade visual da visualização de tabelas, aproximando a experiência à de ferramentas robustas de análise de dados (como Excel ou DBeaver).

## 1. Transformação do Container Principal (Flexbox)
* **Problema:** A tabela não preenchia o espaço adequadamente e o scroll era limitado.
* **Solução:** Substituir a `div` raiz por um container Flexbox com altura controlada (`flex flex-col h-[calc(100vh-3rem)] gap-4`). Isto permite que o layout saiba exatamente qual é o limite de altura disponível, forçando a tabela a respeitar esse espaço e empurrando a paginação para o fundo.

## 2. Remoção do `<ScrollArea>` e Adoção de Scroll Nativo
* **Problema:** O uso de componentes customizados de scroll (`<ScrollArea>`) entra em conflito com tabelas largas, causando cortes e travamentos na rolagem horizontal.
* **Solução:** * O `<ScrollArea>` em torno da tabela foi totalmente removido.
    * O `<Card>` da tabela agora possui `flex flex-col flex-1 min-h-0`. O `min-h-0` é crucial no Flexbox para impedir que a tabela ultrapasse os limites da janela.
    * A `div` que envolve a `table` recebeu `overflow-auto flex-1 w-full relative`, delegando a gestão da rolagem diretamente ao motor nativo do navegador para máxima performance e fluidez.

## 3. Estabilidade Visual (Bordas e Fundos Opacos)
* **Problema:** Sem linhas verticais, os dados misturam-se visualmente. Elementos com `backdrop-blur` causam lentidão e sobreposição confusa de texto.
* **Solução:**
    * **Bordas de Grid:** Adição da classe `border-r` em todas as tags `<th>` e `<td>` para criar as linhas verticais que separam as colunas.
    * **Fundo Sólido:** Substituição de `backdrop-blur` e transparências (`bg-muted/95`) por cores sólidas (`bg-muted` e `bg-background`).

## 4. Gestão Inteligente de Z-Index (Camadas de Interseção)
* **Problema:** Ao rolar para a direita e para baixo em simultâneo, os cabeçalhos das colunas e a primeira coluna intersetavam-se de forma errada no canto superior esquerdo.
* **Solução:**
    * **`thead` Fixo:** O `thead` como um todo recebeu `sticky top-0 z-30`.
    * **Canto Superior Esquerdo (Interseção):** A célula de cabeçalho `#` e o ícone de lupa na linha de filtros receberam `sticky left-0 z-40`. Sendo `z-40`, ficam sempre por cima da primeira coluna (`z-20`) e dos cabeçalhos normais (`z-30`).
    * **Primeira Coluna Fica (Dados):** Recebeu `sticky left-0 z-20 bg-background` para deslizar por cima do resto da tabela sem transparências.

---

## Código Completo Atualizado: `client/src/pages/Tabelas.tsx`

Substitua o conteúdo atual do ficheiro pelo código abaixo:

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Table2,
  FolderOpen,
  Filter,
  Plus,
  Paintbrush,
  Download,
  MoreVertical,
  Search,
  X,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Trash2,
  Loader2,
  FileUp,
  RefreshCw,
} from "lucide-react";
import { useState, useMemo, useCallback, useEffect } from "react";
import { toast } from "sonner";
import {
  listParquetFiles,
  readParquet,
  writeParquetCell,
  addParquetRow,
  addParquetColumn,
  getUniqueValues,
  type ParquetFileInfo,
  type ParquetReadResponse,
} from "@/lib/pythonApi";

type ColumnStyle = {
  headerColor?: string;
  headerBg?: string;
  cellColor?: string;
  cellBg?: string;
};

type RowStyle = {
  color?: string;
  backgroundColor?: string;
};

export default function Tabelas() {
  // File browser state
  const [directory, setDirectory] = useState("");
  const [files, setFiles] = useState<ParquetFileInfo[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [selectedFile, setSelectedFile] = useState<ParquetFileInfo | null>(null);

  // Folder Browser Dialog State
  const [showFolderBrowser, setShowFolderBrowser] = useState(false);

  // Recent Folders State
  const [recentFolders, setRecentFolders] = useState<{ name: string, path: string }[]>([]);

  // Unique Values State
  const [uniqueValuesCache, setUniqueValuesCache] = useState<Record<string, string[]>>({});
  const [isLoadingUniqueValues, setIsLoadingUniqueValues] = useState<Record<string, boolean>>({});

  // Table data state
  const [tableData, setTableData] = useState<ParquetReadResponse | null>(null);
  const [isLoadingTable, setIsLoadingTable] = useState(false);
  const [localRows, setLocalRows] = useState<Record<string, unknown>[]>([]);
  const [localColumns, setLocalColumns] = useState<string[]>([]);

  // Filters and sort
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 50;

  // Edit state
  const [editingCell, setEditingCell] = useState<{ row: number; col: string } | null>(null);
  const [editValue, setEditValue] = useState("");

  // UI state
  const [showFilterRow, setShowFilterRow] = useState(true);
  const [columnStyles, setColumnStyles] = useState<Record<string, ColumnStyle>>({});
  const [rowStyles, setRowStyles] = useState<Record<number, RowStyle>>({});
  const [showAddColumnDialog, setShowAddColumnDialog] = useState(false);
  const [newColumnName, setNewColumnName] = useState("");
  const [showColorDialog, setShowColorDialog] = useState(false);
  const [colorTarget, setColorTarget] = useState<{ type: "column" | "row"; id: string | number } | null>(null);
  const [tempColor, setTempColor] = useState("#000000");
  const [tempBgColor, setTempBgColor] = useState("#ffffff");
  const [showFileBrowser, setShowFileBrowser] = useState(true);

  // Load Component Mount State
  useEffect(() => {
    try {
      const stored = localStorage.getItem("sefin-audit-recent-folders");
      if (stored) {
        setRecentFolders(JSON.parse(stored));
      }
    } catch {
      // Ignore
    }
  }, []);

  const saveRecentFolder = useCallback((folderPath: string) => {
    if (!folderPath) return;
    setRecentFolders(prev => {
      const name = folderPath.split(/[\\/]/).filter(Boolean).pop() || folderPath;
      const newEntry = { name, path: folderPath };

      const filtered = prev.filter(f => f.path !== folderPath);
      const updated = [newEntry, ...filtered].slice(0, 10);

      localStorage.setItem("sefin-audit-recent-folders", JSON.stringify(updated));
      return updated;
    });
  }, []);

  const removeRecentFolder = useCallback((folderPath: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setRecentFolders(prev => {
      const updated = prev.filter(f => f.path !== folderPath);
      localStorage.setItem("sefin-audit-recent-folders", JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Load files from directory
  const handleLoadFiles = useCallback(async (dirToLoad?: string) => {
    const targetDir = dirToLoad || directory;
    if (!targetDir.trim()) {
      toast.error("Informe um diretório");
      return;
    }
    setDirectory(targetDir);
    setIsLoadingFiles(true);
    try {
      const result = await listParquetFiles(targetDir);
      setFiles(result.files);
      if (result.files.length === 0) {
        toast.info("Nenhum arquivo Parquet encontrado neste diretório");
      } else {
        toast.success(`${result.count} arquivo(s) encontrado(s)`);
        saveRecentFolder(targetDir);
      }
    } catch (err: any) {
      toast.error("Erro ao listar arquivos", { description: err.message });
    } finally {
      setIsLoadingFiles(false);
    }
  }, [directory, saveRecentFolder]);

  const openFolderBrowser = () => {
    setShowFolderBrowser(true);
  };

  // Open a parquet file
  const handleOpenFile = useCallback(async (file: ParquetFileInfo) => {
    setSelectedFile(file);
    setIsLoadingTable(true);
    setShowFileBrowser(false);
    setFilters({});
    setSortColumn(null);
    setCurrentPage(1);
    setColumnStyles({});
    setRowStyles({});
    try {
      const result = await readParquet({
        file_path: file.path,
        page: 1,
        page_size: 5000, 
      });
      setTableData(result);
      setLocalRows(result.rows);
      setLocalColumns(result.columns);
    } catch (err: any) {
      toast.error("Erro ao ler arquivo", { description: err.message });
    } finally {
      setIsLoadingTable(false);
    }
  }, []);

  // Filtered and sorted rows (client-side)
  const filteredRows = useMemo(() => {
    let rows = [...localRows];
    Object.entries(filters).forEach(([col, filterValue]) => {
      if (filterValue) {
        rows = rows.filter((row) =>
          String(row[col] ?? "").toLowerCase().includes(filterValue.toLowerCase())
        );
      }
    });
    if (sortColumn) {
      rows.sort((a, b) => {
        const aVal = String(a[sortColumn] ?? "");
        const bVal = String(b[sortColumn] ?? "");
        const numA = parseFloat(aVal);
        const numB = parseFloat(bVal);
        if (!isNaN(numA) && !isNaN(numB)) {
          return sortDirection === "asc" ? numA - numB : numB - numA;
        }
        return sortDirection === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      });
    }
    return rows;
  }, [localRows, filters, sortColumn, sortDirection]);

  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, currentPage]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));

  const handleSort = (col: string) => {
    if (sortColumn === col) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortColumn(col);
      setSortDirection("asc");
    }
  };

  const handleFetchUniqueValues = async (col: string) => {
    if (!selectedFile || uniqueValuesCache[col]) return;

    setIsLoadingUniqueValues(prev => ({ ...prev, [col]: true }));
    try {
      const result = await getUniqueValues(selectedFile.path, col);
      setUniqueValuesCache(prev => ({ ...prev, [col]: result.values }));
    } catch (err: any) {
      toast.error(`Erro ao buscar valores únicos de ${col}`, { description: err.message });
    } finally {
      setIsLoadingUniqueValues(prev => ({ ...prev, [col]: false }));
    }
  };

  const handleCellDoubleClick = (rowIdx: number, col: string) => {
    const globalIdx = (currentPage - 1) * pageSize + rowIdx;
    setEditingCell({ row: globalIdx, col });
    setEditValue(String(filteredRows[globalIdx]?.[col] ?? ""));
  };

  const handleCellSave = useCallback(async () => {
    if (!editingCell) return;
    const newRows = [...localRows];
    const originalRow = filteredRows[editingCell.row];
    const originalIdx = localRows.indexOf(originalRow);
    if (originalIdx >= 0) {
      newRows[originalIdx] = { ...newRows[originalIdx], [editingCell.col]: editValue };
      setLocalRows(newRows);
    }
    if (selectedFile) {
      try {
        await writeParquetCell({
          file_path: selectedFile.path,
          row_index: originalIdx >= 0 ? originalIdx : editingCell.row,
          column: editingCell.col,
          value: editValue,
        });
      } catch {
        // Falha silenciosa
      }
    }
    setEditingCell(null);
  }, [editingCell, editValue, localRows, filteredRows, selectedFile]);

  const handleAddRow = useCallback(async () => {
    const newRow: Record<string, unknown> = {};
    localColumns.forEach((col) => (newRow[col] = ""));
    setLocalRows((prev) => [...prev, newRow]);
    if (selectedFile) {
      try {
        await addParquetRow(selectedFile.path);
      } catch { /* update local sufficient */ }
    }
    toast.success("Nova linha adicionada");
  }, [localColumns, selectedFile]);

  const handleAddColumn = useCallback(async () => {
    if (!newColumnName.trim()) return;
    const colName = newColumnName.trim().toLowerCase().replace(/\s+/g, "_");
    if (localColumns.includes(colName)) {
      toast.error("Coluna já existe");
      return;
    }
    setLocalColumns((prev) => [...prev, colName]);
    setLocalRows((prev) => prev.map((row) => ({ ...row, [colName]: "" })));
    if (selectedFile) {
      try {
        await addParquetColumn(selectedFile.path, colName);
      } catch { /* local update is sufficient */ }
    }
    setShowAddColumnDialog(false);
    setNewColumnName("");
    toast.success(`Coluna "${colName}" adicionada`);
  }, [newColumnName, localColumns, selectedFile]);

  const handleDeleteRow = useCallback((globalIdx: number) => {
    const row = filteredRows[globalIdx];
    setLocalRows((prev) => prev.filter((r) => r !== row));
    toast.success("Linha removida");
  }, [filteredRows]);

  const openColorDialog = (type: "column" | "row", id: string | number) => {
    setColorTarget({ type, id });
    if (type === "column") {
      const style = columnStyles[id as string] || {};
      setTempColor(style.cellColor || "#000000");
      setTempBgColor(style.cellBg || "#ffffff");
    } else {
      const style = rowStyles[id as number] || {};
      setTempColor(style.color || "#000000");
      setTempBgColor(style.backgroundColor || "#ffffff");
    }
    setShowColorDialog(true);
  };

  const applyColor = () => {
    if (!colorTarget) return;
    if (colorTarget.type === "column") {
      setColumnStyles((prev) => ({
        ...prev,
        [colorTarget.id as string]: {
          ...prev[colorTarget.id as string],
          cellColor: tempColor,
          cellBg: tempBgColor === "#ffffff" ? undefined : tempBgColor,
        },
      }));
    } else {
      setRowStyles((prev) => ({
        ...prev,
        [colorTarget.id as number]: {
          color: tempColor,
          backgroundColor: tempBgColor === "#ffffff" ? undefined : tempBgColor,
        },
      }));
    }
    setShowColorDialog(false);
    toast.success("Cores aplicadas");
  };

  const handleExportCurrent = useCallback(async () => {
    if (!selectedFile) return;
    try {
      const res = await fetch(`/api/python/export/excel-download?file_path=${encodeURIComponent(selectedFile.path)}`);
      if (!res.ok) throw new Error("Falha no download");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = selectedFile.name.replace(".parquet", ".xlsx");
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Arquivo Excel exportado!");
    } catch (err: any) {
      toast.error("Erro ao exportar", { description: err.message });
    }
  }, [selectedFile]);

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] gap-4 pb-4">
      {/* Header Fixo */}
      <div className="flex items-center justify-between shrink-0">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">Visualizar Tabelas</h1>
          <p className="text-sm text-muted-foreground">
            Ler, filtrar, editar e personalizar tabelas Parquet
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFileBrowser(!showFileBrowser)}
          >
            <FolderOpen className="h-4 w-4 mr-1.5" />
            {showFileBrowser ? "Ocultar Arquivos" : "Abrir Arquivo"}
          </Button>
          {selectedFile && (
            <Button variant="outline" size="sm" onClick={handleExportCurrent}>
              <Download className="h-4 w-4 mr-1.5" />
              Exportar Excel
            </Button>
          )}
        </div>
      </div>

      {/* File Browser (colapsável) */}
      {showFileBrowser && (
        <Card className="border shadow-sm shrink-0">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={openFolderBrowser} title="Procurar Pasta">
                <FolderOpen className="h-4 w-4" />
              </Button>
              <Input
                placeholder="Informe o diretório com os arquivos Parquet..."
                value={directory}
                onChange={(e) => setDirectory(e.target.value)}
                className="font-mono text-sm"
                onKeyDown={(e) => e.key === "Enter" && handleLoadFiles()}
              />
              <Button onClick={() => handleLoadFiles()} disabled={isLoadingFiles}>
                {isLoadingFiles ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              </Button>
            </div>

            {recentFolders.length > 0 && (
              <div className="pt-2 flex flex-wrap gap-2 items-center">
                <span className="text-xs text-muted-foreground mr-1">Recentes:</span>
                {recentFolders.map((folder, i) => (
                  <Badge
                    key={`${folder.path}-${i}`}
                    variant="secondary"
                    className="group cursor-pointer hover:bg-muted flex items-center pr-1 h-6"
                    onClick={() => handleLoadFiles(folder.path)}
                    title={folder.path}
                  >
                    <FolderOpen className="h-3 w-3 mr-1.5 opacity-50" />
                    <span className="truncate max-w-[120px]">{folder.name}</span>
                    <button
                      className="ml-1.5 opacity-0 group-hover:opacity-100 p-0.5 hover:bg-background/80 rounded"
                      onClick={(e) => removeRecentFolder(folder.path, e)}
                    >
                      <X className="h-2.5 w-2.5" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}

            {files.length > 0 && (
              <ScrollArea className="max-h-[160px]">
                <div className="space-y-1">
                  {files.map((file) => (
                    <div
                      key={file.path}
                      className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors hover:bg-muted/50 ${selectedFile?.path === file.path ? "bg-primary/5 border border-primary/20" : ""
                        }`}
                      onClick={() => handleOpenFile(file)}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <FileUp className="h-4 w-4 text-emerald-500 shrink-0" />
                        <span className="text-sm font-mono truncate">{file.relative_path || file.name}</span>
                      </div>
                      <div className="flex items-center gap-3 shrink-0 text-xs text-muted-foreground">
                        <span>{file.size_human}</span>
                        <span>{file.rows} linhas</span>
                        <span>{file.columns} cols</span>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      )}

      {/* Loading */}
      {isLoadingTable && (
        <div className="flex items-center justify-center py-16 flex-1">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Carregando tabela...</span>
        </div>
      )}

      {/* Table View */}
      {!isLoadingTable && localColumns.length > 0 && (
        <>
          {/* Toolbar da Tabela */}
          <Card className="border shadow-sm shrink-0">
            <CardContent className="p-3">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono text-xs">
                    {selectedFile?.name || "Tabela"}
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    {filteredRows.length} / {localRows.length} linhas
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    {localColumns.length} colunas
                  </Badge>
                </div>
                <div className="flex items-center gap-1.5">
                  <Button
                    variant={showFilterRow ? "default" : "outline"}
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => setShowFilterRow(!showFilterRow)}
                  >
                    <Filter className="h-3 w-3 mr-1" />
                    Filtros
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-xs" onClick={handleAddRow}>
                    <Plus className="h-3 w-3 mr-1" />
                    Linha
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setShowAddColumnDialog(true)}>
                    <Plus className="h-3 w-3 mr-1" />
                    Coluna
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => {
                      setFilters({});
                      setSortColumn(null);
                    }}
                  >
                    <X className="h-3 w-3 mr-1" />
                    Limpar
                  </Button>
                  {selectedFile && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs"
                      onClick={() => handleOpenFile(selectedFile)}
                    >
                      <RefreshCw className="h-3 w-3 mr-1" />
                      Recarregar
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border shadow-sm flex flex-col flex-1 min-h-0 overflow-hidden">
            <div className="overflow-auto flex-1 w-full bg-background relative">
              <table className="w-full text-xs border-collapse">
                <thead className="sticky top-0 z-30 shadow-sm bg-muted">
                  <tr>
                    {/* Interseção (Canto Superior Esquerdo): Z-Index 40 */}
                    <th className="px-3 py-2 text-left font-semibold text-muted-foreground w-12 border-b border-r sticky left-0 top-0 z-40 bg-muted">
                      #
                    </th>
                    {localColumns.map((col) => (
                      <th
                        key={col}
                        className="px-3 py-2 text-left font-semibold text-muted-foreground border-b border-r whitespace-nowrap group bg-muted sticky top-0 z-30"
                        style={{
                          color: columnStyles[col]?.headerColor,
                          backgroundColor: columnStyles[col]?.headerBg,
                        }}
                      >
                        <div className="flex items-center gap-1.5">
                          <button
                            className="hover:text-foreground transition-colors flex items-center gap-1.5"
                            onClick={() => handleSort(col)}
                          >
                            {col}
                            {sortColumn === col && <ArrowUpDown className="h-3 w-3" />}
                          </button>
                          <DropdownMenu onOpenChange={(open) => { if (open) handleFetchUniqueValues(col); }}>
                            <DropdownMenuTrigger asChild>
                              <button className="opacity-0 group-hover:opacity-100 hover:opacity-100 focus:opacity-100 rounded hover:bg-background/50 p-0.5">
                                <MoreVertical className="h-3 w-3" />
                              </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="start" className="w-56">
                              <DropdownMenuItem onClick={() => openColorDialog("column", col)}>
                                <Paintbrush className="h-3.5 w-3.5 mr-2" />
                                Cores da Coluna
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleSort(col)}>
                                <ArrowUpDown className="h-3.5 w-3.5 mr-2" />
                                Ordenar
                              </DropdownMenuItem>

                              <DropdownMenuSeparator />

                              <div className="px-2 py-1.5">
                                <p className="text-xs font-semibold text-muted-foreground mb-1.5">Valores Únicos ({col})</p>
                                {isLoadingUniqueValues[col] ? (
                                  <div className="flex items-center justify-center p-2 text-muted-foreground text-xs">
                                    <Loader2 className="h-3 w-3 animate-spin mr-1.5" />
                                    Carregando...
                                  </div>
                                ) : uniqueValuesCache[col] && uniqueValuesCache[col].length > 0 ? (
                                  <div className="flex flex-wrap gap-1">
                                    {uniqueValuesCache[col].map((val, i) => (
                                      <Badge
                                        key={i}
                                        variant="secondary"
                                        className="text-[10px] px-1.5 cursor-pointer hover:bg-primary hover:text-primary-foreground max-w-full truncate"
                                        onClick={() => {
                                          if (!showFilterRow) setShowFilterRow(true);
                                          setFilters(prev => ({ ...prev, [col]: val }));
                                        }}
                                        title={val}
                                      >
                                        {val || "(vazio)"}
                                      </Badge>
                                    ))}
                                  </div>
                                ) : (
                                  <p className="text-[10px] text-muted-foreground italic px-1">Nenhum valor encontrado</p>
                                )}
                              </div>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </th>
                    ))}
                    <th className="px-3 py-2 w-8 border-b border-r bg-muted sticky top-0 z-30" />
                  </tr>
                  
                  {/* Linha de Filtros */}
                  {showFilterRow && (
                    <tr className="bg-muted/80">
                      {/* Interseção dos filtros (Z-40 no topo esquerdo) */}
                      <th className="px-3 py-1.5 border-b border-r sticky left-0 z-40 bg-muted">
                        <Search className="h-3.5 w-3.5 text-muted-foreground" />
                      </th>
                      {localColumns.map((col) => (
                        <th key={col} className="px-2 py-1.5 border-b border-r bg-muted/80 font-normal">
                          <Input
                            placeholder="Filtrar..."
                            value={filters[col] || ""}
                            onChange={(e) =>
                              setFilters((prev) => ({ ...prev, [col]: e.target.value }))
                            }
                            className="h-6 text-xs border-0 bg-background/80 rounded px-1.5 focus-visible:ring-1 focus-visible:ring-primary"
                          />
                        </th>
                      ))}
                      <th className="border-b border-r bg-muted/80" />
                    </tr>
                  )}
                </thead>

                {/* Corpo da Tabela */}
                <tbody>
                  {paginatedRows.map((row, rowIdx) => {
                    const globalIdx = (currentPage - 1) * pageSize + rowIdx;
                    const rStyle = rowStyles[globalIdx] || {};
                    return (
                      <tr
                        key={globalIdx}
                        className="hover:bg-primary/5 even:bg-muted/10 transition-colors group"
                        style={{
                          color: rStyle.color,
                          backgroundColor: rStyle.backgroundColor,
                        }}
                      >
                        {/* Coluna Fila Fixa com Fundo Sólido Nativo */}
                        <td className="px-3 py-2 text-muted-foreground border-b border-r font-mono text-[11px] sticky left-0 z-20 bg-background group-even:bg-muted/30 group-hover:bg-muted/50 transition-colors">
                          {globalIdx + 1}
                        </td>
                        
                        {/* Células de Dados */}
                        {localColumns.map((col) => {
                          const isEditing = editingCell?.row === globalIdx && editingCell?.col === col;
                          const cStyle = columnStyles[col] || {};
                          return (
                            <td
                              key={col}
                              className="px-3 py-2 border-b border-r whitespace-nowrap max-w-[250px] truncate"
                              style={{
                                color: rStyle.color || cStyle.cellColor,
                                backgroundColor: rStyle.backgroundColor || cStyle.cellBg,
                              }}
                              title={String(row[col] ?? "")}
                              onDoubleClick={() => handleCellDoubleClick(rowIdx, col)}
                            >
                              {isEditing ? (
                                <Input
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  onBlur={handleCellSave}
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") handleCellSave();
                                    if (e.key === "Escape") setEditingCell(null);
                                  }}
                                  className="h-5 text-xs border-primary px-1 font-mono"
                                  autoFocus
                                />
                              ) : (
                                <span className="font-mono text-[11px]">{String(row[col] ?? "")}</span>
                              )}
                            </td>
                          );
                        })}
                        
                        {/* Coluna de Ação */}
                        <td className="px-1 py-1.5 border-b border-r">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <button className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-muted transition-opacity">
                                <MoreVertical className="h-3 w-3" />
                              </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-36">
                              <DropdownMenuItem onClick={() => openColorDialog("row", globalIdx)}>
                                <Paintbrush className="h-3 w-3 mr-2" />
                                Cores da Linha
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-destructive" onClick={() => handleDeleteRow(globalIdx)}>
                                <Trash2 className="h-3 w-3 mr-2" />
                                Remover Linha
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Paginação Fixa no Rodapé do Card */}
            <div className="flex items-center justify-between px-4 py-2 border-t bg-muted/50 shrink-0">
              <p className="text-xs text-muted-foreground font-medium">
                Mostrando {Math.min((currentPage - 1) * pageSize + 1, filteredRows.length)}–
                {Math.min(currentPage * pageSize, filteredRows.length)} de {filteredRows.length} linhas
              </p>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 w-7 p-0"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => p - 1)}
                >
                  <ChevronLeft className="h-3 w-3" />
                </Button>
                <span className="text-xs px-2 font-mono">
                  {currentPage} / {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 w-7 p-0"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((p) => p + 1)}
                >
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </Card>
        </>
      )}

      {/* Empty State */}
      {!isLoadingTable && localColumns.length === 0 && !showFileBrowser && (
        <Card className="border-dashed flex-1 flex flex-col items-center justify-center min-h-[400px]">
          <CardContent className="flex flex-col items-center justify-center gap-4">
            <Table2 className="h-12 w-12 text-muted-foreground/50" />
            <div className="text-center space-y-1">
              <p className="font-medium">Nenhuma tabela carregada</p>
              <p className="text-sm text-muted-foreground">
                Abra um arquivo Parquet para começar a visualizar e editar dados
              </p>
            </div>
            <Button variant="outline" onClick={() => setShowFileBrowser(true)}>
              <FolderOpen className="h-4 w-4 mr-2" />
              Abrir Arquivo Parquet
            </Button>
          </CardContent>
        </Card>
      )}
      
      {/* Modais omitidos para poupar espaço, mantenha os seus originais (AddColumn e Colors) */}
      <Dialog open={showAddColumnDialog} onOpenChange={setShowAddColumnDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Adicionar Nova Coluna</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-sm">Nome da Coluna</Label>
              <Input
                placeholder="nome_da_coluna"
                value={newColumnName}
                onChange={(e) => setNewColumnName(e.target.value)}
                className="font-mono"
                onKeyDown={(e) => e.key === "Enter" && handleAddColumn()}
              />
              <p className="text-xs text-muted-foreground">
                Use letras minúsculas e underscores. Espaços serão convertidos.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddColumnDialog(false)}>Cancelar</Button>
            <Button onClick={handleAddColumn}>Adicionar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showColorDialog} onOpenChange={setShowColorDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              Personalizar Cores — {colorTarget?.type === "column" ? `Coluna: ${colorTarget.id}` : `Linha: ${(colorTarget?.id as number) + 1}`}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-sm">Cor do Texto</Label>
              <div className="flex items-center gap-2">
                <input type="color" value={tempColor} onChange={(e) => setTempColor(e.target.value)} className="h-8 w-12 rounded border cursor-pointer" />
                <Input value={tempColor} onChange={(e) => setTempColor(e.target.value)} className="font-mono text-sm flex-1" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm">Cor de Fundo</Label>
              <div className="flex items-center gap-2">
                <input type="color" value={tempBgColor} onChange={(e) => setTempBgColor(e.target.value)} className="h-8 w-12 rounded border cursor-pointer" />
                <Input value={tempBgColor} onChange={(e) => setTempBgColor(e.target.value)} className="font-mono text-sm flex-1" />
              </div>
            </div>
            <div className="p-3 rounded-lg border">
              <p className="text-xs text-muted-foreground mb-1">Pré-visualização:</p>
              <div className="p-2 rounded text-sm font-mono" style={{ color: tempColor, backgroundColor: tempBgColor }}>
                Exemplo de texto com as cores selecionadas
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowColorDialog(false)}>Cancelar</Button>
            <Button onClick={applyColor}><Paintbrush className="h-4 w-4 mr-1.5" />Aplicar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}