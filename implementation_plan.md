# Sistema de Auditoria e Análise Fiscal - Frontend Improvement

Improve the user interface and user experience of the `sefin_audit_2` application, now renamed to **Sistema de Auditoria e Análise Fiscal**, by leveraging MCP Stitch for premium designs and implementing new features for CNPJ analysis management on the Home page.

## User Review Required

> [!IMPORTANT]
> - The project will be renamed to **Sistema de Auditoria e Análise Fiscal**.
> - The Home page will now feature a "Recently Analyzed CNPJs" section.
> - The Home page will allow initiating audits for single or multiple CNPJs.

## Proposed Changes

### [Stitch Design Phase]

#### [NEW] [Stitch Project](projects/13834223804759897694)
- Generate premium UI versions for:
    - [Home.tsx](file:///c:/Users/eniot/OneDrive%20-%20SECRETARIA%20DE%20ESTADO%20DE%20FINANCAS/Desenvolvimento/sefin_audit_2/client/src/pages/Home.tsx) (Dashboard): New layout showing analyzed CNPJs and quick-start analysis options.
    - [AuditarCNPJ.tsx](file:///c:/Users/eniot/OneDrive%20-%20SECRETARIA%20DE%20ESTADO%20DE%20FINANCAS/Desenvolvimento/sefin_audit_2/client/src/pages/AuditarCNPJ.tsx): Updated with new branding and multiple CNPJ support if applicable.

### [Frontend Implementation Phase]

#### [MODIFY] [App.tsx](file:///c:/Users/eniot/OneDrive%20-%20SECRETARIA%20DE%20ESTADO%20DE%20FINANCAS/Desenvolvimento/sefin_audit_2/client/src/App.tsx)
- Update page titles and branding to "Sistema de Auditoria e Análise Fiscal".

#### [MODIFY] [Home.tsx](file:///c:/Users/eniot/OneDrive%20-%20SECRETARIA%20DE%20ESTADO%20DE%20FINANCAS/Desenvolvimento/sefin_audit_2/client/src/pages/Home.tsx)
- Update main title to "Sistema de Auditoria e Análise Fiscal".
- Implement a section to display analyzed CNPJs using [useAuditHistory](file:///c:/Users/eniot/OneDrive%20-%20SECRETARIA%20DE%20ESTADO%20DE%20FINANCAS/Desenvolvimento/sefin_audit_2/client/src/hooks/useAuditoria.ts#5-15).
- Add functionality to select and initiate analysis for single or multiple CNPJs directly.
- Apply premium "command center" aesthetics (glassmorphism, advanced cards).

#### [MODIFY] [index.css](file:///c:/Users/eniot/OneDrive%20-%20SECRETARIA%20DE%20ESTADO%20DE%20FINANCAS/Desenvolvimento/sefin_audit_2/client/src/index.css)
- Add utility classes for the new premium design tokens.

## Verification Plan

### Automated Tests
- `npm run build`: Verify build success.
- `vitest`: Ensure existing logic remains functional.

### Manual Verification
1.  **Branding Check**: Verify the new project name appears throughout the UI.
2.  **Analyzed CNPJs List**: Ensure the Home page correctly displays the list of recently processed CNPJs.
3.  **Multi-CNPJ Initiation**: Test initiating an analysis for multiple CNPJs from the Home page.
