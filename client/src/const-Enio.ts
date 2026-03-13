export { COOKIE_NAME, ONE_YEAR_MS } from "@shared/const";

// Generate login URL at runtime so redirect URI reflects the current origin.
export const getLoginUrl = () => {
  // Para fins de desenvolvimento local sem o servidor OAuth original,
  // nós apenas redirecionamos direto para uma rota na própria API 
  // que forçará um login automático com um usuário padrão validado.
  return `${window.location.origin}/api/oauth/local-login`;
};
