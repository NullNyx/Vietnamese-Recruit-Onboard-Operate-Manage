    // Tiny reverse proxy used by the Playwright `webServer` in
    // vroom-hr/playwright.config.ts. It lets the browser talk to a single
    // same-origin host (http://localhost:3000) so the backend's
    // `Secure; SameSite=Lax` HttpOnly auth cookie is carried and no
    // cross-origin CORS preflight is required.
    //
    //   /api/*  -> http://localhost:8000   (FastAPI backend, real data)
    //   /*      -> http://localhost:3001    (Next.js dev server for vroom-hr)
    //
    // Run:  node e2e/proxy.mjs   (PORT default 3000)
    import http from "node:http";
    
    const PORT = parseInt(process.env.PROXY_PORT || "3000", 10);
    const BE = process.env.BACKEND_URL || "http://localhost:8000";
    const FE = process.env.FRONTEND_URL || "http://localhost:3001";
    
    const beUrl = new URL(BE);
    const feUrl = new URL(FE);
    
    function forwardReq(req, res, target) {
      const u = new URL(req.url, target);
      const headers = { ...req.headers };
      // Present the upstream host so the backend attributes cookies & redirects
      // to its own host (browser still sees them via this proxy origin :3000).
      headers["host"] = u.host;
      headers["x-forwarded-host"] = req.headers["host"] || `localhost:${PORT}`;
      headers["x-forwarded-proto"] = "http";
      if (!headers["x-forwarded-for"]) headers["x-forwarded-for"] = "127.0.0.1";
      delete headers["content-length"]; // recompute from stream; safer for proxied bodies
    
      const upstream = http.request(
        {
          protocol: u.protocol,
          hostname: u.hostname,
          port: u.port || (u.protocol === "https:" ? 443 : 80),
          method: req.method,
          path: `${u.pathname}${u.search}`,
          headers,
        },
        (upRes) => {
          const noBody =
            req.method === "HEAD" ||
            upRes.statusCode === 304 ||
            upRes.statusCode === 204;
          res.writeHead(upRes.statusCode || 200, upRes.headers);
          if (noBody) {
            res.end();
            upRes.resume();
            return;
          }
          upRes.pipe(res);
        }
      );
      upstream.on("error", (err) => {
        if (!res.headersSent) {
          res.writeHead(502, { "content-type": "application/json" });
          res.end(
            JSON.stringify({
              proxy_error: err.code || "UPSTREAM_ERROR",
              message: String(err.message),
            })
          );
        }
        req.resume();
      });
      req.pipe(upstream);
    }
    
    const server = http.createServer((req, res) => {
      const isApi = req.url.startsWith("/api/");
      forwardReq(req, res, isApi ? beUrl : feUrl);
    });
    
    server.on("clientError", (_err, socket) => {
      if (socket.writable) socket.end("HTTP/1.1 400 Bad Request\r\n\r\n");
    });
    
    server.listen(PORT, "0.0.0.0", () => {
      console.log(`[vroom-hr e2e proxy] listening on http://localhost:${PORT}`);
      console.log(`  /api/* -> ${BE}`);
      console.log(`  /*     -> ${FE}`);
    });
    