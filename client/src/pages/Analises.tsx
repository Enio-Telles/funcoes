import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Puzzle,
  ArrowRight,
  Calculator,
  BarChart3,
  Zap,
  Activity,
} from "lucide-react";
import { toast } from "sonner";
import { useLocation } from "wouter";
import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartConfig,
} from "@/components/ui/chart";

const chartData = [
  { month: "Jan", total: 450.5 },
  { month: "Fev", total: 380.2 },
  { month: "Mar", total: 520.8 },
  { month: "Abr", total: 490.3 },
  { month: "Mai", total: 610.1 },
  { month: "Jun", total: 580.4 },
];

const pieData = [
  { name: "NFe", value: 400, color: "var(--color-nfe)" },
  { name: "NFCe", value: 300, color: "var(--color-nfce)" },
  { name: "C100", value: 300, color: "var(--color-c100)" },
];

const chartConfig = {
  total: {
    label: "Faturamento (milhões)",
    color: "hsl(var(--primary))",
  },
  nfe: {
    label: "NFe",
    color: "hsl(var(--primary))",
  },
  nfce: {
    label: "NFCe",
    color: "hsl(var(--chart-2))",
  },
  c100: {
    label: "C100",
    color: "hsl(var(--chart-3))",
  },
} satisfies ChartConfig;

const analysisModules = [
  {
    icon: BarChart3,
    title: "Análise de Faturamento por Período",
    description: "Agrupa o faturamento por mês, com filtros por CNPJ e período",
    status: "active" as const,
    color: "text-orange-600",
    bgColor: "bg-orange-50",
    route: "/analises/faturamento-periodo",
  },
  {
    icon: Calculator,
    title: "Cálculo FIFO/PEPS",
    description: "Calcular custo médio ponderado e FIFO para estoque de mercadorias",
    status: "planned" as const,
    color: "text-emerald-600",
    bgColor: "bg-emerald-50",
  },
  {
    icon: BarChart3,
    title: "Análise de Alíquotas",
    description: "Verificar aplicação correta de alíquotas de ICMS por NCM e operação",
    status: "planned" as const,
    color: "text-orange-600",
    bgColor: "bg-orange-50",
  },
  {
    icon: Zap,
    title: "Geração de Tabelas Derivadas",
    description: "Criar novas tabelas a partir de funções Python customizadas aplicadas sobre dados existentes",
    status: "planned" as const,
    color: "text-amber-600",
    bgColor: "bg-amber-50",
  },
];

const statusLabels = {
  active: { label: "Ativo", variant: "default" as const },
  planned: { label: "Planejado", variant: "secondary" as const },
  development: { label: "Em Desenvolvimento", variant: "outline" as const },
};

export default function Analises() {
  const [, navigate] = useLocation();
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Análises</h1>
        <p className="text-sm text-muted-foreground">
          Módulos de cruzamento de dados, cálculos fiscais e geração de tabelas derivadas
        </p>
      </div>

      {/* Info Banner */}
      <Card className="border-dashed border-primary/20 bg-primary/5">
        <CardContent className="p-5 flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
            <Puzzle className="h-5 w-5 text-primary" />
          </div>
          <div className="space-y-1 flex-1">
            <p className="text-sm font-medium">Módulo Expansível</p>
            <p className="text-xs text-muted-foreground">
              Este módulo foi projetado para receber novas análises e cruzamentos de dados.
              Cada análise é executada no backend Python usando Polars, garantindo performance
              mesmo com grandes volumes de dados. Novos módulos podem ser adicionados sem
              alterar a estrutura existente.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              Tendência de Faturamento (Global)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[200px] w-full">
              <BarChart data={chartData}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tickLine={false}
                  tickMargin={10}
                  axisLine={false}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar
                  dataKey="total"
                  fill="var(--color-total)"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              Distribuição por Tipo
            </CardTitle>
          </CardHeader>
          <CardContent className="flex justify-center">
            <ChartContainer config={chartConfig} className="h-[200px] w-full">
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <ChartTooltip content={<ChartTooltipContent />} />
              </PieChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Analysis Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {analysisModules.map((mod) => {
          const status = statusLabels[mod.status];
          return (
            <Card
              key={mod.title}
              className="group cursor-pointer border shadow-sm hover:shadow-md transition-all duration-200 hover:border-primary/30"
              onClick={() => {
                if (mod.route) navigate(mod.route);
                else
                  toast.info("Módulo em planejamento", {
                    description: `"${mod.title}" será implementado como módulo de análise Python.`,
                  });
              }}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className={`h-10 w-10 rounded-lg ${mod.bgColor} flex items-center justify-center`}>
                    <mod.icon className={`h-5 w-5 ${mod.color}`} />
                  </div>
                  <Badge variant={status.variant} className="text-xs">
                    {status.label}
                  </Badge>
                </div>
                <div className="mt-4 space-y-1.5">
                  <h3 className="font-semibold text-sm">{mod.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {mod.description}
                  </p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
