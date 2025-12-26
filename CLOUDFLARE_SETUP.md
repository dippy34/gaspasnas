# Cloudflare Workers Setup Guide

This guide will help you migrate your Express.js API to Cloudflare Workers.

## Step 1: Create KV Namespaces

1. Go to your Cloudflare Dashboard
2. Navigate to **Workers & Pages** → **KV**
3. Create 4 KV namespaces:
   - `SUGGESTIONS_KV` - for storing suggestions and bug reports
   - `ANALYTICS_KV` - for storing analytics data
   - `ADMIN_CREDENTIALS_KV` - for storing admin credentials
   - `TOKENS_KV` - for storing authentication tokens

4. Note down the **Namespace ID** for each namespace

## Step 2: Update wrangler.toml

1. Open `wrangler.toml`
2. Replace the placeholder IDs with your actual KV namespace IDs:
   ```toml
   [[kv_namespaces]]
   binding = "SUGGESTIONS_KV"
   id = "your-actual-suggestions-kv-id"
   preview_id = "your-actual-suggestions-kv-preview-id"
   ```

3. Do this for all 4 KV namespaces

## Step 3: Migrate Existing Data

Run the migration script to copy your existing JSON data to KV:

```bash
# Install Wrangler CLI if you haven't already
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Run the migration script
node scripts/migrate-to-kv.js
```

## Step 4: Deploy Workers Function

The Workers function is already set up at `functions/api/[[path]].js`. 

To deploy:

```bash
# Deploy to Cloudflare
wrangler deploy
```

Or if using Cloudflare Pages, the function will be automatically deployed when you push to your repository.

## Step 5: Update Cloudflare Pages Configuration

In your Cloudflare Pages dashboard:

1. Go to your project settings
2. Navigate to **Builds & deployments**
3. Update the build configuration:
   - **Framework preset:** `None`
   - **Build command:** (leave empty)
   - **Build output directory:** `/`
   - **Root directory:** (leave empty)

## Step 6: Test the API

After deployment, test your API endpoints:

- `POST /api/submit-suggestion` - Should work without authentication
- `POST /api/admin/login` - Should authenticate and return a token
- `GET /api/admin/suggestions` - Should require authentication

## Important Notes

1. **Static Files**: Cloudflare Pages will automatically serve your static HTML/CSS/JS files. The Workers function only handles `/api/*` routes.

2. **File System**: Workers don't have access to the file system. All data must be stored in KV.

3. **Node.js Modules**: Workers use the Web API, not Node.js. The code has been converted to use:
   - Web Crypto API instead of Node's `crypto`
   - KV storage instead of `fs`
   - Fetch API (native in Workers)

4. **IP Address**: Workers automatically provide the client IP via `cf-connecting-ip` header, which is more reliable than Express.

5. **Token Expiration**: Tokens now expire after 24 hours. You may want to implement token refresh logic.

## Troubleshooting

- **KV not found**: Make sure you've created the KV namespaces and updated `wrangler.toml` with the correct IDs
- **Authentication fails**: Check that admin credentials were migrated to KV
- **CORS errors**: The Workers function includes CORS headers, but you may need to adjust them for your domain

## Rollback Plan

If you need to rollback:
1. Your original `index.js` Express server is still in the repository
2. You can deploy it to a Node.js hosting service (Railway, Render, etc.)
3. Update your frontend API URLs to point to the new server

