import * as React from "react"
import {
  Calculator,
  Calendar,
  CreditCard,
  FileSearch,
  LayoutDashboard,
  Search,
  Settings,
  Smile,
  User,
} from "lucide-react"

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command"
import { useLocation } from "wouter"

export function GlobalSearch() {
  const [open, setOpen] = React.useState(false)
  const [, setLocation] = useLocation()

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const runCommand = React.useCallback((command: () => void) => {
    setOpen(false)
    command()
  }, [])

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex h-9 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm text-muted-foreground shadow-sm hover:bg-accent hover:text-accent-foreground sm:w-64"
      >
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4" />
          <span>Busca global...</span>
        </div>
        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Digite um comando ou pesquise..." />
        <CommandList>
          <CommandEmpty>Nenhum resultado encontrado.</CommandEmpty>
          <CommandGroup heading="Sugestões">
            <CommandItem onSelect={() => runCommand(() => setLocation("/"))}>
              <LayoutDashboard className="mr-2 h-4 w-4" />
              <span>Início</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => setLocation("/extracao"))}>
              <Search className="mr-2 h-4 w-4" />
              <span>Extração Oracle</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => setLocation("/analises"))}>
              <FileSearch className="mr-2 h-4 w-4" />
              <span>Análises Fiscais</span>
            </CommandItem>
          </CommandGroup>
          <CommandSeparator />
          <CommandGroup heading="Configurações">
            <CommandItem onSelect={() => runCommand(() => setLocation("/configuracoes"))}>
              <Settings className="mr-2 h-4 w-4" />
              <span>Ajustes</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => setLocation("/perfil"))}>
              <User className="mr-2 h-4 w-4" />
              <span>Meu Perfil</span>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
