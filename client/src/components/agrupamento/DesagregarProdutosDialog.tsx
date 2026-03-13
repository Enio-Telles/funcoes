import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { SplitSquareHorizontal } from "lucide-react";
import { DesagregarProdutosContent } from "./DesagregarProdutosContent";

interface DesagregarProdutosDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    cnpj: string;
    codigo: string;
    onSuccess: () => void;
}

export function DesagregarProdutosDialog({
    open,
    onOpenChange,
    cnpj,
    codigo,
    onSuccess,
}: DesagregarProdutosDialogProps) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-[95vw] w-[1400px] h-[90vh] flex flex-col p-0 overflow-hidden bg-slate-50 border-none shadow-2xl">
                <DialogHeader className="p-6 pb-4 border-b bg-white shrink-0">
                    <DialogTitle className="flex items-center gap-3 text-xl font-black text-slate-900 uppercase tracking-widest">
                        <div className="p-2 bg-purple-600 rounded-xl">
                            <SplitSquareHorizontal className="h-5 w-5 text-white" />
                        </div>
                        Desagregação Premium: <span className="font-mono text-purple-600 ml-2">{codigo}</span>
                    </DialogTitle>
                </DialogHeader>

                <div className="flex-1 overflow-hidden">
                    <DesagregarProdutosContent 
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
