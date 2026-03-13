import React, { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { FolderBrowserDialog } from "@/components/ui/folder-browser-dialog";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function AnaliseFaturamentoPeriodo() {
  const [inputDir, setInputDir] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [cnpj, setCnpj] = useState("");
  const [dataIni, setDataIni] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [arquivoBase, setArquivoBase] = useState("nfe_saida.parquet");
  const [result, setResult] = useState<{ file?: string; sample?: any[]; rows?: number } | null>(null);
  const [openInput, setOpenInput] = useState(false);
  const [openOutput, setOpenOutput] = useState(false);
  const [loading, setLoading] = useState(false);

  async function runAnalysis() {
    try {
      if (!inputDir || !outputDir) {
        toast.error("Informe diretórios de entrada e saída");
        return;
      }
      setLoading(true);
      setResult(null);
      const res = await fetch("/api/python/analises/analise_faturamento_periodo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input_dir: inputDir,
          cnpj,
          data_ini: dataIni || null,
          data_fim: dataFim || null,
          output_dir: outputDir,
          arquivo_base: arquivoBase || null,
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.detail || "Falha na análise");
      }
      setResult({ file: data.file, sample: data.sample, rows: data.rows });
      toast.success("Análise concluída");
    } catch (e: any) {
      toast.error(e.message || "Erro ao executar a análise");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-4 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Análise de Faturamento por Período</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium">Diretório de Entrada</label>
              <div className="flex gap-2">
                <Input value={inputDir} onChange={(e) => setInputDir(e.target.value)} placeholder="C:\\caminho\\parquets" />
                <Button variant="outline" onClick={() => setOpenInput(true)}>Selecionar</Button>
              </div>
              <FolderBrowserDialog open={openInput} onOpenChange={setOpenInput} onSelect={(p) => setInputDir(p)} />
            </div>

            <div>
              <label className="block text-sm font-medium">Diretório de Saída</label>
              <div className="flex gap-2">
                <Input value={outputDir} onChange={(e) => setOutputDir(e.target.value)} placeholder="C:\\caminho\\saida" />
                <Button variant="outline" onClick={() => setOpenOutput(true)}>Selecionar</Button>
              </div>
              <FolderBrowserDialog open={openOutput} onOpenChange={setOpenOutput} onSelect={(p) => setOutputDir(p)} />
            </div>

            <div>
              <label className="block text-sm font-medium">CNPJ (opcional)</label>
              <Input value={cnpj} onChange={(e) => setCnpj(e.target.value)} placeholder="00.000.000/0000-00" />
            </div>

            <div>
              <label className="block text-sm font-medium">Data Inicial (YYYY-MM-DD)</label>
              <Input value={dataIni} onChange={(e) => setDataIni(e.target.value)} placeholder="2024-01-01" />
            </div>

            <div>
              <label className="block text-sm font-medium">Data Final (YYYY-MM-DD)</label>
              <Input value={dataFim} onChange={(e) => setDataFim(e.target.value)} placeholder="2024-12-31" />
            </div>

            <div>
              <label className="block text-sm font-medium">Arquivo Base (parquet)</label>
              <Input value={arquivoBase} onChange={(e) => setArquivoBase(e.target.value)} placeholder="nfe_saida.parquet" />
            </div>
          </div>

          <Button onClick={runAnalysis} disabled={loading}>
            {loading ? "Processando..." : "Executar"}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Resultado</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-3">
              <strong>Arquivo gerado:</strong> {result.file || "-"}
            </div>
            <div>
              <strong>Prévia (até 10 linhas):</strong>
              <Table>
                <TableHeader>
                  <TableRow>
                    {(result.sample?.[0] ? Object.keys(result.sample[0]) : []).map((k) => (
                      <TableHead key={k}>{k}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(result.sample || []).map((row, idx) => (
                    <TableRow key={idx}>
                      {Object.values(row).map((v: any, i) => (
                        <TableCell key={i}>{String(v)}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
