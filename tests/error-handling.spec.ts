import { test, expect } from '@playwright/test';

test.describe('Error Handling', () => {
  test('should display proper error message for 409 conflict', async ({ page }) => {
    // Capturar logs de consola para debug
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      const text = msg.text();
      consoleLogs.push(`${msg.type()}: ${text}`);
      // Log específicamente los mensajes de debug de 409
      if (text.includes('409 Error Debug')) {
        console.log(`DEBUG: ${text}`);
      }
    });
    
    // Navegar a la página de registro
    await page.goto('http://localhost/register');

    // Esperar a que la página cargue
    await page.waitForLoadState('networkidle');

    // Crear un usuario primero
    const timestamp = Date.now();
    const email = `test${timestamp}@example.com`;
    
    // Llenar el formulario de registro
    await page.fill('input[name="firstName"]', 'Test');
    await page.fill('input[name="lastName"]', 'User');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.fill('input[name="confirmPassword"]', 'TestPassword123!');

    // Marcar los checkboxes de términos y condiciones
    await page.check('input[name="acceptTerms"]');
    await page.check('input[name="acceptPrivacy"]');

    // Enviar el formulario (primer registro - debe ser exitoso)
    await page.click('button[type="submit"]');
    
    // Esperar a que aparezca el mensaje de éxito o redirección
    await page.waitForTimeout(2000);
    
    // Navegar de nuevo a la página de registro para intentar registrar el mismo email
    await page.goto('http://localhost/register');
    await page.waitForLoadState('networkidle');
    
    // Llenar el formulario con el mismo email (esto debe generar error 409)
    await page.fill('input[name="firstName"]', 'Test');
    await page.fill('input[name="lastName"]', 'User');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.fill('input[name="confirmPassword"]', 'TestPassword123!');

    // Marcar los checkboxes
    await page.check('input[name="acceptTerms"]');
    await page.check('input[name="acceptPrivacy"]');

    // Interceptar la respuesta de la API para verificar el error 409
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/api/v1/auth/register') && response.status() === 409
    );

    // Enviar el formulario (segundo registro - debe fallar con 409)
    await page.click('button[type="submit"]');
    
    // Esperar la respuesta de error
    const response = await responsePromise;
    expect(response.status()).toBe(409);
    
    // Verificar que el mensaje de error se muestre correctamente y no sea '[object Object]'
    await page.waitForSelector('.text-destructive', { timeout: 10000 });
    
    // Buscar el mensaje de error en diferentes posibles selectores
    const errorSelectors = [
      '.text-destructive',
      '[data-testid="error-message"]',
      '.error-message',
      '.alert-error',
      '.text-red-500',
      '.text-danger',
      '[role="alert"]'
    ];
    
    let errorMessage = '';
    for (const selector of errorSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible()) {
          errorMessage = await element.textContent() || '';
          break;
        }
      } catch (e) {
        // Continuar con el siguiente selector
      }
    }
    
    console.log('Error message found:', errorMessage);
    
    // Imprimir logs de consola para depuración
    console.log('Console logs captured:');
    consoleLogs.forEach(log => console.log(log));
    
    // Imprimir logs específicos de handleResponseError
    const handleResponseLogs = consoleLogs.filter(log => log.includes('handleResponseError'));
    if (handleResponseLogs.length > 0) {
      console.log('\n=== HandleResponseError Logs ===');
      for (const log of handleResponseLogs) {
        console.log(log);
      }
      console.log('=== End HandleResponseError Logs ===\n');
    }
    
    // Verificar que el mensaje no sea '[object Object]' o similar
    expect(errorMessage).not.toContain('[object Object]');
    expect(errorMessage).not.toContain('object,object');
    expect(errorMessage).not.toBe('');
    
    // El mensaje debe contener información útil sobre el conflicto
    expect(errorMessage.toLowerCase()).toMatch(/(conflict|exists|already|usuario|email)/i);
    
    console.log('Test completed successfully. Error message:', errorMessage);
  });
});