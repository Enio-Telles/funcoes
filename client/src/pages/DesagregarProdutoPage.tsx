import { useLocation, useParams } from "wouter";
import { DesagregarProdutosContent } from "@/components/agrupamento/DesagregarProdutosContent";
import { Card } from "@/components/ui/card";
import { ChevronLeft, SplitSquareHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DesagregarProdutoPage() {
    const { cnpj, codigo } = useParams();
    const [, setLocation] = useLocation();

    if (!cnpj || !codigo) {
        return (
            <div className="flex items-center justify-center h-screen bg-slate-50">
                <p className="text-slate-500 font-bold uppercase tracking-widest">Parâmetros inválidos.</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Header de Navegação */}
            <header className="h-16 bg-white border-b flex items-center justify-between px-8 shrink-0 z-50 shadow-sm">
                <div className="flex items-center gap-4">
                    <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={() => window.close()} 
                        className="rounded-xl hover:bg-slate-100"
                    >
                        <ChevronLeft className="h-5 w-5 text-slate-600" />
                    </Button>
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-600 rounded-xl shadow-lg shadow-purple-200">
                            <SplitSquareHorizontal className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-sm font-black text-slate-900 uppercase tracking-widest leading-none">
                                Desagregação de Cadastro
                            </h1>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mt-1">
                                Origem: <span className="font-mono text-purple-600 font-black">{codigo}</span> • CNPJ: <span className="font-mono text-slate-600">{cnpj}</span>
                            </p>
                        </div>
                    </div>
                </div>
                
                <div className="hidden md:flex items-center border-l border-slate-200 pl-6 ml-6 h-8">
                    <span className="text-[10px] font-black text-slate-300 uppercase tracking-[0.2em]">Painel de Auditoria Fiscal</span>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 overflow-hidden">
                <DesagregarProdutosContent 
                    cnpj={cnpj} 
                    codigo={codigo} 
                    onSuccess={() => {
                        // Opcional: fechar a aba após sucesso ou mostrar mensagem de conclusão
                        setTimeout(() => window.close(), 2000);
                    }}
                    onCancel={() => window.close()}
                />
            </main>
        </div>
    );
}
