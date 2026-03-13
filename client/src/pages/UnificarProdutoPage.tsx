import { useRoute, useLocation } from "wouter";
import { UnificarProdutosContent } from "@/components/agrupamento/UnificarProdutosContent";
import { Boxes, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function UnificarProdutoPage() {
    const [, params] = useRoute("/unificar/:cnpj/:codigo");
    const [, setLocation] = useLocation();

    if (!params?.cnpj || !params?.codigo) {
        return (
            <div className="flex items-center justify-center h-screen">
                <p className="text-slate-500 font-bold uppercase tracking-widest">Parâmetros inválidos</p>
            </div>
        );
    }

    const { cnpj, codigo } = params;

    return (
        <div className="min-h-screen bg-slate-100 flex flex-col overflow-hidden">
            {/* Header fixo */}
            <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm z-10 shrink-0">
                <div className="flex items-center gap-4">
                    <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={() => window.close()}
                        className="hover:bg-slate-100 rounded-full"
                    >
                        <ChevronLeft className="h-5 w-5 text-slate-500" />
                    </Button>
                    <div className="flex items-center gap-3">
                        <Boxes className="h-6 w-6 text-blue-600" />
                        <div>
                            <h1 className="text-xl font-black text-slate-900 tracking-tight uppercase leading-none">
                                Unificar Atributos: Código {codigo}
                            </h1>
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">
                                Consolidação de variações fiscais para cadastro oficial • CNPJ {cnpj}
                            </p>
                        </div>
                    </div>
                </div>
                
                <div className="flex items-center gap-2">
                    <div className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full border border-blue-100 text-[10px] font-black uppercase tracking-widest">
                        Modo Tela Cheia
                    </div>
                </div>
            </header>

            {/* Conteúdo Principal */}
            <main className="flex-1 overflow-hidden p-6">
                <div className="max-w-[1800px] mx-auto h-full bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
                    <UnificarProdutosContent 
                        cnpj={cnpj} 
                        codigo={codigo} 
                        onSuccess={() => {
                            // Opcional: fechar a aba se o sucesso for atingido?
                            // toast.success já é disparado pelo componente
                        }}
                        onCancel={() => window.close()}
                        embedded={false}
                    />
                </div>
            </main>
        </div>
    );
}
