// Debug script to check tokens in localStorage
console.log('=== TOKEN DEBUG ===');

// Check all seele-related items in localStorage
const seeleKeys = [];
for (let i = 0; i < localStorage.length; i++) {
  const key = localStorage.key(i);
  if (key && key.startsWith('seele_')) {
    seeleKeys.push(key);
  }
}

console.log('Seele keys found:', seeleKeys);

// Check specific tokens
const accessToken = localStorage.getItem('seele_access_token');
const refreshToken = localStorage.getItem('seele_refresh_token');
const tokenExpiration = localStorage.getItem('seele_token_expiration');

console.log('Access Token:', accessToken ? 'EXISTS' : 'NOT FOUND');
console.log('Refresh Token:', refreshToken ? 'EXISTS' : 'NOT FOUND');
console.log('Token Expiration:', tokenExpiration);

if (accessToken) {
  console.log('Access Token Length:', accessToken.length);
  console.log('Access Token Segments:', accessToken.split('.').length);
  console.log('Access Token Preview:', accessToken.substring(0, 50) + '...');
}

if (refreshToken) {
  console.log('Refresh Token Length:', refreshToken.length);
  console.log('Refresh Token Segments:', refreshToken.split('.').length);
  console.log('Refresh Token Preview:', refreshToken.substring(0, 50) + '...');
  
  // Check if it's a valid JWT format
  const segments = refreshToken.split('.');
  if (segments.length !== 3) {
    console.error('❌ INVALID REFRESH TOKEN: Not enough segments!');
    console.log('Expected 3 segments (header.payload.signature), got:', segments.length);
    console.log('Segments:', segments);
  } else {
    console.log('✅ Refresh token has correct JWT format');
    try {
      const header = JSON.parse(atob(segments[0]));
      const payload = JSON.parse(atob(segments[1]));
      console.log('Token Header:', header);
      console.log('Token Payload:', payload);
      console.log('Token Expiration:', new Date(payload.exp * 1000));
    } catch (e) {
      console.error('❌ Error parsing token:', e.message);
    }
  }
}

// Check current time vs expiration
if (tokenExpiration) {
  const expTime = parseInt(tokenExpiration);
  const now = Date.now();
  const timeLeft = expTime - now;
  console.log('Time until expiration:', Math.floor(timeLeft / 1000), 'seconds');
  console.log('Token expired:', timeLeft <= 0);
}

console.log('=== END TOKEN DEBUG ===');