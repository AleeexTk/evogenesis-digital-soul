const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const ROOT_DIR = process.cwd(); // Should be c:\Project_Pyramid2024
const APP_DIR = path.join(ROOT_DIR, 'APP', 'Pyramid_JSON');
const CORE_DIR = path.join(ROOT_DIR, 'CORE');

const MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.json': 'application/json',
    '.png': 'image/png'
};

const server = http.createServer((req, res) => {
    console.log(`[REQUEST] ${req.method} ${req.url}`);

    // --- PROXY TO PURPLE BRIDGE (AEGIS) ---
    // Forward all /api/bridge requests to Python (Port 8000)
    if (req.url.startsWith('/api/bridge')) {
        const options = {
            hostname: '127.0.0.1',
            port: 8000,
            path: req.url.replace('/api/bridge', ''), // Strip prefix -> /protocol
            method: req.method,
            headers: {
                ...req.headers,
                'x-origin': 'node-proxy',
                'x-trust-level': '1.0' // Trust local proxy
            }
        };

        const proxyReq = http.request(options, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res, { end: true });
        });

        proxyReq.on('error', (e) => {
            console.error(`[PROXY ERROR] ${e.message}`);
            
            // Fallback for "GET" if Bridge is down? No, security first.
            res.writeHead(502, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ 
                error: 'Purple Bridge Unreachable', 
                details: 'Ensure PURPLE/bridge_core.py is running on port 8000.' 
            }));
        });

        if (req.method === 'POST' || req.method === 'PUT') {
            req.pipe(proxyReq, { end: true });
        } else {
            proxyReq.end();
        }
        return;
    }

    // Static File Serving
    let filePath;
    if (req.url === '/' || req.url === '/index.html') {
        filePath = path.join(APP_DIR, 'index.html');
    } else {
        // Try to find file in APP_DIR first
        filePath = path.join(APP_DIR, req.url);
    }

    const ext = path.extname(filePath);
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    fs.readFile(filePath, (err, content) => {
        if (err) {
            if (err.code === 'ENOENT') {
                res.writeHead(404);
                res.end('404 Not Found');
            } else {
                res.writeHead(500);
                res.end(`Server Error: ${err.code}`);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

console.log(`
[TRAILBLAZER] Server online.
[SOUL] Interface ready.
[PROVOCATEUR] Listening on http://localhost:${PORT}
[PURPLE] Bridge Proxy Active (Target: :8000)
`);

server.listen(PORT);
