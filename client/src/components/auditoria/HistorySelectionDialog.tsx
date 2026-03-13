import { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
    Search,
    Loader2,
    Shield,
    Database,
    BarChart3,
    FileText,
    ChevronRight,
    History
} from "lucide-react";
import { getAuditHistory, type AuditHistorySummary } from "@/lib/pythonApi";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

interface HistorySelectionDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSelect: (cnpj: string) => void;
}

export function HistorySelectionDialog({
    open,
    onOpenChange,
    onSelect,
}: HistorySelectionDialogProps) {
    const [history, setHistory] = useState<AuditHistorySummary[]>([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState("");

    useEffect(() => {
        if (open) {
            loadHistory();
        }
    }, [open]);

    const loadHistory = async () => {
        setLoading(true);
        try {
            const res = await getAuditHistory();
            if (res.success) {
                setHistory(res.historico);
            }
        } catch (error) {
            console.error("Failed to load history", error);
        } finally {
            setLoading(false);
        }
    };

    const formatCnpj = (value: string) => {
        const digits = value.replace(/\D/g, "").slice(0, 14);
        if (digits.length <= 2) return digits;
        if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`;
        if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`;
        if (digits.length <= 12) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`;
        return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
    };

    const filteredHistory = history.filter((h) =>
        h.cnpj.includes(search.replace(/\D/g, "")) ||
        (h.razao_social && h.razao_social.toLowerCase().includes(search.toLowerCase()))
    );

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[85vh] flex flex-col p-0 overflow-hidden">
                <DialogHeader className="p-6 pb-2">
                    <DialogTitle className="flex items-center gap-2">
                        <History className="h-5 w-5 text-blue-600" />
                        Escolher CNPJ Auditado
                    </DialogTitle>
                    <div className="relative mt-4">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Buscar por CNPJ ou Razão Social..."
                            className="pl-9 h-11"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </DialogHeader>

                <div className="flex-1 overflow-hidden">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-20 gap-3">
                            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                            <p className="text-sm text-muted-foreground">Carregando histórico...</p>
                        </div>
                    ) : history.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 text-center px-10">
                            <History className="h-10 w-10 text-muted-foreground/30 mb-3" />
                            <p className="text-sm font-medium">Nenhum histórico encontrado</p>
                            <p className="text-xs text-muted-foreground mt-1">
                                Realize uma auditoria completa primeiro para que os CNPJs apareçam aqui.
                            </p>
                        </div>
                    ) : (
                        <ScrollArea className="h-full px-6 pb-6">
                            <div className="space-y-2 py-2">
                                {filteredHistory.length === 0 ? (
                                    <p className="text-center py-10 text-sm text-muted-foreground">
                                        Nenhum resultado para "{search}"
                                    </p>
                                ) : (
                                    filteredHistory.map((item) => (
                                        <button
                                            key={item.cnpj}
                                            className="w-full text-left flex items-center justify-between p-4 rounded-xl border border-transparent bg-muted/30 hover:bg-blue-50 hover:border-blue-100 transition-all group"
                                            onClick={() => {
                                                onSelect(item.cnpj);
                                                onOpenChange(false);
                                            }}
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className="h-10 w-10 rounded-full bg-white border shadow-sm flex items-center justify-center group-hover:scale-110 transition-transform">
                                                    <Shield className="h-5 w-5 text-blue-600" />
                                                </div>
                                                <div>
                                                    <p className="font-mono font-bold text-base text-slate-900">
                                                        {formatCnpj(item.cnpj)}
                                                    </p>
                                                    {item.razao_social && (
                                                        <p className="text-xs text-slate-500 font-medium truncate max-w-[320px]" title={item.razao_social}>
                                                            {item.razao_social}
                                                        </p>
                                                    )}
                                                    <div className="flex gap-3 mt-1.5">
                                                        <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-normal bg-white">
                                                            <Database className="h-2.5 w-2.5 mr-1" /> {item.qtd_parquets} tab
                                                        </Badge>
                                                        <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-normal bg-white">
                                                            <BarChart3 className="h-2.5 w-2.5 mr-1" /> {item.qtd_analises} an
                                                        </Badge>
                                                        <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-normal bg-white">
                                                            <FileText className="h-2.5 w-2.5 mr-1" /> {item.qtd_relatorios} rel
                                                        </Badge>
                                                    </div>
                                                </div>
                                            </div>
                                            <ChevronRight className="h-5 w-5 text-slate-400 group-hover:translate-x-1 transition-transform" />
                                        </button>
                                    ))
                                )}
                            </div>
                        </ScrollArea>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
