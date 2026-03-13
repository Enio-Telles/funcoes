import React from "react";
import ParquetViewer from "@/components/ParquetViewer";
import { useLocation } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

function useQuery() {
  const [, setLoc] = useLocation();
  const params = new URLSearchParams(window.location.search);
  const get = (k: string) => params.get(k) || "";
  const backToTables = () => setLoc("/tabelas");
  return { get, backToTables };
}

export default function ParquetView() {
  const { get, backToTables } = useQuery();
  const filePath = get("file_path");

  if (!filePath) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Abrir Arquivo Parquet</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="text-sm text-muted-foreground">Nenhum arquivo informado. Use a tela "Visualizar Tabelas" para abrir arquivos.</div>
          <Button onClick={backToTables}>Voltar</Button>
        </CardContent>
      </Card>
    );
  }

  return <ParquetViewer filePath={filePath} />;
}
