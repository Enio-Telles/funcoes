import os from "node:os";
import path from "node:path";
import fs from "node:fs/promises";

export type ParquetFixture = {
  baseDir: string;
  cnpj: string;
  cnpjDir: string;
  parquetPath: string;
  cleanup: () => Promise<void>;
};

/**
 * Creates a deterministic temp directory structure matching the expectations of python-api.test.ts.
 *
 * NOTE: This helper only creates the directory structure and returns paths.
 * The parquet file itself should be created by the caller (e.g., via a python script
 * or by copying a fixture file).
 */
export async function createTempParquetFixture(): Promise<ParquetFixture> {
  const baseDir = await fs.mkdtemp(path.join(os.tmpdir(), "sefin-audit-tool-"));
  const cnpj = "12345678000190";
  const cnpjDir = path.join(baseDir, cnpj);
  await fs.mkdir(cnpjDir, { recursive: true });

  const parquetPath = path.join(cnpjDir, `nfe_saida_${cnpj}.parquet`);

  const cleanup = async () => {
    // rm recursive is available in node 14+
    await fs.rm(baseDir, { recursive: true, force: true });
  };

  return { baseDir, cnpj, cnpjDir, parquetPath, cleanup };
}
