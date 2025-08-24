import { test, expect } from '@playwright/test';

// Credenciales por defecto encontradas en el proyecto
const DEFAULT_CREDENTIALS = {
  admin: {
    email: 'admin@seele.com',
    password: 'Admin123!'
  },
  user: {
    email: 'test@example.com',
    password: 'testpassword123'
  }
};

test.describe('Login Network Diagnosis', () => {
  test('should diagnose network connectivity and login issues', async ({ page }) => {
    console.log('🔍 Starting network diagnosis...');
    
    // Configurar timeouts más largos
    test.setTimeout(60000);
    
    // Interceptar todos los requests y responses
    const requests: Array<{url: string, method: string, timestamp: string}> = [];
    const responses: Array<{url: string, status: number, statusText: string, timestamp: string}> = [];
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    
    page.on('request', request => {
      requests.push({
        url: request.url(),
        method: request.method(),
        timestamp: new Date().toISOString()
      });
      console.log(`📤 Request: ${request.method()} ${request.url()}`);
    });
    
    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        timestamp: new Date().toISOString()
      });
      console.log(`📥 Response: ${response.status()} ${response.url()}`);
    });
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log(`🚨 Console Error: ${msg.text()}`);
      }
    });
    
    page.on('pageerror', error => {
      pageErrors.push(error.message);
      console.log(`💥 Page Error: ${error.message}`);
    });
    
    try {
      console.log('🌐 Attempting to navigate to base URL...');
      
      // Navegar a la página principal con timeout extendido
      await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 30000 });
      
      console.log('✅ Page loaded successfully');
      
      // Esperar un poco para que se carguen los recursos
      await page.waitForTimeout(2000);
      
      // Verificar si hay elementos de login visibles
      const emailInput = page.locator('input[type="email"]');
      const passwordInput = page.locator('input[type="password"]');
      const submitButton = page.locator('button[type="submit"]');
      
      console.log('🔍 Checking for login form elements...');
      
      if (await emailInput.isVisible({ timeout: 5000 })) {
        console.log('✅ Email input found');
        
        // Llenar el formulario con credenciales de admin
        await emailInput.fill(DEFAULT_CREDENTIALS.admin.email);
        await passwordInput.fill(DEFAULT_CREDENTIALS.admin.password);
        
        console.log('📝 Form filled with admin credentials');
        
        // Hacer clic en submit
        console.log('🖱️ Clicking submit button...');
        await submitButton.click();
        
        // Esperar para ver qué pasa
        await page.waitForTimeout(5000);
        
        console.log('⏱️ Waited 5 seconds after submit');
        
      } else {
        console.log('❌ Login form not found');
      }
      
    } catch (error) {
      console.log(`❌ Navigation error: ${(error as Error).message}`);
    }
    
    // Verificar conectividad directa con la API
    console.log('🏥 Testing direct API connectivity...');
    
    try {
      const healthResponse = await page.request.get('http://localhost:80/api/v1/health');
      console.log(`🏥 Health check status: ${healthResponse.status()}`);
      
      if (healthResponse.ok()) {
        const healthData = await healthResponse.json();
        console.log('🏥 Health data:', JSON.stringify(healthData, null, 2));
      } else {
        console.log('❌ Health check failed with status:', healthResponse.status());
      }
    } catch (error) {
      console.log('❌ Health check request failed:', (error as Error).message);
    }
    
    // Probar login directo via API
    console.log('🔐 Testing direct login API call...');
    
    try {
      const loginResponse = await page.request.post('http://localhost:80/api/v1/auth/login', {
        data: {
          email: DEFAULT_CREDENTIALS.admin.email,
          password: DEFAULT_CREDENTIALS.admin.password
        },
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log(`🔐 Direct login status: ${loginResponse.status()}`);
      
      if (loginResponse.ok()) {
        const loginData = await loginResponse.json();
        console.log('🔐 Login successful:', JSON.stringify(loginData, null, 2));
      } else {
        const errorText = await loginResponse.text();
        console.log('❌ Direct login failed:', errorText);
      }
    } catch (error) {
      console.log('❌ Direct login request failed:', (error as Error).message);
    }
    
    // Resumen de diagnóstico
    console.log('\n📊 DIAGNOSIS SUMMARY:');
    console.log(`📤 Total requests: ${requests.length}`);
    console.log(`📥 Total responses: ${responses.length}`);
    console.log(`🚨 Console errors: ${consoleErrors.length}`);
    console.log(`💥 Page errors: ${pageErrors.length}`);
    
    if (requests.length > 0) {
      console.log('\n📤 REQUESTS:');
      requests.forEach((req, i) => {
        console.log(`  ${i + 1}. ${req.method} ${req.url} at ${req.timestamp}`);
      });
    }
    
    if (responses.length > 0) {
      console.log('\n📥 RESPONSES:');
      responses.forEach((res, i) => {
        console.log(`  ${i + 1}. ${res.status} ${res.url} at ${res.timestamp}`);
      });
    }
    
    if (consoleErrors.length > 0) {
      console.log('\n🚨 CONSOLE ERRORS:');
      consoleErrors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error}`);
      });
    }
    
    if (pageErrors.length > 0) {
      console.log('\n💥 PAGE ERRORS:');
      pageErrors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error}`);
      });
    }
    
    // La prueba siempre pasa, solo estamos diagnosticando
    expect(true).toBe(true);
  });
});