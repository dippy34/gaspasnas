// Migration script to copy data from JSON files to Cloudflare KV
// Run with: node scripts/migrate-to-kv.js

const fs = require('fs');
const path = require('path');

// You'll need to install wrangler: npm install -g wrangler
// Then run: wrangler kv:key put --namespace-id=YOUR_NAMESPACE_ID "key" "value"

console.log('Migration Script for Cloudflare KV');
console.log('===================================\n');

console.log('This script will help you migrate your JSON data to Cloudflare KV.\n');
console.log('You need to manually copy the data using Wrangler CLI commands.\n');

const dataDir = path.join(__dirname, '..', 'data');

// Read and display suggestions
try {
  const suggestionsPath = path.join(dataDir, 'suggestions.json');
  if (fs.existsSync(suggestionsPath)) {
    const suggestions = JSON.parse(fs.readFileSync(suggestionsPath, 'utf8'));
    console.log('SUGGESTIONS_KV:');
    console.log('Key: suggestions');
    console.log('Value:', JSON.stringify(suggestions, null, 2));
    console.log('\nCommand:');
    console.log(`wrangler kv:key put --namespace-id=YOUR_SUGGESTIONS_KV_ID "suggestions" '${JSON.stringify(suggestions)}'`);
    console.log('\n');
  }
} catch (error) {
  console.error('Error reading suggestions:', error.message);
}

// Read and display analytics
try {
  const analyticsPath = path.join(dataDir, 'analytics.json');
  if (fs.existsSync(analyticsPath)) {
    const analytics = JSON.parse(fs.readFileSync(analyticsPath, 'utf8'));
    console.log('ANALYTICS_KV:');
    console.log('Key: analytics');
    console.log('Value:', JSON.stringify(analytics, null, 2));
    console.log('\nCommand:');
    console.log(`wrangler kv:key put --namespace-id=YOUR_ANALYTICS_KV_ID "analytics" '${JSON.stringify(analytics)}'`);
    console.log('\n');
  }
} catch (error) {
  console.error('Error reading analytics:', error.message);
}

// Read and display admin credentials
try {
  const credentialsPath = path.join(dataDir, 'admin-credentials.json');
  if (fs.existsSync(credentialsPath)) {
    const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));
    console.log('ADMIN_CREDENTIALS_KV:');
    console.log('Key: credentials');
    console.log('Value:', JSON.stringify(credentials, null, 2));
    console.log('\nCommand:');
    console.log(`wrangler kv:key put --namespace-id=YOUR_ADMIN_CREDENTIALS_KV_ID "credentials" '${JSON.stringify(credentials)}'`);
    console.log('\n');
  } else {
    console.log('ADMIN_CREDENTIALS_KV:');
    console.log('No admin credentials file found. You may need to create admin accounts first.');
    console.log('\n');
  }
} catch (error) {
  console.error('Error reading credentials:', error.message);
}

console.log('\n===================================');
console.log('Migration Instructions:');
console.log('1. Install Wrangler: npm install -g wrangler');
console.log('2. Login: wrangler login');
console.log('3. Get your KV namespace IDs from Cloudflare Dashboard');
console.log('4. Run the commands shown above, replacing YOUR_*_KV_ID with actual IDs');
console.log('5. For TOKENS_KV, you can leave it empty initially (tokens are created on login)');

