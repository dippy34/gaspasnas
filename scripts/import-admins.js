// Script to import admin credentials programmatically
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Helper function to hash password
function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex');
}

// Helper function to read existing credentials
function readCredentials() {
  const credentialsPath = path.join(__dirname, '..', 'data', 'admin-credentials.json');
  try {
    const data = fs.readFileSync(credentialsPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return [];
  }
}

// Helper function to write credentials
function writeCredentials(credentials) {
  const credentialsPath = path.join(__dirname, '..', 'data', 'admin-credentials.json');
  fs.writeFileSync(credentialsPath, JSON.stringify(credentials, null, 2), 'utf8');
  console.log(`✓ Credentials saved to ${credentialsPath}`);
}

// Import credentials function
function importCredentials(newCredentials) {
  const existing = readCredentials();
  const existingEmails = new Set(existing.map(c => c.email.toLowerCase()));
  
  let added = 0;
  let skipped = 0;

  newCredentials.forEach(cred => {
    const email = cred.email.toLowerCase();
    
    if (existingEmails.has(email)) {
      console.log(`⚠ Skipped ${cred.email} (already exists)`);
      skipped++;
      return;
    }

    existing.push({
      email: cred.email,
      password: hashPassword(cred.password),
      createdAt: new Date().toISOString()
    });
    
    existingEmails.add(email);
    console.log(`✓ Added ${cred.email}`);
    added++;
  });

  writeCredentials(existing);
  console.log(`\n📊 Summary: ${added} added, ${skipped} skipped, ${existing.length} total`);
}

// Example usage - Edit this array to add your credentials
const credentialsToImport = [
  { email: 'admin@example.com', password: 'admin123' },
  { email: 'admin2@example.com', password: 'password456' },
  { email: 'admin3@example.com', password: 'secure789' },
  // Add more credentials here in the format: { email: 'email@example.com', password: 'password' }
];

// Run the import
if (require.main === module) {
  console.log('🔐 Importing admin credentials...\n');
  importCredentials(credentialsToImport);
}

// Export for use in other files
module.exports = { importCredentials, hashPassword };

