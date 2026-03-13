import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Settings,
  Database,
  FolderOpen,
  Save,
  Shield,
  Palette,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export default function Configuracoes() {
  const [oracleConfig, setOracleConfig] = useState({
    host: "exa01-scan.sefin.ro.gov.br",
    port: "1521",
    service: "sefindw",
  });

  const [paths, setPaths] = useState({
    sqlDir: "",
    defaultOutput: "",
  });

  const [preferences, setPreferences] = useState({
    autoSave: true,
    normalizeColumns: true,
    includeAuxiliary: true,
  });

  const handleSave = () => {
    toast.info("Funcionalidade em desenvolvimento", {
      description: "As configurações serão persistidas no backend.",
    });
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Configurações</h1>
        <p className="text-sm text-muted-foreground">
          Configurações gerais do sistema e preferências do usuário
        </p>
      </div>

      {/* Oracle Connection */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            Conexão Oracle (Padrão)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Host</Label>
              <Input
                value={oracleConfig.host}
                onChange={(e) => setOracleConfig((p) => ({ ...p, host: e.target.value }))}
                className="h-8 text-xs font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Porta</Label>
              <Input
                value={oracleConfig.port}
                onChange={(e) => setOracleConfig((p) => ({ ...p, port: e.target.value }))}
                className="h-8 text-xs font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Serviço</Label>
              <Input
                value={oracleConfig.service}
                onChange={(e) => setOracleConfig((p) => ({ ...p, service: e.target.value }))}
                className="h-8 text-xs font-mono"
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Credenciais (CPF e senha) são informadas na tela de extração e não são armazenadas.
          </p>
        </CardContent>
      </Card>

      {/* Paths */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <FolderOpen className="h-4 w-4 text-primary" />
            Diretórios Padrão
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Pasta de Consultas SQL</Label>
            <Input
              value={paths.sqlDir}
              onChange={(e) => setPaths((p) => ({ ...p, sqlDir: e.target.value }))}
              className="h-8 text-xs font-mono"
              placeholder="/caminho/para/consultas_sql"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Pasta de Saída Padrão</Label>
            <Input
              value={paths.defaultOutput}
              onChange={(e) => setPaths((p) => ({ ...p, defaultOutput: e.target.value }))}
              className="h-8 text-xs font-mono"
              placeholder="/caminho/para/saida"
            />
          </div>
        </CardContent>
      </Card>

      {/* Preferences */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Settings className="h-4 w-4 text-primary" />
            Preferências
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm">Salvar automaticamente</Label>
              <p className="text-xs text-muted-foreground">
                Salvar alterações em tabelas automaticamente
              </p>
            </div>
            <Switch
              checked={preferences.autoSave}
              onCheckedChange={(v) => setPreferences((p) => ({ ...p, autoSave: v }))}
            />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm">Normalizar colunas</Label>
              <p className="text-xs text-muted-foreground">
                Converter nomes de colunas para minúsculas ao extrair
              </p>
            </div>
            <Switch
              checked={preferences.normalizeColumns}
              onCheckedChange={(v) => setPreferences((p) => ({ ...p, normalizeColumns: v }))}
            />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm">Incluir tabelas auxiliares</Label>
              <p className="text-xs text-muted-foreground">
                Extrair tabelas auxiliares por padrão
              </p>
            </div>
            <Switch
              checked={preferences.includeAuxiliary}
              onCheckedChange={(v) => setPreferences((p) => ({ ...p, includeAuxiliary: v }))}
            />
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave}>
        <Save className="h-4 w-4 mr-2" />
        Salvar Configurações
      </Button>
    </div>
  );
}
