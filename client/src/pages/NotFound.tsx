import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { useLocation } from "wouter";

export default function NotFound() {
  const [, setLocation] = useLocation();

  const handleGoHome = () => {
    setLocation("/");
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-lg glass-card border-primary/10 shadow-2xl overflow-hidden">
        <CardContent className="pt-12 pb-12 text-center space-y-6">
          <div className="flex justify-center">
            <div className="relative h-24 w-24">
              <div className="absolute inset-0 bg-rose-500/20 rounded-full animate-ping opacity-25" />
              <div className="relative h-24 w-24 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                <AlertCircle className="h-12 w-12 text-rose-500" />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <h1 className="text-6xl font-black tracking-tighter text-gradient">404</h1>
            <h2 className="text-2xl font-bold tracking-tight">
              Página não encontrada
            </h2>
            <p className="text-muted-foreground max-w-xs mx-auto text-sm leading-relaxed">
              Desculpe, o recurso que você está tentando acessar não existe ou foi movido.
            </p>
          </div>

          <div className="pt-4">
            <Button
              onClick={handleGoHome}
              className="premium-gradient hover:shadow-lg hover:shadow-primary/20 text-white px-8 py-6 rounded-2xl transition-all duration-300 font-bold gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Voltar ao Início
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
