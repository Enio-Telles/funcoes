import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search, Loader2, Shield, Database, BarChart3, FileText, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { AuditHistorySummary } from "@/lib/pythonApi";

interface AuditHistoryListProps {
    history: AuditHistorySummary[];
    loading: boolean;
    onViewHistory: (cnpj: string) => void;
}

export function AuditHistoryList({ history, loading, onViewHistory }: AuditHistoryListProps) {
    const [searchHistory, setSearchHistory] = useState("");

    const formatCnpj = (value: string) => {
        const digits = value.replace(/\D/g, "").slice(0, 14);
        if (digits.length <= 2) return digits;
        if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`;
        if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`;
        if (digits.length <= 12) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`;
        return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
    };

    const filteredHistory = history.filter((h) =>
        h.cnpj.includes(searchHistory.replace(/\D/g, "")) ||
        (h.razao_social && h.razao_social.toLowerCase().includes(searchHistory.toLowerCase()))
    );

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-medium">CNPJs Auditados Recentemente</CardTitle>
                <div className="relative w-64">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Buscar CNPJ ou Razão Social..."
                        className="pl-8"
                        value={searchHistory}
                        onChange={(e) => setSearchHistory(e.target.value)}
                    />
                </div>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : history.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                        Nenhum CNPJ auditado encontrado no sistema.
                    </div>
                ) : (
                    <div className="space-y-4 mt-4">
                        {filteredHistory.length === 0 ? (
                            <div className="text-center py-4 text-sm text-muted-foreground">Nenhum resultado para a busca.</div>
                        ) : (
                            filteredHistory.map((item) => (
                                <div
                                    key={item.cnpj}
                                    className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-muted/50 cursor-pointer transition-colors"
                                    onClick={() => onViewHistory(item.cnpj)}
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                                            <Shield className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <p className="font-mono font-medium text-lg">{formatCnpj(item.cnpj)}</p>
                                            {item.razao_social && (
                                                <p className="text-sm text-muted-foreground font-medium -mt-1 truncate max-w-sm" title={item.razao_social}>
                                                    {item.razao_social}
                                                </p>
                                            )}
                                            <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                                                <span className="flex items-center gap-1"><Database className="h-3 w-3" /> {item.qtd_parquets} tabelas</span>
                                                <span className="flex items-center gap-1"><BarChart3 className="h-3 w-3" /> {item.qtd_analises} análises</span>
                                                <span className="flex items-center gap-1"><FileText className="h-3 w-3" /> {item.qtd_relatorios} relatórios</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        {item.ultima_modificacao && (
                                            <div className="text-right text-xs text-muted-foreground">
                                                <p>Última modif.</p>
                                                <p>{new Date(item.ultima_modificacao).toLocaleDateString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</p>
                                            </div>
                                        )}
                                        <ChevronRight className="h-5 w-5 text-muted-foreground" />
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
