import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import {
    CheckCircle2,
    XCircle,
    AlertCircle,
    Database,
    BarChart3,
    FolderOpen,
    ExternalLink,
    Table2,
    Clock,
    FileText,
    Package,
    Download,
    Loader2,
    Boxes,
    MousePointerClick,
    ListTree,
    GitBranch,
} from "lucide-react";
import { useLocation } from "wouter";
import type { AuditPipelineResponse, AuditFileResult } from "@/lib/pythonApi";
import { downloadRevisaoManualExcel } from "@/lib/pythonApi";

interface AuditResultViewProps {
    result: AuditPipelineResponse;
    elapsed?: string;
}

export function AuditResultView({ result, elapsed }: AuditResultViewProps) {
    const [, navigate] = useLocation();
    const [downloadingRevisao, setDownloadingRevisao] = useState(false);
    const [downloadMsg, setDownloadMsg] = useState<string | null>(null);

    const handleDownloadRevisao = async () => {
        if (!result.cnpj) return;
        const cleanCnpj = result.cnpj.replace(/\D/g, "");
        setDownloadingRevisao(true);
        setDownloadMsg(null);
        try {
            await downloadRevisaoManualExcel(cleanCnpj);
            setDownloadMsg("Download concluído!");
        } catch (err: any) {
            setDownloadMsg(err?.message || "Erro ao baixar planilha");
        } finally {
            setDownloadingRevisao(false);
            setTimeout(() => setDownloadMsg(null), 4000);
        }
    };

    const openParquetInNewTab = (filePath: string) => {
        const url = `/tabelas/view?file_path=${encodeURIComponent(filePath)}`;
        window.open(url, "_blank");
    };

    const FileCard = ({ file, index }: { file: AuditFileResult; index: number }) => (
        <div
            className="flex items-center gap-3 p-3 rounded-lg border bg-muted/30 cursor-pointer hover:bg-primary/5 hover:border-primary/30 transition-all duration-200 group animate-in fade-in slide-in-from-bottom-2"
            style={{ animationDelay: `${index * 50}ms`, animationFillMode: "backwards" }}
            onClick={() => openParquetInNewTab(file.path)}
            title={`Abrir ${file.name} em nova aba`}
        >
            <FolderOpen className="h-4 w-4 text-emerald-500 shrink-0" />
            <div className="space-y-0.5 min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                    {file.rows} linhas, {file.columns} colunas
                    {file.analise && <Badge variant="outline" className="ml-2 text-[9px] py-0">{file.analise}</Badge>}
                </p>
            </div>
            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
        </div>
    );

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
            {/* Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-blue-500/10">
                                <Database className="h-5 w-5 text-blue-500" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{result.arquivos_extraidos?.length || 0}</p>
                                <p className="text-xs text-muted-foreground">Consultas</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-orange-500/10">
                                <Package className="h-5 w-5 text-orange-500" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{result.arquivos_produtos?.length || 0}</p>
                                <p className="text-xs text-muted-foreground">Produtos</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-emerald-500/10">
                                <BarChart3 className="h-5 w-5 text-emerald-500" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{result.arquivos_analises?.length || 0}</p>
                                <p className="text-xs text-muted-foreground">Análises</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-indigo-500/10">
                                <FileText className="h-5 w-5 text-indigo-500" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{result.arquivos_relatorios?.length || 0}</p>
                                <p className="text-xs text-muted-foreground">Relatórios</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${(result.erros?.length || 0) > 0 ? "bg-orange-500/10" : "bg-emerald-500/10"}`}>
                                {(result.erros?.length || 0) > 0 ? (
                                    <AlertCircle className="h-5 w-5 text-orange-500" />
                                ) : (
                                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                )}
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{result.erros?.length || 0}</p>
                                <p className="text-xs text-muted-foreground">Erros</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-violet-500/10">
                                <Clock className="h-5 w-5 text-violet-500" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{elapsed || "Concluído"}</p>
                                <p className="text-xs text-muted-foreground">Tempo</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Etapas Detail */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Agrupamento de Produtos */}
                <Card className="border-orange-500/20">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <Package className="h-4 w-4 text-orange-500" />
                            Unificação de Produtos
                            <Badge variant="outline" className="ml-auto text-xs">
                                {(result.arquivos_produtos?.length || 0)} arquivos
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[350px]">
                            <div className="space-y-1.5">
                                {(result.arquivos_produtos?.length || 0) > 0 ? (
                                    result.arquivos_produtos.map((file, i) => (
                                        <FileCard key={file.path} file={file} index={i} />
                                    ))
                                ) : (
                                    <div className="flex items-center justify-center py-8 text-xs text-muted-foreground">
                                        Nenhum arquivo de produtos gerado
                                    </div>
                                )}
                            </div>
                        </ScrollArea>
                        <Separator className="my-3" />
                        <div className="flex items-center justify-between">
                            <code className="text-[10px] text-muted-foreground truncate max-w-[150px]">
                                {result.dir_analises}
                            </code>
                            <div className="flex flex-wrap items-center gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-7 text-xs gap-1.5"
                                    onClick={handleDownloadRevisao}
                                    disabled={downloadingRevisao}
                                    title="Baixar planilha de revisão manual (Excel)"
                                >
                                    {downloadingRevisao ? (
                                        <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                        <Download className="h-3 w-3" />
                                    )}
                                    Revisão Manual
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-7 text-xs gap-1.5 border-orange-200 text-orange-700 bg-orange-50 hover:bg-orange-100 hover:text-orange-800"
                                    onClick={() => {
                                        const cleanCnpj = result.cnpj.replace(/\D/g, "");
                                        const expectedFileName = `produtos_agregados_${cleanCnpj}.parquet`;
                                        const productFile = result.arquivos_produtos?.find(f => f.name === expectedFileName);
                                        const path = productFile ? productFile.path : `${result.dir_analises || ""}/${expectedFileName}`;
                                        const normalizedPath = path.replace(/\\/g, '/');
                                        navigate(`/revisao-manual?cnpj=${cleanCnpj}&file_path=${encodeURIComponent(normalizedPath)}`);
                                    }}
                                    title="Página Interativa: Análises de Agrupamento e Resolução em Lote"
                                >
                                    <Boxes className="h-3 w-3" />
                                    Tabela de Visão
                                </Button>
                                <Separator orientation="vertical" className="h-4 mx-1" />

                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-7 text-xs gap-1.5 border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 hover:text-blue-800"
                                    onClick={() => {
                                        const cleanCnpj = result.cnpj.replace(/\D/g, "");
                                        const expectedFileName = `produtos_agregados_${cleanCnpj}.parquet`;
                                        const productFile = result.arquivos_produtos?.find(f => f.name === expectedFileName);
                                        const path = productFile ? productFile.path : `${result.dir_analises || ""}/${expectedFileName}`;
                                        const normalizedPath = path.replace(/\\/g, '/');
                                        navigate(`/agregacao-selecao?cnpj=${cleanCnpj}&file_path=${encodeURIComponent(normalizedPath)}`);
                                    }}
                                    title="Selecione livremente produtos para agregação manual"
                                >
                                    <MousePointerClick className="h-3 w-3" />
                                    Agregação por Seleção
                                </Button>

                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-7 text-xs gap-1.5 border-emerald-200 text-emerald-700 bg-emerald-50 hover:bg-emerald-100 hover:text-emerald-800 font-bold"
                                    onClick={() => {
                                        const cleanCnpj = result.cnpj.replace(/\D/g, "");
                                        const expectedName = `mapa_auditoria_agregados_${cleanCnpj}.parquet`;
                                        const allFiles = [...(result.arquivos_analises || []), ...(result.arquivos_produtos || [])];
                                        const existingFile = allFiles.find(f => f.name === expectedName);
                                        const path = existingFile ? existingFile.path : `${result.dir_analises || ""}/${expectedName}`;
                                        openParquetInNewTab(path.replace(/\\/g, '/'));
                                    }}
                                    title="Ver resumo de todos os produtos que foram unificados manualmente"
                                >
                                    <ListTree className="h-3 w-3 text-emerald-600" />
                                    Mapa Agregados
                                </Button>

                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-7 text-xs gap-1.5 border-amber-200 text-amber-700 bg-amber-50 hover:bg-amber-100 hover:text-amber-800 font-bold"
                                    onClick={() => {
                                        const cleanCnpj = result.cnpj.replace(/\D/g, "");
                                        const expectedName = `mapa_auditoria_desagregados_${cleanCnpj}.parquet`;
                                        const allFiles = [...(result.arquivos_analises || []), ...(result.arquivos_produtos || [])];
                                        const existingFile = allFiles.find(f => f.name === expectedName);
                                        const path = existingFile ? existingFile.path : `${result.dir_analises || ""}/${expectedName}`;
                                        openParquetInNewTab(path.replace(/\\/g, '/'));
                                    }}
                                    title="Ver itens que foram separados ou renomeados individualmente"
                                >
                                    <GitBranch className="h-3 w-3 text-amber-600" />
                                    Mapa Desagregados
                                </Button>
                                
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 text-xs gap-1.5 text-slate-500"
                                    onClick={() => {
                                        localStorage.setItem("sefin-audit-open-dir", result.dir_analises || "");
                                        navigate("/tabelas");
                                    }}
                                >
                                    <Table2 className="h-3 w-3" />
                                    Arquivos
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Etapa 1: Extração */}
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <Database className="h-4 w-4 text-blue-500" />
                            Dados Extraídos
                            <Badge variant="outline" className="ml-auto text-xs">
                                {(result.arquivos_extraidos?.length || 0)} arquivos
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[350px]">
                            <div className="space-y-1.5">
                                {result.arquivos_extraidos?.map((file, i) => (
                                    <FileCard key={file.path} file={file} index={i} />
                                ))}
                            </div>
                        </ScrollArea>
                        <Separator className="my-3" />
                        <div className="flex items-center justify-between">
                            <code className="text-[10px] text-muted-foreground truncate max-w-[250px]">
                                {result.dir_parquet}
                            </code>
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-7 text-xs gap-1.5"
                                onClick={() => {
                                    localStorage.setItem("sefin-audit-open-dir", result.dir_parquet);
                                    navigate("/tabelas");
                                }}
                            >
                                <Table2 className="h-3 w-3" />
                                Ver Pasta
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Etapa 2: Análises */}
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <BarChart3 className="h-4 w-4 text-emerald-500" />
                            Relatórios e Análises
                            <Badge variant="outline" className="ml-auto text-xs">
                                {(result.arquivos_analises?.length || 0)} arquivos
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {/* Análises status */}
                        {result.etapas?.find((e) => e.etapa === "Análises")?.analises && (
                            <div className="space-y-2 mb-4">
                                {result.etapas.find((e) => e.etapa === "Análises")!.analises!.map((a, i) => (
                                    <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted/30">
                                        {a.status === "sucesso" ? (
                                            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                        ) : a.status === "erro" ? (
                                            <XCircle className="h-4 w-4 text-red-500" />
                                        ) : (
                                            <AlertCircle className="h-4 w-4 text-yellow-500" />
                                        )}
                                        <span className="text-sm font-medium">{a.nome}</span>
                                        <Badge
                                            variant={a.status === "sucesso" ? "default" : a.status === "erro" ? "destructive" : "secondary"}
                                            className="ml-auto text-[10px]"
                                        >
                                            {a.status}
                                        </Badge>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Arquivos de análise */}
                        <ScrollArea className="h-[200px]">
                            <div className="space-y-1.5">
                                {(result.arquivos_analises?.length || 0) > 0 ? (
                                    result.arquivos_analises.map((file, i) => (
                                        <FileCard key={file.path} file={file} index={i} />
                                    ))
                                ) : (
                                    <div className="flex items-center justify-center py-8 text-xs text-muted-foreground">
                                        Nenhum arquivo de análise gerado
                                    </div>
                                )}
                            </div>
                        </ScrollArea>

                        {(result.arquivos_analises?.length || 0) > 0 && (
                            <>
                                <Separator className="my-3" />
                                <div className="flex items-center justify-between">
                                    <code className="text-[10px] text-muted-foreground truncate max-w-[250px]">
                                        {result.dir_analises}
                                    </code>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="h-7 text-xs gap-1.5"
                                        onClick={() => {
                                            localStorage.setItem("sefin-audit-open-dir", result.dir_analises);
                                            navigate("/tabelas");
                                        }}
                                    >
                                        <Table2 className="h-3 w-3" />
                                        Ver Análises
                                    </Button>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Etapa 3: Relatórios */}
            {(result.arquivos_relatorios?.length || 0) > 0 && (
                <Card className="border-indigo-500/20">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <FileText className="h-4 w-4 text-indigo-500" />
                            Documentos Gerados
                            <Badge variant="outline" className="ml-auto text-xs">
                                {(result.arquivos_relatorios?.length || 0)} documentos
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {result.arquivos_relatorios?.map((doc, i) => (
                                <div
                                    key={doc.path}
                                    className="flex items-center gap-3 p-3 rounded-lg border bg-muted/30 group animate-in fade-in slide-in-from-bottom-2"
                                    style={{ animationDelay: `${i * 80}ms`, animationFillMode: "backwards" }}
                                >
                                    <div className={`p-1.5 rounded-md ${(doc.tipo?.includes("Word") || false) ? "bg-blue-500/10" : "bg-gray-500/10"}`}>
                                        <FileText className={`h-4 w-4 ${(doc.tipo?.includes("Word") || false) ? "text-blue-500" : "text-gray-500"}`} />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <p className="text-sm font-medium truncate">{doc.name}</p>
                                        <p className="text-xs text-muted-foreground">{doc.tipo || "Desconhecido"}</p>
                                    </div>
                                    <Badge variant="outline" className="text-[9px] py-0 shrink-0">
                                        {(doc.tipo?.includes("Word") || false) ? "DOCX" : "TXT"}
                                    </Badge>
                                </div>
                            ))}
                        </div>
                        <Separator className="my-3" />
                        <div className="flex items-center justify-between">
                            <code className="text-[10px] text-muted-foreground truncate max-w-[350px]">
                                {result.dir_relatorios}
                            </code>
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-7 text-xs gap-1.5"
                                onClick={() => {
                                    localStorage.setItem("sefin-audit-open-dir", result.dir_relatorios);
                                    navigate("/tabelas");
                                }}
                            >
                                <FolderOpen className="h-3 w-3" />
                                Ver Relatórios
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Erros */}
            {(result.erros?.length || 0) > 0 && (
                <Card className="border-orange-500/30">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-semibold flex items-center gap-2 text-orange-500">
                            <AlertCircle className="h-4 w-4" />
                            Erros ({result.erros?.length || 0})
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[120px]">
                            <div className="space-y-1 font-mono text-xs">
                                {result.erros?.map((erro, i) => (
                                    <p key={i} className="text-orange-600 dark:text-orange-400">{erro}</p>
                                ))}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
