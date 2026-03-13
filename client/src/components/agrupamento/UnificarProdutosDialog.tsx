import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Boxes } from "lucide-react";
import { UnificarProdutosContent } from "./UnificarProdutosContent";

interface UnificarProdutosDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    cnpj: string;
    codigo: string;
    onSuccess: () => void;
}

export function UnificarProdutosDialog({
    open,
    onOpenChange,
    cnpj,
    codigo,
    onSuccess,
}: UnificarProdutosDialogProps) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-[98vw] w-[1600px] h-[95vh] flex flex-col p-3 overflow-hidden border-none shadow-2xl bg-white/95 backdrop-blur-sm">
                <DialogHeader className="px-2 pb-2 space-y-0.5 shrink-0">
                    <div className="flex items-center gap-2">
                        <Boxes className="h-5 w-5 text-blue-600" />
                        <DialogTitle className="text-xl font-black text-slate-900 tracking-tight uppercase">
                            Unificar Atributos: Código {codigo}
                        </DialogTitle>
                    </div>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                        Consolidação de variações fiscais para cadastro oficial
                    </p>
                </DialogHeader>

                <div className="flex-1 overflow-hidden mt-1">
                    <UnificarProdutosContent 
                        cnpj={cnpj} 
                        codigo={codigo} 
                        onSuccess={() => {
                            onSuccess();
                            onOpenChange(false);
                        }}
                        onCancel={() => onOpenChange(false)}
                        embedded={true}
                    />
                </div>
            </DialogContent>
        </Dialog>
    );
}
