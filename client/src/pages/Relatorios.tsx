import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FileText,
  FileType,
  Download,
  Loader2,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { generateTimbradoReport, generateDETNotification } from "@/lib/pythonApi";

export default function Relatorios() {
  const [activeTab, setActiveTab] = useState("timbrado");

  const [timbradoData, setTimbradoData] = useState({
    orgao: "GERÊNCIA DE FISCALIZAÇÃO",
    razao_social: "",
    cnpj: "",
    ie: "",
    situacao_ie: "",
    regime_pagamento: "",
    regime_especial: "",
    atividade_principal: "",
    endereco: "",
    num_dsf: "",
    objeto: "Vistoria",
    relato: "",
    conclusao: "",
    afte: "",
    matricula: "",
    data_extenso: "",
    endereco_orgao: "Av. Presidente Dutra, 4250 - Olaria, Porto Velho - RO",
  });

  const [detData, setDetData] = useState({
    razao_social: "",
    cnpj: "",
    ie: "",
    endereco: "",
    dsf: "",
    assunto: "",
    corpo: "",
    prazo: "30",
    afte: "",
    matricula: "",
  });

  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateTimbrado = async () => {
    if (!timbradoData.cnpj || !timbradoData.razao_social) {
      toast.error("Preencha ao menos CNPJ e Razão Social");
      return;
    }
    setIsGenerating(true);
    try {
      await generateTimbradoReport(timbradoData);
      toast.success("Relatório Word gerado com sucesso!");
    } catch (err: any) {
      toast.error("Erro ao gerar relatório", { description: err.message });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateDET = async (format: "html" | "txt") => {
    if (!detData.cnpj || !detData.razao_social) {
      toast.error("Preencha ao menos CNPJ e Razão Social");
      return;
    }
    setIsGenerating(true);
    try {
      await generateDETNotification(detData, format);
      toast.success(`Notificação ${format.toUpperCase()} gerada com sucesso!`);
    } catch (err: any) {
      toast.error("Erro ao gerar notificação", { description: err.message });
    } finally {
      setIsGenerating(false);
    }
  };

  const updateTimbrado = (field: string, value: string) => {
    setTimbradoData((prev) => ({ ...prev, [field]: value }));
  };

  const updateDet = (field: string, value: string) => {
    setDetData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Relatórios</h1>
        <p className="text-sm text-muted-foreground">
          Gerar relatórios oficiais em Word e TXT com modelos SEFIN
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="timbrado" className="gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            Papel Timbrado SEFIN
          </TabsTrigger>
          <TabsTrigger value="det" className="gap-1.5">
            <FileType className="h-3.5 w-3.5" />
            Notificação DET
          </TabsTrigger>
        </TabsList>

        {/* Papel Timbrado SEFIN */}
        <TabsContent value="timbrado" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold">Dados do Contribuinte</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">Razão Social</Label>
                      <Input
                        value={timbradoData.razao_social}
                        onChange={(e) => updateTimbrado("razao_social", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">CNPJ</Label>
                      <Input
                        value={timbradoData.cnpj}
                        onChange={(e) => updateTimbrado("cnpj", e.target.value)}
                        className="h-8 text-xs font-mono"
                        placeholder="00.000.000/0000-00"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">Inscrição Estadual</Label>
                      <Input
                        value={timbradoData.ie}
                        onChange={(e) => updateTimbrado("ie", e.target.value)}
                        className="h-8 text-xs font-mono"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Situação IE</Label>
                      <Select
                        value={timbradoData.situacao_ie}
                        onValueChange={(v) => updateTimbrado("situacao_ie", v)}
                      >
                        <SelectTrigger className="h-8 text-xs">
                          <SelectValue placeholder="Selecione" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ativa">Ativa</SelectItem>
                          <SelectItem value="suspensa">Suspensa</SelectItem>
                          <SelectItem value="cancelada">Cancelada</SelectItem>
                          <SelectItem value="baixada">Baixada</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">Regime de Pagamento</Label>
                      <Input
                        value={timbradoData.regime_pagamento}
                        onChange={(e) => updateTimbrado("regime_pagamento", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Regime Especial</Label>
                      <Input
                        value={timbradoData.regime_especial}
                        onChange={(e) => updateTimbrado("regime_especial", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Atividade Principal</Label>
                    <Input
                      value={timbradoData.atividade_principal}
                      onChange={(e) => updateTimbrado("atividade_principal", e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Endereço</Label>
                    <Input
                      value={timbradoData.endereco}
                      onChange={(e) => updateTimbrado("endereco", e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">DSF</Label>
                    <Input
                      value={timbradoData.num_dsf}
                      onChange={(e) => updateTimbrado("num_dsf", e.target.value)}
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold">Dados do Auditor</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">Nome do AFTE</Label>
                      <Input
                        value={timbradoData.afte}
                        onChange={(e) => updateTimbrado("afte", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Matrícula</Label>
                      <Input
                        value={timbradoData.matricula}
                        onChange={(e) => updateTimbrado("matricula", e.target.value)}
                        className="h-8 text-xs font-mono"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">Órgão</Label>
                      <Input
                        value={timbradoData.orgao}
                        onChange={(e) => updateTimbrado("orgao", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Data por Extenso</Label>
                      <Input
                        value={timbradoData.data_extenso}
                        onChange={(e) => updateTimbrado("data_extenso", e.target.value)}
                        className="h-8 text-xs"
                        placeholder="28 de fevereiro de 2026"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold">Conteúdo do Relatório</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1.5">
                    <Label className="text-xs">1. Objeto</Label>
                    <Input
                      value={timbradoData.objeto}
                      onChange={(e) => updateTimbrado("objeto", e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">2. Relato</Label>
                    <Textarea
                      value={timbradoData.relato}
                      onChange={(e) => updateTimbrado("relato", e.target.value)}
                      className="text-xs min-h-[120px]"
                      placeholder="Descreva o relato da auditoria..."
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">3. Conclusão</Label>
                    <Textarea
                      value={timbradoData.conclusao}
                      onChange={(e) => updateTimbrado("conclusao", e.target.value)}
                      className="text-xs min-h-[80px]"
                      placeholder="Conclusão do relatório..."
                    />
                  </div>
                </CardContent>
              </Card>

              <Button className="w-full" onClick={handleGenerateTimbrado} disabled={isGenerating}>
                {isGenerating ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Gerar Relatório Word (.docx)
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Notificação DET */}
        <TabsContent value="det" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold">Dados do Destinatário</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Razão Social</Label>
                    <Input
                      value={detData.razao_social}
                      onChange={(e) => updateDet("razao_social", e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">CNPJ</Label>
                      <Input
                        value={detData.cnpj}
                        onChange={(e) => updateDet("cnpj", e.target.value)}
                        className="h-8 text-xs font-mono"
                        placeholder="00.000.000/0000-00"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Inscrição Estadual</Label>
                      <Input
                        value={detData.ie}
                        onChange={(e) => updateDet("ie", e.target.value)}
                        className="h-8 text-xs font-mono"
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Endereço</Label>
                    <Input
                      value={detData.endereco}
                      onChange={(e) => updateDet("endereco", e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">DSF</Label>
                    <Input
                      value={detData.dsf}
                      onChange={(e) => updateDet("dsf", e.target.value)}
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold">Dados do Auditor</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">Nome do AFTE</Label>
                      <Input
                        value={detData.afte}
                        onChange={(e) => updateDet("afte", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Matrícula</Label>
                      <Input
                        value={detData.matricula}
                        onChange={(e) => updateDet("matricula", e.target.value)}
                        className="h-8 text-xs font-mono"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold">Conteúdo da Notificação</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Assunto</Label>
                    <Input
                      value={detData.assunto}
                      onChange={(e) => updateDet("assunto", e.target.value)}
                      className="h-8 text-xs"
                      placeholder="Assunto da notificação"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Corpo da Notificação</Label>
                    <Textarea
                      value={detData.corpo}
                      onChange={(e) => updateDet("corpo", e.target.value)}
                      className="text-xs min-h-[200px]"
                      placeholder="Texto da notificação DET..."
                    />
                  </div>
                </CardContent>
              </Card>

              <div className="flex gap-2">
                <Button className="flex-1" onClick={() => handleGenerateDET("html")} disabled={isGenerating}>
                  {isGenerating ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4 mr-2" />
                  )}
                  Gerar HTML
                </Button>
                <Button variant="outline" className="flex-1" onClick={() => handleGenerateDET("txt")} disabled={isGenerating}>
                  <FileType className="h-4 w-4 mr-2" />
                  Gerar TXT
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
