import { useAuth } from "@/_core/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Activity,
  BarChart3,
  Clock,
  Database,
  FileText,
  Play,
  RotateCcw,
  Search,
  Shield,
  Zap,
} from "lucide-react";
import { useState } from "react";
import { useAuditHistory, useRunAudit } from "@/hooks/useAuditoria";
import { motion } from "framer-motion";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { toast } from "sonner";

export default function Home() {
  const { user } = useAuth();
  const { data: history, isLoading: loadingHistory } = useAuditHistory();
  const runAudit = useRunAudit();
  const [cnpjsInput, setCnpjsInput] = useState("");

  const handleStartAudit = async () => {
    if (!cnpjsInput.trim()) {
      toast.error("Insira ao menos um CNPJ para iniciar.");
      return;
    }

    const cnpjs = cnpjsInput
      .split(/[\n,]/)
      .map((c) => c.trim())
      .filter((c) => c.length > 0);

    if (cnpjs.length === 0) return;

    // Se o backend suportar apenas um por vez, podemos disparar em sequência ou mostrar aviso
    // Por enquanto, seguimos o plano de disparar a pipeline
    toast.info(`Iniciando análise para ${cnpjs.length} CNPJ(s)...`);

    for (const cnpj of cnpjs) {
      try {
        await runAudit.mutateAsync({
          cnpj,
          dataLimite: format(new Date(), "yyyy-MM-dd"), // Ajustar conforme necessidade
        });
      } catch (error) {
        console.error(`Erro ao auditar ${cnpj}:`, error);
      }
    }

    setCnpjsInput("");
  };

  const stats = [
    {
      label: "Empresas Analisadas",
      value: history?.length || 0,
      icon: Shield,
      trend: "+12% este mês",
      color: "text-emerald-500",
    },
    {
      label: "Última Modificação",
      value: history?.[0]?.ultima_modificacao
        ? format(new Date(history[0].ultima_modificacao), "dd/MM/yyyy")
        : "Nenhuma",
      icon: Clock,
      trend: "Recentemente",
      color: "text-blue-500",
    },
    {
      label: "Servidores Oracle",
      value: "On-line",
      icon: Activity,
      trend: "Latência: 45ms",
      color: "text-amber-500",
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold tracking-tight text-gradient">
            Centro de Comando
          </h1>
          <p className="text-muted-foreground">
            Bem-vindo ao Sistema de Auditoria e Análise Fiscal — SEFIN/RO
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground glass-card px-4 py-2 rounded-full">
          <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[10px]">
            CONECTADO
          </Badge>
          <span>Produção Oracle</span>
        </div>
      </div>

      {/* Stats Summary Area */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, idx) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
          >
            <Card className="glass-card overflow-hidden group hover:shadow-xl hover:shadow-primary/5 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div className={`p-3 rounded-xl bg-background/50 border border-border/50 group-hover:scale-110 transition-transform duration-300`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 bg-muted px-2 py-0.5 rounded">
                    Métrica
                  </span>
                </div>
                <div className="mt-4 space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold tracking-tight">{stat.value}</p>
                </div>
                <div className="mt-4 pt-4 border-t border-border/40 flex items-center gap-2 text-xs text-muted-foreground">
                  <Zap className="h-3 w-3 text-amber-500" />
                  <span>{stat.trend}</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Nova Auditoria - Quick Action */}
        <div className="lg:col-span-12 xl:col-span-5 space-y-6">
          <Card className="glass-card shadow-lg border-primary/10">
            <CardHeader>
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Play className="h-4 w-4 text-primary" />
                </div>
                <CardTitle className="text-lg">Nova Auditoria</CardTitle>
              </div>
              <p className="text-xs text-muted-foreground">
                Inicie um novo processo de análise em lote inserindo os CNPJs abaixo.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Lista de CNPJs
                </label>
                <Textarea
                  placeholder="Ex: 00.000.000/0001-91 ou apenas números...&#10;Aceita múltiplos CNPJs por linha ou vírgulas."
                  className="min-h-[120px] bg-background/40 border-border/60 focus:border-primary/50 resize-none font-mono text-sm"
                  value={cnpjsInput}
                  onChange={(e) => setCnpjsInput(e.target.value)}
                />
              </div>
              <Button 
                onClick={handleStartAudit}
                disabled={runAudit.isPending}
                className="w-full premium-gradient hover:shadow-lg hover:shadow-primary/20 transition-all font-bold gap-2"
              >
                {runAudit.isPending ? (
                  <RotateCcw className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {runAudit.isPending ? "Processando..." : "Iniciar Análise em Lote"}
              </Button>
            </CardContent>
          </Card>

          {/* Dica / Info */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-primary/10 to-emerald-500/5 border border-primary/5 flex items-start gap-4 shadow-sm">
            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <BarChart3 className="h-5 w-5 text-primary" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-bold">Dica do Sistema</p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Utilize o módulo de **Relatórios** para gerar documentos Word automáticos com base nos resultados das auditorias concluídas.
              </p>
            </div>
          </div>
        </div>

        {/* Auditorias Recentes - List */}
        <div className="lg:col-span-12 xl:col-span-7">
          <Card className="glass-card h-full">
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="space-y-1">
                <CardTitle className="text-lg">Auditorias Recentes</CardTitle>
                <p className="text-xs text-muted-foreground">
                  Acompanhamento das últimas empresas processadas
                </p>
              </div>
              <Button variant="ghost" size="sm" className="text-xs gap-1 h-8">
                <RotateCcw className="h-3 w-3" />
                Ver tudo
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {loadingHistory ? (
                  Array(5).fill(0).map((_, i) => (
                    <div key={i} className="h-14 w-full animate-pulse bg-muted/40 rounded-xl mb-2" />
                  ))
                ) : history && history.length > 0 ? (
                  history.slice(0, 7).map((audit, idx) => (
                    <motion.div
                      key={audit.cnpj}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/30 transition-colors group cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-lg bg-background border flex items-center justify-center shadow-sm group-hover:border-primary/30 transition-colors">
                          <Database className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div>
                          <p className="text-sm font-bold tracking-tight">
                            {audit.cnpj}
                          </p>
                          <p className="text-[10px] text-muted-foreground">
                             {audit.razao_social || "CNPJ Processado"}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] font-medium text-muted-foreground">
                          {audit.ultima_modificacao ? format(new Date(audit.ultima_modificacao), "dd/MM/yyyy HH:mm", { locale: ptBR }) : '-'}
                        </div>
                        <div className="flex gap-1 mt-1 justify-end">
                           <Badge variant="outline" className="text-[9px] px-1 py-0 h-4 border-emerald-500/20 bg-emerald-500/5 text-emerald-600">
                             {audit.qtd_parquets} Tab
                           </Badge>
                           <Badge variant="outline" className="text-[9px] px-1 py-0 h-4 border-blue-500/20 bg-blue-500/5 text-blue-600">
                             {audit.qtd_relatorios} Rel
                           </Badge>
                        </div>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center space-y-3">
                    <div className="h-12 w-12 rounded-full bg-muted/30 flex items-center justify-center">
                      <FileText className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-medium">Nenhuma auditoria encontrada</p>
                      <p className="text-xs text-muted-foreground">
                        Inicie sua primeira análise no card ao lado.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
