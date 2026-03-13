import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FolderOpen, ArrowUpCircle, Folder, Loader2 } from "lucide-react";
import { browseDirectory, type BrowseEntry } from "@/lib/pythonApi";
import { toast } from "sonner";

export interface FolderBrowserDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    title?: string;
    initialPath?: string;
    onSelect: (path: string) => void;
}

export function FolderBrowserDialog({ open, onOpenChange, title = "Selecionar Pasta", initialPath, onSelect }: FolderBrowserDialogProps) {
    const [entries, setEntries] = useState<BrowseEntry[]>([]);
    const [currentPath, setCurrentPath] = useState("");
    const [parentPath, setParentPath] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (open) {
            loadPath(initialPath || "");
        }
    }, [open, initialPath]);

    const loadPath = async (path: string) => {
        setIsLoading(true);
        try {
            const result = await browseDirectory(path);
            setCurrentPath(result.current);
            setParentPath(result.parent);
            setEntries(result.entries || []);
        } catch (err: any) {
            if (path !== "") {
                toast.error("Pasta não encontrada, retornando à raiz");
                try {
                    const fallbackResult = await browseDirectory("");
                    setCurrentPath(fallbackResult.current);
                    setParentPath(fallbackResult.parent);
                    setEntries(fallbackResult.entries || []);
                } catch (fallbackErr: any) {
                    toast.error("Erro ao navegar nas pastas", { description: fallbackErr.message });
                }
            } else {
                toast.error("Erro ao navegar nas pastas", { description: err.message });
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelect = () => {
        onSelect(currentPath);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <FolderOpen className="h-4 w-4" />
                        {title}
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-4">
                    <div className="flex items-center gap-2 p-2 bg-muted rounded-md font-mono text-xs overflow-x-auto whitespace-nowrap">
                        <span className="text-muted-foreground mr-1">Atual:</span>
                        {currentPath || "Raiz do Sistema"}
                    </div>

                    <ScrollArea className="h-[300px] border rounded-md p-2">
                        {isLoading ? (
                            <div className="flex items-center justify-center h-full">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : (
                            <div className="space-y-1">
                                {parentPath && (
                                    <Button
                                        variant="ghost"
                                        className="w-full justify-start h-8 px-2"
                                        onClick={() => loadPath(parentPath)}
                                    >
                                        <ArrowUpCircle className="h-4 w-4 mr-2 text-muted-foreground" />
                                        .. (Subir)
                                    </Button>
                                )}
                                {entries.map((entry) => (
                                    <Button
                                        key={entry.path}
                                        variant="ghost"
                                        className="w-full justify-start h-8 px-2 font-normal"
                                        onClick={() => loadPath(entry.path)}
                                    >
                                        <Folder className="h-4 w-4 mr-2 text-primary/70" />
                                        <span className="truncate">{entry.name}</span>
                                    </Button>
                                ))}
                                {entries.length === 0 && !parentPath && (
                                    <div className="text-center py-4 text-sm text-muted-foreground">
                                        Nenhuma pasta encontrada
                                    </div>
                                )}
                            </div>
                        )}
                    </ScrollArea>
                </div>

                <DialogFooter className="sm:justify-between">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancelar
                    </Button>
                    <Button onClick={handleSelect} disabled={!currentPath || isLoading}>
                        Selecionar Pasta Atual
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
