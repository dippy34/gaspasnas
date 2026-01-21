export async function onRequest({ params, env, request }) {
  const key = params.path.join("/")
  const r2Path = `non-semag/${key}`

  // Try to get the object from R2
  const object = await env.R2_SEMAG.get(r2Path)

  if (!object) {
    // Return 404 with helpful error message
    return new Response(`Not found: ${r2Path}`, { 
      status: 404,
      headers: {
        "Content-Type": "text/plain"
      }
    })
  }

  return new Response(object.body, {
    headers: {
      "Content-Type": object.httpMetadata?.contentType || "application/octet-stream",
      "Cache-Control": "public, max-age=31536000, immutable"
    }
  })
}

