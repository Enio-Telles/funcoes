import { useState, useEffect, useMemo } from "react";
import { useLocation } from "wouter";
import { 
  Boxes, 
  SplitSquareHorizontal, 
  Search, 
  ArrowUpDown, 
  Loader2,
  AlertCircle,
  ChevronLeft,
  FileSpreadsheet,
  CheckCircle2,
  Info
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { readParquet, type ParquetReadResponse } from "@/lib/pythonApi";
import { UnificarProdutosDialog } from "@/components/agrupamento/UnificarProdutosDialog";
import { DesagregarProdutosDialog } from "@/components/agrupamento/DesagregarProdutosDialog";

export default function RevisaoManual() {
  const [location, navigate] = useLocation();
  const searchParams = new URLSearchParams(window.location.search);
  const cnpj = searchParams.get("cnpj") || "";
  const filePath = searchParams.get("file_path") || "";

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ParquetReadResponse | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({
    "requer_revisao_manual": "true"
  });
  const [sortColumn, setSortColumn] = useState<string | undefined>(undefined);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc" | undefined>(undefined);

  const [activeDialog, setActiveDialog] = useState<"unificar" | "desagregar" | null>(null);
  const [selectedCodigo, setSelectedCodigo] = useState<string>("");

  useEffect(() => {
    if (filePath) {
      loadData();
    }
  }, [filePath, filters, sortColumn, sortDirection]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await readParquet({
        file_path: filePath,
        page: 1,
        page_size: 1000, // Load a good amount for manual review
        filters,
        sort_column: sortColumn,
        sort_direction: sortDirection
      });
      setData(res);
    } catch (error) {
      console.error("Erro ao carregar dados para revisão:", error);
      toast.error("Erro ao carregar dados", {
        description: "Não foi possível carrergar a tabela de produtos para revisão."
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(prev => prev === "asc" ? "desc" : prev === "desc" ? undefined : "asc");
      if (sortDirection === "desc") setSortColumn(undefined);
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const filteredRows = useMemo(() => {
    if (!data) return [];
    return data.rows;
  }, [data]);

  if (!filePath) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <h2 className="text-xl font-semibold">Nenhum arquivo selecionado</h2>
        <p className="text-muted-foreground">Selecione um arquivo de auditoria para iniciar a revisão manual.</p>
        <Button onClick={() => navigate("/auditar")}>Ir para Auditoria</Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => window.history.back()}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-2xl font-bold tracking-tight text-slate-800">Revisão Manual de Produtos</h1>
          </div>
          <p className="text-muted-foreground flex items-center gap-2">
            <Badge variant="outline" className="font-mono bg-slate-50">{cnpj}</Badge>
            <span>Analise e resolva agrupamentos complexos linha a linha.</span>
          </p>
        </div>
        
        <div className="flex items-center gap-2">
           <Button variant="outline" size="sm" className="gap-2" onClick={() => loadData()}>
             <Loader2 className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
             Atualizar
           </Button>
        </div>
      </div>

      <Separator />

      <div className="grid grid-cols-1 gap-6">
        {/* Requisito: Sistemática de Interface */}
        <Card className="border-blue-100 shadow-sm overflow-hidden">
          <CardHeader className="bg-slate-50/80 pb-4 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-lg">Tabela de Revisão</CardTitle>
              </div>
              <Badge variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-100 uppercase text-[10px] font-bold tracking-wider">
                {filteredRows.length} Itens Pendentes
              </Badge>
            </div>
            <CardDescription>
              Ações disponíveis: <strong>Agregar</strong> (consolidar múltiplos registros em um código oficial) ou <strong>Desagregar</strong> (separar um registro aglutinado em novos códigos).
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0 overflow-auto max-h-[70vh]">
            {loading && filteredRows.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
                <p className="text-muted-foreground animate-pulse text-sm">Carregando produtos para revisão...</p>
              </div>
            ) : filteredRows.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3 text-center px-4">
                <div className="h-16 w-16 rounded-full bg-green-50 flex items-center justify-center border border-green-100 mb-2">
                  <CheckCircle2 className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="text-lg font-medium text-slate-800">Parabéns! Revisão Concluída.</h3>
                <p className="text-sm text-muted-foreground max-w-sm">
                  Não existem mais produtos com marcação de revisão manual pendente para este CNPJ.
                </p>
              </div>
            ) : (
              <table className="w-full text-sm border-collapse">
                <thead className="bg-slate-50/50 sticky top-0 z-10 border-b">
                  <tr>
                    {[
                      { key: "chave_produto", label: "CHAVE / CÓDIGO" },
                      { key: "lista_descricao", label: "DESCRIÇÕES ENCONTRADAS" },
                      { key: "ncm_consenso", label: "NCM" },
                      { key: "lista_unid", label: "UNIDADES" },
                      { key: "descricoes_conflitantes", label: "CONFLITOS" }
                    ].map(col => (
                      <th key={col.key} className="px-4 py-3 text-left font-semibold text-slate-700">
                        <button className="flex items-center gap-1 hover:text-blue-600 transition-colors" onClick={() => handleSort(col.key)}>
                          {col.label}
                          {sortColumn === col.key ? (
                            <ArrowUpDown className={`h-3 w-3 ${sortDirection ? 'text-blue-600' : 'text-slate-300'}`} />
                          ) : (
                            <ArrowUpDown className="h-3 w-3 text-slate-300 opacity-0 group-hover:opacity-100" />
                          )}
                        </button>
                      </th>
                    ))}
                    <th className="px-4 py-3 text-center font-semibold text-slate-700 bg-slate-50 sticky right-0 shadow-[-4px_0_10px_rgba(0,0,0,0.02)]">
                      Ações de Decisão
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredRows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors group">
                      <td className="px-4 py-3 font-mono text-xs font-bold text-slate-600">{row.chave_produto as string}</td>
                      <td className="px-4 py-3 max-w-md text-slate-800">
                        <div className="flex flex-col gap-1">
                          {String(row.lista_descricao || "").split(" | ").map((desc, i) => (
                            <span key={i} className={i > 0 ? "text-[10px] text-muted-foreground border-t pt-1 border-slate-100" : "font-medium"}>
                              {desc}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{row.ncm_consenso as string}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {String(row.lista_unid || "").split(", ").map((un, i) => (
                            <Badge key={i} variant="outline" className="text-[10px] uppercase font-bold text-slate-500 bg-slate-50 h-5 px-1.5">
                              {un}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-[10px] text-red-600 max-w-xs italic">
                        {row.descricoes_conflitantes as string}
                      </td>
                      
                      {/* Ações Fixas conforme Requisito 3 */}
                      <td className="px-4 py-3 bg-white/95 sticky right-0 ring-1 ring-slate-100 shadow-[-4px_0_10px_rgba(0,0,0,0.02)]">
                        <div className="flex items-center gap-2 justify-center">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="h-8 text-xs gap-1.5 border-blue-200 text-blue-700 bg-blue-50/50 hover:bg-blue-100 hover:text-blue-800 shadow-sm"
                            onClick={() => {
                              window.open(`/unificar/${cnpj}/${row.chave_produto}`, '_blank');
                            }}
                          >
                            <Boxes className="h-3.5 w-3.5" /> Agregar
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="h-8 text-xs gap-1.5 border-purple-200 text-purple-700 bg-purple-50/50 hover:bg-purple-100 hover:text-purple-800 shadow-sm"
                            onClick={() => {
                              window.open(`/desagregar/${cnpj}/${row.chave_produto}`, '_blank');
                            }}
                          >
                            <SplitSquareHorizontal className="h-3.5 w-3.5" /> Desagregar
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
        
        {/* Info Card explaining rules from agregacao_desagragecao.md */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-slate-50/50 border-dashed">
                <CardHeader className="p-4 pb-2">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                        <Info className="h-3.5 w-3.5" /> Regra de Agregação
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                        Ao agregar, as unidades de medida originais serão consolidadas na lista <strong>lista_unid</strong> e o estoque será unificado sob o código oficial selecionado.
                    </p>
                </CardContent>
            </Card>
            
            <Card className="bg-slate-50/50 border-dashed">
                <CardHeader className="p-4 pb-2">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                        <Info className="h-3.5 w-3.5" /> Regra de Desagregação
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                        Permite separar características aglutinadas em uma mesma linha. Cada novo produto gerado receberá um <strong>novo código único</strong> no sistema.
                    </p>
                </CardContent>
            </Card>
            
            <Card className="bg-slate-50/50 border-dashed">
                <CardHeader className="p-4 pb-2">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                        <Info className="h-3.5 w-3.5" /> Enriquecimento Fiscal
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                        Os pop-ups exibem hierarquia detalhada de <strong>NCM</strong> e segmentos <strong>CEST</strong> baseados em tabelas de referência oficiais de 2024.
                    </p>
                </CardContent>
            </Card>
        </div>
      </div>

      <UnificarProdutosDialog
        open={activeDialog === 'unificar'}
        onOpenChange={(open) => !open && setActiveDialog(null)}
        cnpj={cnpj}
        codigo={selectedCodigo}
        onSuccess={loadData}
      />

      <DesagregarProdutosDialog
        open={activeDialog === 'desagregar'}
        onOpenChange={(open) => !open && setActiveDialog(null)}
        cnpj={cnpj}
        codigo={selectedCodigo}
        onSuccess={loadData}
      />
    </div>
  );
}
