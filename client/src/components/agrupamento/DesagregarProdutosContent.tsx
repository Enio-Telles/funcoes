import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, SplitSquareHorizontal, Info, Plus, ChevronRight, X } from "lucide-react";
import { getProdutoDetalhes, resolverManualDesagregar, getNcmDetails, getCestDetails, type NcmDetailsResponse, type CestDetailsResponse } from "@/lib/pythonApi";
import { toast } from "sonner";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

interface DesagregarProdutosContentProps {
    cnpj: string;
    codigo: string;
    onSuccess: () => void;
    onCancel: () => void;
    embedded?: boolean;
}

interface ProdutoDetalhe {
    fonte: string;
    codigo: string;
    descricao: string;
    ncm: string;
    cest: string;
    gtin: string;
    tipo_item: string;
    descr_compl_c170: string;
    codigo_original?: string;
    descricao_original?: string;
    co_emitente?: string;
}

interface GrupoDesagregacao {
    id: string;
    codigo_novo: string;
    descricao_nova: string;
    ncm_novo: string;
    cest_novo: string;
    gtin_novo: string;
    itens: ProdutoDetalhe[];
}

export function DesagregarProdutosContent({
    cnpj,
    codigo,
    onSuccess,
    onCancel,
    embedded = false
}: DesagregarProdutosContentProps) {
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [itensOriginais, setItensOriginais] = useState<ProdutoDetalhe[]>([]);
    const [grupos, setGrupos] = useState<GrupoDesagregacao[]>([]);
    const [selectedItemIndexes, setSelectedItemIndexes] = useState<number[]>([]);

    // Estados para detalhes fiscais (NCM/CEST) enriquecidos
    const [ncmDetailsMap, setNcmDetailsMap] = useState<Record<string, NcmDetailsResponse["data"]>>({});
    const [cestDetailsMap, setCestDetailsMap] = useState<Record<string, CestDetailsResponse["data"]>>({});
    const [loadingFiscais, setLoadingFiscais] = useState<Record<string, boolean>>({});

    useEffect(() => {
        if (codigo) {
            loadDetails();
        }
    }, [codigo, cnpj]);

    // Busca enriquecimento fiscal para cada grupo quando os campos mudam
    useEffect(() => {
        grupos.forEach(grupo => {
            // NCM
            if (grupo.ncm_novo && !ncmDetailsMap[grupo.ncm_novo] && !loadingFiscais[`ncm_${grupo.ncm_novo}`]) {
                setLoadingFiscais(prev => ({ ...prev, [`ncm_${grupo.ncm_novo}`]: true }));
                getNcmDetails(grupo.ncm_novo)
                    .then(res => {
                        if (res.success) setNcmDetailsMap(prev => ({ ...prev, [grupo.ncm_novo]: res.data }));
                    })
                    .finally(() => setLoadingFiscais(prev => ({ ...prev, [`ncm_${grupo.ncm_novo}`]: false })));
            }
            // CEST
            if (grupo.cest_novo && !cestDetailsMap[grupo.cest_novo] && !loadingFiscais[`cest_${grupo.cest_novo}`]) {
                setLoadingFiscais(prev => ({ ...prev, [`cest_${grupo.cest_novo}`]: true }));
                getCestDetails(grupo.cest_novo)
                    .then(res => {
                        if (res.success) setCestDetailsMap(prev => ({ ...prev, [grupo.cest_novo]: res.data }));
                    })
                    .finally(() => setLoadingFiscais(prev => ({ ...prev, [`cest_${grupo.cest_novo}`]: false })));
            }
        });
    }, [grupos]);

    const loadDetails = async () => {
        setLoading(true);
        try {
            const res = await getProdutoDetalhes(cnpj, codigo);
            if (res.success && res.itens) {
                const itensOrdenados = [...res.itens].sort((a, b) => (a.fonte || '').localeCompare(b.fonte || ''));
                setItensOriginais(itensOrdenados);
                
                const primeiraReq = itensOrdenados[0] || {};
                setGrupos([
                    {
                        id: crypto.randomUUID(),
                        codigo_novo: codigo,
                        descricao_nova: primeiraReq.descricao || "",
                        ncm_novo: primeiraReq.ncm || "",
                        cest_novo: primeiraReq.cest || "",
                        gtin_novo: primeiraReq.gtin || "",
                        itens: [...itensOrdenados]
                    }
                ]);
            }
        } catch (error) {
            toast.error("Erro ao carregar detalhes para desagregação.");
        } finally {
            setLoading(false);
        }
    };

    const handleConfirm = async () => {
        if (grupos.some(g => g.itens.length === 0)) {
            toast.error("Existem grupos vazios. Mova itens ou remova o código.");
            return;
        }
        if (grupos.some(g => !g.descricao_nova.trim())) {
            toast.error("Todos os códigos novos devem ter uma descrição válida.");
            return;
        }

        const itensDecididos: any[] = [];
        grupos.forEach(grupo => {
            grupo.itens.forEach(item => {
                itensDecididos.push({
                    fonte: item.fonte,
                    codigo_original: item.codigo_original || item.codigo,
                    descricao_original: item.descricao_original || item.descricao,
                    codigo_novo: grupo.codigo_novo,
                    descricao_nova: grupo.descricao_nova,
                    ncm_novo: grupo.ncm_novo,
                    cest_novo: grupo.cest_novo,
                    gtin_novo: grupo.gtin_novo,
                    co_emitente: item.co_emitente
                });
            });
        });

        setSaving(true);
        try {
            const res = await resolverManualDesagregar(cnpj, itensDecididos);
            if (res.status === "sucesso") {
                toast.success(res.mensagem);
                onSuccess();
            } else {
                toast.error(res.mensagem);
            }
        } catch (error) {
            toast.error("Erro ao salvar desagregação.");
        } finally {
            setSaving(false);
        }
    };

    const handleCriarNovoGrupo = () => {
        const novoIndex = grupos.length;
        setGrupos([
            ...grupos,
            {
                id: crypto.randomUUID(),
                codigo_novo: `${codigo}_${novoIndex}`,
                descricao_nova: "",
                ncm_novo: "",
                cest_novo: "",
                gtin_novo: "",
                itens: []
            }
        ]);
    };

    const handleMoverItensParaGrupo = (grupoDestinoId: string) => {
        if (selectedItemIndexes.length === 0) return;
        const itensMover = selectedItemIndexes.map(idx => itensOriginais[idx]);
        
        setGrupos(prev => {
            const novosGrupos = [...prev];
            novosGrupos.forEach(g => {
                g.itens = g.itens.filter(item => !itensMover.includes(item));
            });
            const destino = novosGrupos.find(g => g.id === grupoDestinoId);
            if (destino) {
                destino.itens.push(...itensMover);
                if (!destino.descricao_nova && itensMover.length > 0) {
                    destino.descricao_nova = itensMover[0].descricao || "";
                    if (!destino.ncm_novo) destino.ncm_novo = itensMover[0].ncm || "";
                    if (!destino.cest_novo) destino.cest_novo = itensMover[0].cest || "";
                }
            }
            return novosGrupos;
        });
        setSelectedItemIndexes([]);
    };

    const itensAgrupados = useMemo(() => {
        const gruposMap: Record<string, { item: ProdutoDetalhe; indexes: number[] }> = {};
        
        itensOriginais.forEach((item, idx) => {
            const desc = (item.descricao || item.descricao_original || "").toUpperCase().trim();
            const ncm = (item.ncm || "").trim();
            const cest = (item.cest || "").trim();
            const gtin = (item.gtin || "").trim();
            const key = `${desc}|${ncm}|${cest}|${gtin}`;
            
            if (!gruposMap[key]) {
                gruposMap[key] = { item, indexes: [] };
            }
            gruposMap[key].indexes.push(idx);
        });
        
        return Object.values(gruposMap);
    }, [itensOriginais]);

    const toggleItemSelection = (indexes: number[]) => {
        const allSelected = indexes.every(idx => selectedItemIndexes.includes(idx));
        
        if (allSelected) {
            setSelectedItemIndexes(prev => prev.filter(i => !indexes.includes(i)));
        } else {
            setSelectedItemIndexes(prev => {
                const newSelection = [...prev];
                indexes.forEach(idx => {
                    if (!newSelection.includes(idx)) newSelection.push(idx);
                });
                return newSelection;
            });
        }
    };

    const atualizarGrupo = (id: string, campo: keyof GrupoDesagregacao, valor: string) => {
        setGrupos(prev => prev.map(g => g.id === id ? { ...g, [campo]: valor } : g));
    };

    const removerGrupo = (id: string) => {
        setGrupos(prev => {
            const removido = prev.find(g => g.id === id);
            if (!removido) return prev;
            const novos = prev.filter(g => g.id !== id);
            if (novos.length > 0) novos[0].itens.push(...removido.itens);
            return novos;
        });
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-full gap-3 py-20">
                <Loader2 className="h-10 w-10 animate-spin text-purple-600" />
                <p className="text-sm font-black text-slate-600 uppercase tracking-widest">Sincronizando Registros...</p>
            </div>
        );
    }

    return (
        <div className={`flex flex-col h-full bg-slate-50 ${embedded ? "" : "p-0"}`}>
            <div className="flex-1 overflow-hidden">
                <div className="h-full grid grid-cols-1 lg:grid-cols-2 divide-x divide-slate-200 overflow-hidden">
                    {/* Coluna Esquerda: Registros Originais */}
                    <div className="flex flex-col h-full overflow-hidden bg-white/50">
                        <div className="p-4 bg-white border-b shrink-0 flex justify-between items-center shadow-sm z-10">
                            <h3 className="text-blue-900 font-black text-[12px] uppercase tracking-widest flex items-center gap-2">
                                <div className="w-1.5 h-3 bg-blue-600 rounded-full" />
                                Registrar Registros ({itensOriginais.length})
                            </h3>
                            <div className="flex gap-2 items-center">
                                <Badge variant="outline" className="text-slate-500 font-black">
                                    {itensAgrupados.length} ÚNICOS
                                </Badge>
                                <Badge variant="secondary" className={selectedItemIndexes.length > 0 ? "bg-purple-100 text-purple-700 font-black" : "font-black"}>
                                    {selectedItemIndexes.length} SELECIONADOS
                                </Badge>
                            </div>
                        </div>
                        <ScrollArea className="flex-1 p-4">
                            <div className="space-y-3 pb-8">
                                {itensAgrupados.map((grupoAgrupado, gIdx) => {
                                    const { item, indexes } = grupoAgrupado;
                                    const isSelected = indexes.every(idx => selectedItemIndexes.includes(idx));
                                    const isPartiallySelected = !isSelected && indexes.some(idx => selectedItemIndexes.includes(idx));
                                    
                                    const grupoDestinoIdx = grupos.findIndex(g => g.itens.some(i => indexes.includes(itensOriginais.indexOf(i))));
                                    const groupColors = ["bg-blue-600", "bg-emerald-600", "bg-amber-600", "bg-rose-600", "bg-cyan-600"];
                                    
                                    return (
                                        <div 
                                            key={gIdx} 
                                            onClick={() => toggleItemSelection(indexes)}
                                            className={`p-4 rounded-xl border transition-all cursor-pointer relative group ${isSelected ? 'border-purple-500 bg-purple-50 shadow-md ring-1 ring-purple-100' : isPartiallySelected ? 'border-purple-300 bg-purple-50/50' : 'border-slate-200 bg-white hover:border-slate-300 shadow-sm'}`}
                                        >
                                            <div className="flex flex-col gap-2">
                                                <div className="flex justify-between items-start">
                                                    <div className="flex gap-2">
                                                        <Badge variant="outline" className="text-[9px] font-black tracking-widest uppercase border-slate-300 text-slate-500">
                                                            {indexes.length} REGISTRO{indexes.length > 1 ? 'S' : ''}
                                                        </Badge>
                                                        {grupoDestinoIdx >= 0 && (
                                                            <Badge className={`text-[9px] font-black tracking-widest text-white border-none ${groupColors[grupoDestinoIdx % groupColors.length]}`}>
                                                                ALOCADO AO GRUPO {grupoDestinoIdx + 1}
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <div className={`h-5 w-5 rounded-full border-2 flex items-center justify-center transition-all ${isSelected ? 'bg-purple-600 border-purple-600 scale-110 shadow-lg shadow-purple-200' : isPartiallySelected ? 'border-purple-400 bg-purple-200' : 'border-slate-200 group-hover:border-slate-400'}`}>
                                                        {isSelected && <div className="h-2 w-2 bg-white rounded-full" />}
                                                        {isPartiallySelected && <div className="h-1 w-2.5 bg-purple-600 rounded-full" />}
                                                    </div>
                                                </div>
                                                <h4 className="font-bold text-[13px] text-slate-800 leading-snug line-clamp-2 uppercase">
                                                    {item.descricao || item.descricao_original}
                                                </h4>
                                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px] text-slate-500 font-mono">
                                                    <span>NCM: <b className="text-slate-700">{item.ncm || "-"}</b></span>
                                                    <span>CEST: <b className="text-slate-700">{item.cest || "-"}</b></span>
                                                    <span>GTIN: <b className="text-slate-700">{item.gtin || "-"}</b></span>
                                                    <span>TIPO: <b className="text-slate-700">{item.tipo_item || "-"}</b></span>
                                                    <span>DESCR: <b className="text-slate-700">{item.descr_compl_c170 || "-"}</b></span>
                                                    <span>FONTES: <b className="text-slate-700">{Array.from(new Set(indexes.map(idx => itensOriginais[idx].fonte))).join(', ')}</b></span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </ScrollArea>
                    </div>

                    {/* Coluna Direita: Novos Grupos */}
                    <div className="flex flex-col h-full bg-slate-50 overflow-hidden">
                        <div className="p-4 bg-white border-b shrink-0 flex justify-between items-center shadow-sm z-10">
                            <h3 className="text-purple-900 font-black text-[12px] uppercase tracking-widest flex items-center gap-2">
                                <div className="w-1.5 h-3 bg-purple-600 rounded-full" />
                                Definição de Novos Grupos ({grupos.length})
                            </h3>
                            <Button size="sm" onClick={handleCriarNovoGrupo} className="h-8 px-4 bg-purple-600 hover:bg-purple-700 font-black text-[10px] uppercase tracking-widest rounded-lg transition-transform active:scale-95 shadow-lg shadow-purple-100">
                                <Plus className="h-3.5 w-3.5 mr-1" />
                                Adicionar Código
                            </Button>
                        </div>
                        <ScrollArea className="flex-1 p-4">
                            <div className="space-y-6 pb-20">
                                {grupos.map((grupo, idx) => {
                                    const groupColors = ["border-t-blue-600", "border-t-emerald-600", "border-t-amber-600", "border-t-rose-600", "border-t-cyan-600"];
                                    const colorClass = groupColors[idx % groupColors.length];
                                    
                                    return (
                                        <div key={grupo.id} className={`bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition-all ${grupo.itens.length === 0 ? "opacity-60" : "hover:shadow-xl hover:shadow-slate-200/50"}`}>
                                            <div className={`h-1.5 w-full ${colorClass} bg-slate-100 border-t-4`} />
                                            <div className="p-5 space-y-5">
                                                <div className="flex justify-between items-center">
                                                    <div className="flex items-center gap-3">
                                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-black text-sm ${colorClass.replace('border-t-', 'bg-')}`}>
                                                            {idx + 1}
                                                        </div>
                                                        <div>
                                                            <h4 className="font-black text-[11px] text-slate-400 uppercase tracking-widest leading-none">Grupo Destino</h4>
                                                            <p className="text-lg font-black text-slate-900 leading-none mt-1">NOVO ITEM</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        {selectedItemIndexes.length > 0 && (
                                                            <Button 
                                                                size="sm" 
                                                                className="h-8 px-4 bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-100 font-black text-[10px] uppercase tracking-widest rounded-lg group/btn"
                                                                onClick={() => handleMoverItensParaGrupo(grupo.id)}
                                                            >
                                                                <ChevronRight className="h-3.5 w-3.5 mr-1 group-hover/btn:translate-x-1 transition-transform" />
                                                                Mover Para Cá
                                                            </Button>
                                                        )}
                                                        {idx > 0 && (
                                                            <Button 
                                                                variant="ghost" size="icon" className="h-8 w-8 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg"
                                                                onClick={() => removerGrupo(grupo.id)}
                                                            >
                                                                <X className="h-4 w-4" />
                                                            </Button>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                                    <div className="space-y-1.5">
                                                        <Label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Código Novo</Label>
                                                        <Input 
                                                            value={grupo.codigo_novo} 
                                                            onChange={(e) => atualizarGrupo(grupo.id, "codigo_novo", e.target.value)}
                                                            className="h-10 font-mono font-black border-slate-200 focus:border-purple-400 rounded-xl bg-slate-50/50"
                                                        />
                                                    </div>
                                                    <div className="space-y-1.5 md:col-span-2">
                                                        <Label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">NCM</Label>
                                                        <Input 
                                                            value={grupo.ncm_novo} 
                                                            onChange={(e) => atualizarGrupo(grupo.id, "ncm_novo", e.target.value)}
                                                            className="h-10 font-mono border-slate-200 focus:border-purple-400 rounded-xl bg-slate-50/50"
                                                        />
                                                    </div>
                                                    <div className="space-y-1.5 md:col-span-3">
                                                        <Label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Descrição Padronizada</Label>
                                                        <Input 
                                                            value={grupo.descricao_nova} 
                                                            onChange={(e) => atualizarGrupo(grupo.id, "descricao_nova", e.target.value)}
                                                            className="h-10 border-slate-200 focus:border-purple-400 rounded-xl bg-slate-50/50 font-bold"
                                                            placeholder="Digite a descrição oficial para este grupo..."
                                                        />
                                                    </div>
                                                    <div className="space-y-1.5">
                                                        <Label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">CEST</Label>
                                                        <Input 
                                                            value={grupo.cest_novo} 
                                                            onChange={(e) => atualizarGrupo(grupo.id, "cest_novo", e.target.value)}
                                                            className="h-10 font-mono border-slate-200 focus:border-purple-400 rounded-xl bg-slate-50/50"
                                                        />
                                                    </div>
                                                    <div className="space-y-1.5 md:col-span-2">
                                                        <Label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">GTIN</Label>
                                                        <Input 
                                                            value={grupo.gtin_novo} 
                                                            onChange={(e) => atualizarGrupo(grupo.id, "gtin_novo", e.target.value)}
                                                            className="h-10 font-mono border-slate-200 focus:border-purple-400 rounded-xl bg-slate-50/50"
                                                        />
                                                    </div>
                                                </div>

                                                {/* Enriquecimento Fiscal Premium */}
                                                {(grupo.ncm_novo || grupo.cest_novo) && (
                                                    <div className="bg-slate-50 rounded-xl border border-slate-200/50 p-4 space-y-3 shadow-inner">
                                                        {grupo.ncm_novo && ncmDetailsMap[grupo.ncm_novo] && (
                                                            <div className="flex gap-3 items-start">
                                                                <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                                                                    <Info className="h-4 w-4" />
                                                                </div>
                                                                <div className="flex-1 text-[11px] space-y-1 overflow-hidden">
                                                                    <p className="font-black text-blue-800 uppercase tracking-wider">Detalhamento NCM {grupo.ncm_novo}</p>
                                                                    <div className="text-slate-600 leading-relaxed font-medium whitespace-pre-wrap italic">
                                                                        {ncmDetailsMap[grupo.ncm_novo].descricao}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}
                                                        {grupo.cest_novo && cestDetailsMap[grupo.cest_novo] && (
                                                            <div className="flex gap-3 items-start pt-3 border-t border-slate-200/50">
                                                                <div className="p-2 bg-purple-100 rounded-lg text-purple-600">
                                                                    <Info className="h-4 w-4" />
                                                                </div>
                                                                <div className="flex-1 text-[11px] space-y-1 overflow-hidden">
                                                                    <p className="font-black text-purple-800 uppercase tracking-wider">Detalhamento CEST {grupo.cest_novo}</p>
                                                                    <div className="text-slate-600 leading-relaxed font-medium italic">
                                                                        <p><span className="text-slate-400 mr-1">SEGMENTO:</span> {cestDetailsMap[grupo.cest_novo].nome_segmento}</p>
                                                                        <p className="mt-1">{cestDetailsMap[grupo.cest_novo].descricoes?.[0]}</p>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}
                                                        {!ncmDetailsMap[grupo.ncm_novo] && !cestDetailsMap[grupo.cest_novo] && (
                                                            <div className="flex items-center justify-center p-2 opacity-30 text-[10px] font-black uppercase tracking-widest">
                                                                Buscando informações fiscais...
                                                            </div>
                                                        )}
                                                    </div>
                                                )}

                                                <div className="flex justify-between items-center bg-slate-100/50 p-3 rounded-xl border border-slate-200">
                                                    <div className="flex items-center gap-2">
                                                        <Boxes className="h-4 w-4 text-slate-400" />
                                                        <span className="text-[11px] font-black text-slate-500 uppercase tracking-widest">Itens Alocados</span>
                                                    </div>
                                                    <Badge variant="outline" className="font-black text-[11px] tracking-widest border-slate-300 text-slate-700">
                                                        {grupo.itens.length} UNIDADES
                                                    </Badge>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </ScrollArea>
                    </div>
                </div>
            </div>

            {/* Footer de Ações */}
            <div className={`p-4 border-t bg-white flex justify-between items-center shadow-[0_-4px_20px_-10px_rgba(0,0,0,0.1)] shrink-0 z-30 ${embedded ? "" : "px-8"}`}>
                <div className="flex flex-col">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">Resumo da Operação</span>
                    <div className="flex items-center gap-3">
                        <span className="text-[14px] font-black text-slate-700">{grupos.length} GRUPOS</span>
                        <Separator orientation="vertical" className="h-3 bg-slate-300" />
                        <span className="text-[14px] font-black text-slate-400">{grupos.reduce((acc, g) => acc + g.itens.length, 0)} / {itensOriginais.length} ITENS ALOCADOS</span>
                    </div>
                </div>
                <div className="flex gap-3">
                    <Button variant="ghost" onClick={onCancel} className="h-10 px-6 text-[11px] font-black uppercase tracking-widest text-slate-500 hover:text-slate-800 rounded-xl">
                        Descartar
                    </Button>
                    <Button
                        disabled={loading || saving || selectedItemIndexes.length > 0}
                        onClick={handleConfirm}
                        className="h-12 px-12 bg-purple-600 hover:bg-purple-700 shadow-xl shadow-purple-200 font-black text-[14px] uppercase tracking-widest transition-all hover:scale-[1.02] active:scale-[0.98] rounded-xl"
                    >
                        {saving ? (
                            <>
                                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                                Processando...
                            </>
                        ) : "Concluir Desagregação"}
                    </Button>
                </div>
            </div>
        </div>
    );
}

// Re-using Sidebar icons for consistency
function Boxes(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
      <path d="m3.3 7 8.7 5 8.7-5" />
      <path d="M12 22V12" />
    </svg>
  )
}
