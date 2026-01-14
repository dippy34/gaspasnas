// Cloudflare Workers proxy function
// Handles /proxy route for proxying web content

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  
  // Get the target URL from query parameter
  const targetUrl = url.searchParams.get('url');
  
  if (!targetUrl) {
    // If no URL parameter, serve a simple HTML UI at /proxy (like /admin -> admin.html)
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Scramjet Proxy</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body {
      background: #020304;
      color: #00ff7f;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
    }
    .container {
      max-width: 480px;
      width: 100%;
      padding: 24px 20px;
      border-radius: 16px;
      box-shadow: 0 0 32px rgba(0, 255, 127, 0.35);
      background: radial-gradient(circle at top, #02110a 0, #020304 55%);
    }
    h1 {
      font-size: 1.6rem;
      margin: 0 0 12px;
      text-align: center;
      letter-spacing: 0.08em;
    }
    p {
      font-size: 0.9rem;
      color: #8af5c0;
      text-align: center;
      margin: 0 0 18px;
    }
    label {
      display: block;
      font-size: 0.85rem;
      margin-bottom: 6px;
      color: #b3ffe0;
    }
    input[type="url"] {
      width: 100%;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid #0aff9d;
      background: #030a08;
      color: #e6fff6;
      outline: none;
      font-size: 0.95rem;
    }
    input[type="url"]::placeholder {
      color: #4fd8a1;
    }
    button {
      margin-top: 14px;
      width: 100%;
      padding: 10px 14px;
      border-radius: 999px;
      border: none;
      background: linear-gradient(135deg, #00ff7f, #00ffa8);
      color: #020304;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      box-shadow: 0 0 18px rgba(0, 255, 127, 0.45);
    }
    button:hover {
      filter: brightness(1.05);
    }
    .hint {
      margin-top: 10px;
      font-size: 0.8rem;
      text-align: center;
      color: #6be6b3;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Scramjet Proxy</h1>
    <p>Enter a URL to open it through the Nova Hub proxy.</p>
    <form id="proxy-form">
      <label for="proxy-url">Target URL</label>
      <input id="proxy-url" type="url" name="url" placeholder="https://example.com" required />
      <button type="submit">Go</button>
    </form>
    <div class="hint">Short link: <strong>${url.origin}/proxy</strong></div>
  </div>
  <script>
    const form = document.getElementById('proxy-form');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const input = document.getElementById('proxy-url');
      const target = input.value.trim();
      if (!target) return;
      const encoded = encodeURIComponent(target);
      window.location.href = '/proxy?url=' + encoded;
    });
  </script>
</body>
</html>`;

    return new Response(html, {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8'
      }
    });
  }
  
  try {
    // Validate URL
    const targetUrlObj = new URL(targetUrl);
    
    // Fetch the target URL
    const proxyRequest = new Request(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': targetUrl,
        'Origin': targetUrlObj.origin
      }
    });
    
    const response = await fetch(proxyRequest);
    
    // Check if it's HTML content
    const contentType = response.headers.get('content-type') || '';
    const isHtml = contentType.includes('text/html');
    
    if (!isHtml) {
      // For non-HTML content (images, CSS, JS, etc.), return as-is
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          'Content-Type': contentType,
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=3600'
        }
      });
    }
    
    // For HTML content, rewrite URLs
    const html = await response.text();
    
    // Get the proxy base URL
    const proxyBase = `${url.origin}/proxy?url=`;
    
    // Rewrite URLs in the HTML
    let modifiedHtml = html;
    
    // Rewrite href attributes
    modifiedHtml = modifiedHtml.replace(/href=["']([^"']+)["']/gi, (match, urlPath) => {
      if (urlPath.startsWith('javascript:') || urlPath.startsWith('mailto:') || urlPath.startsWith('#') || urlPath.startsWith('data:')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `href="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite src attributes
    modifiedHtml = modifiedHtml.replace(/src=["']([^"']+)["']/gi, (match, urlPath) => {
      if (urlPath.startsWith('data:')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `src="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite action attributes
    modifiedHtml = modifiedHtml.replace(/action=["']([^"']+)["']/gi, (match, urlPath) => {
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `action="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite CSS url() references
    modifiedHtml = modifiedHtml.replace(/url\(["']?([^"')]+)["']?\)/gi, (match, urlPath) => {
      if (urlPath.startsWith('data:') || urlPath.startsWith('#')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `url("${proxyBase}${encodeURIComponent(absoluteUrl)}")`;
      } catch (e) {
        return match;
      }
    });
    
    // Inject base tag to help with relative URLs
    modifiedHtml = modifiedHtml.replace(
      /<head[^>]*>/i,
      `<head><base href="${targetUrl}">`
    );
    
    // Return the modified HTML
    return new Response(modifiedHtml, {
      status: response.status,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-cache'
      }
    });
    
  } catch (error) {
    console.error('Proxy error:', error);
    return new Response(`Proxy error: ${error.message}`, {
      status: 500,
      headers: {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
}
