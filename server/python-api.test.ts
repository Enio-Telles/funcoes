import { describe, expect, it, beforeAll, afterAll } from "vitest";
import fs from "node:fs/promises";
import { createTempParquetFixture, type ParquetFixture } from "./_test_utils/parquetFixture";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

/**
 * Tests for the Python API proxy integration.
 * These tests verify that the Express proxy correctly forwards requests
 * to the Python FastAPI backend and returns proper responses.
 */

const PYTHON_API_BASE = "http://localhost:8001";

const isIntegration = process.env.INTEGRATION === "1";
const describeIntegration = isIntegration ? describe : describe.skip;

let fixture: ParquetFixture | null = null;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function generateFixtureParquet(outputParquetPath: string): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const scriptPath = path.join(__dirname, "_test_utils", "generate_parquet_fixture.py");
    const child = spawn("python", [scriptPath, outputParquetPath], {
      stdio: "inherit",
    });
    child.on("error", reject);
    child.on("exit", code => {
      if (code === 0) resolve();
      else reject(new Error(`Fixture generator exited with code ${code}`));
    });
  });
}

beforeAll(async () => {
  if (!isIntegration) return;
  fixture = await createTempParquetFixture();
  await generateFixtureParquet(fixture.parquetPath);
});

afterAll(async () => {
  if (!isIntegration) return;
  if (fixture) await fixture.cleanup();
  fixture = null;
});

describeIntegration("Python API - Health", () => {
  it("returns health status", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/health`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.status).toBe("ok");
    expect(data.engine).toBe("polars");
  });
});

describeIntegration("Python API - CNPJ Validation", () => {
  it("validates a correct CNPJ", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/validate-cnpj?cnpj=11222333000181`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.valid).toBe(true);
    expect(data.cnpj_limpo).toBe("11222333000181");
  });

  it("rejects an invalid CNPJ", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/validate-cnpj?cnpj=00000000000000`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.valid).toBe(false);
  });
});

describeIntegration("Python API - Parquet Operations", () => {
  it("lists parquet files in a directory", async () => {
    const directory = encodeURIComponent(fixture!.baseDir);
    const res = await fetch(`${PYTHON_API_BASE}/api/python/parquet/list?directory=${directory}`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.count).toBeGreaterThan(0);
    expect(data.files).toBeInstanceOf(Array);
    expect(data.files.length).toBeGreaterThan(0);
    // Each file should have required fields
    const file = data.files[0];
    expect(file).toHaveProperty("name");
    expect(file).toHaveProperty("path");
    expect(file).toHaveProperty("rows");
    expect(file).toHaveProperty("columns");
  });

  it("returns 404 for non-existent directory", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/parquet/list?directory=/nonexistent/path`);
    expect(res.status).toBe(404);
  });

  it("reads a parquet file with pagination", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/parquet/read`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: fixture!.parquetPath,
        page: 1,
        page_size: 10,
      }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.columns).toBeInstanceOf(Array);
    expect(data.columns.length).toBeGreaterThan(0);
    expect(data.rows).toBeInstanceOf(Array);
    expect(data.total_rows).toBeGreaterThanOrEqual(5);
    expect(data.rows.length).toBeGreaterThan(0);
    // Check column names
    expect(data.columns).toContain("nfe_numero");
    expect(data.columns).toContain("cnpj_emitente");
    expect(data.columns).toContain("valor_total");
  });

  it("returns 404 for non-existent parquet file", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/parquet/read`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: "/tmp/nonexistent.parquet",
        page: 1,
        page_size: 10,
      }),
    });
    expect(res.status).toBe(404);
  });
});

describeIntegration("Python API - Excel Export", () => {
  it("exports a parquet file to Excel download", async () => {
    const res = await fetch(
      `${PYTHON_API_BASE}/api/python/export/excel-download?file_path=${encodeURIComponent(fixture!.parquetPath)}`
    );
    expect(res.status).toBe(200);
    const contentType = res.headers.get("content-type");
    expect(contentType).toContain("spreadsheetml");
    const arrayBuffer = await res.arrayBuffer();
    expect(arrayBuffer.byteLength).toBeGreaterThan(0);

    // sanity check: save to temp and ensure file is created (optional)
    const outPath = fixture!.parquetPath.replace(/\.parquet$/, ".xlsx");
    await fs.writeFile(outPath, Buffer.from(arrayBuffer));
    const stat = await fs.stat(outPath);
    expect(stat.size).toBeGreaterThan(0);
  });
});

describeIntegration("Python API - Report Generation", () => {
  it("generates a timbrado Word report", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/reports/timbrado`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        razao_social: "Empresa Teste LTDA",
        cnpj: "12.345.678/0001-90",
        ie: "12345678",
        afte: "João da Silva",
        matricula: "300012345",
        objeto: "Vistoria fiscal",
      }),
    });
    expect(res.status).toBe(200);
    const contentType = res.headers.get("content-type");
    expect(contentType).toContain("wordprocessingml");
    const blob = await res.blob();
    expect(blob.size).toBeGreaterThan(0);
  });

  it("generates a DET notification in HTML", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/reports/det-notification`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        razao_social: "Empresa Teste LTDA",
        cnpj: "12.345.678/0001-90",
        ie: "12345678",
        endereco: "Rua Teste, 123",
        dsf: "DSF-001",
        assunto: "Monitoramento Fiscal",
        corpo: "Notificação de teste",
        afte: "João da Silva",
        matricula: "300012345",
      }),
    });
    expect(res.status).toBe(200);
    const text = await res.text();
    expect(text).toContain("NOTIFICAÇÃO");
    expect(text).toContain("Empresa Teste LTDA");
  });

  it("generates a DET notification in TXT", async () => {
    const res = await fetch(`${PYTHON_API_BASE}/api/python/reports/det-notification-txt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        razao_social: "Empresa Teste LTDA",
        cnpj: "12.345.678/0001-90",
        ie: "12345678",
        assunto: "Monitoramento Fiscal",
        corpo: "Notificação de teste",
        afte: "João da Silva",
        matricula: "300012345",
      }),
    });
    expect(res.status).toBe(200);
    const text = await res.text();
    expect(text).toContain("NOTIFICAÇÃO");
    expect(text).toContain("Empresa Teste LTDA");
  });
});
