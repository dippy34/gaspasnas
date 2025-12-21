// Example: How to import admin credentials programmatically

// Method 1: Using the simple script
// Just edit scripts/import-admins-simple.js and run: node scripts/import-admins-simple.js

// Method 2: Using the import function directly
const { importAdminCredentials } = require('../index.js');

// Import credentials
const credentials = [
  { email: 'admin@example.com', password: 'admin123' },
  { email: 'admin2@example.com', password: 'password456' },
  { email: 'admin3@example.com', password: 'secure789' },
];

console.log('Importing credentials...\n');
const result = importAdminCredentials(credentials);
console.log('\nResult:', result);

