import "dotenv/config";
import express from "express";
import { createServer } from "http";
import net from "net";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import { registerOAuthRoutes } from "./oauth";
import { appRouter } from "../routers";
import { createContext } from "./context";
import { serveStatic, setupVite } from "./vite";

function isPortAvailable(port: number): Promise<boolean> {
  return new Promise(resolve => {
    const server = net.createServer();
    server.listen(port, () => {
      server.close(() => resolve(true));
    });
    server.on("error", () => resolve(false));
  });
}

async function findAvailablePort(startPort: number = 3000): Promise<number> {
  for (let port = startPort; port < startPort + 20; port++) {
    if (await isPortAvailable(port)) {
      return port;
    }
  }
  throw new Error(`No available port found starting from ${startPort}`);
}

async function startServer() {
  const app = express();
  const server = createServer(app);

  // OAuth callback under /api/oauth/callback
  registerOAuthRoutes(app);

  // Python API proxy - manual implementation to avoid Vite middleware conflicts
  const pythonPort = process.env.PYTHON_API_PORT || "8001";
  app.all("/api/python/*", async (req, res) => {
    try {
      const targetUrl = `http://localhost:${pythonPort}${req.originalUrl}`;

      // Clone request headers (string-only; drop host)
      const headers: Record<string, string> = {};
      for (const [key, value] of Object.entries(req.headers)) {
        if (typeof value === "string") headers[key] = value;
      }
      delete headers["host"];

      // Determine how to forward the body. Since we moved the body parsers
      // below this route, req is still a raw stream. We can forward it directly.
      const method = req.method.toUpperCase();
      const isMutation = method === "POST" || method === "PUT" || method === "PATCH";

      // Base fetch options
      const fetchOptions: RequestInit = {
        method,
        headers,
        // @ts-ignore - duplex is required in Node.js when body is a stream
        duplex: isMutation ? 'half' : undefined
      };

      if (isMutation) {

        // Stream raw bytes from the incoming request directly to the fetch call
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        fetchOptions.body = req as any;
      }

      const response = await fetch(targetUrl, fetchOptions);

      // Mirror response headers
      response.headers.forEach((value, key) => {
        // Avoid setting multiple content-length
        if (key.toLowerCase() !== "content-length") res.setHeader(key, value);
      });

      res.status(response.status);

      // Stream response
      const respType = response.headers.get("content-type") || "";
      if (respType.includes("application/json") || respType.startsWith("text/")) {
        const body = await response.text();
        res.send(body);
      } else {
        const buffer = Buffer.from(await response.arrayBuffer());
        res.send(buffer);
      }
    } catch (error: any) {
      console.error("[Python Proxy Error]", error?.stack || error?.message || error);
      res.status(502).json({
        detail: `Python API unavailable: ${error?.message || String(error)}`,
      });
    }
  });

  // Configure body parser with larger size limit for all other routes
  app.use(express.json({ limit: "50mb" }));
  app.use(express.urlencoded({ limit: "50mb", extended: true }));


  // tRPC API
  app.use(
    "/api/trpc",
    createExpressMiddleware({
      router: appRouter,
      createContext,
    })
  );
  // development mode uses Vite, production mode uses static files
  if (process.env.NODE_ENV === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  const preferredPort = parseInt(process.env.PORT || "3000");
  const port = await findAvailablePort(preferredPort);

  if (port !== preferredPort) {
    console.log(`Port ${preferredPort} is busy, using port ${port} instead`);
  }

  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
  });
}

startServer().catch(console.error);
