// Test script to login and inspect tokens
// Using native fetch (Node.js 18+)

async function testLogin() {
    try {
        console.log('Testing login...');
        
        const response = await fetch('http://localhost:8000/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: 'admin@seele.com',
                password: 'Admin123!'
            }),
        });
        
        if (!response.ok) {
            const error = await response.text();
            console.error('Login failed:', response.status, error);
            return;
        }
        
        const result = await response.json();
        console.log('Login successful!');
        console.log('User:', result.user.email);
        
        const tokens = result.tokens;
        console.log('\n=== TOKEN ANALYSIS ===');
        console.log('Access Token Length:', tokens.access_token.length);
        console.log('Access Token Segments:', tokens.access_token.split('.').length);
        console.log('Access Token Preview:', tokens.access_token.substring(0, 50) + '...');
        
        console.log('\nRefresh Token Length:', tokens.refresh_token.length);
        console.log('Refresh Token Segments:', tokens.refresh_token.split('.').length);
        console.log('Refresh Token Preview:', tokens.refresh_token.substring(0, 50) + '...');
        
        // Test refresh token immediately
        console.log('\n=== TESTING REFRESH TOKEN ===');
        const refreshResponse = await fetch('http://localhost:8000/api/v1/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: tokens.refresh_token }),
        });
        
        if (!refreshResponse.ok) {
            const refreshError = await refreshResponse.text();
            console.error('Refresh failed:', refreshResponse.status, refreshError);
        } else {
            const refreshResult = await refreshResponse.json();
            console.log('Refresh successful!');
            console.log('New Access Token Length:', refreshResult.tokens.access_token.length);
            console.log('New Refresh Token Length:', refreshResult.tokens.refresh_token.length);
        }
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

testLogin();