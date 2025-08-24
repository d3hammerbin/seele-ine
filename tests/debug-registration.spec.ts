import { test, expect } from '@playwright/test';

test('Debug registration error', async ({ page }) => {
  // Navegar a la página de registro
  await page.goto('http://localhost:3000/register');
  
  // Generar un email único para evitar conflictos
  const timestamp = Date.now();
  const uniqueEmail = `test.user.${timestamp}@example.com`;
  
  // Llenar el formulario de registro
  await page.fill('input[name="firstName"]', 'Ricardo');
  await page.fill('input[name="lastName"]', 'Madrigal');
  await page.fill('input[name="email"]', uniqueEmail);
  await page.fill('input[name="password"]', 'Rurowni&0321');
  await page.fill('input[name="confirmPassword"]', 'Rurowni&0321');
  
  // Marcar los checkboxes de términos y condiciones
  await page.check('input[name="acceptTerms"]');
  await page.check('input[name="acceptPrivacy"]');
  
  // Interceptar la respuesta de la API
  const responsePromise = page.waitForResponse('**/api/v1/auth/register');
  
  // Hacer clic en el botón de registro
  await page.click('button[type="submit"]');
  
  // Esperar la respuesta
  const response = await responsePromise;
  
  console.log('Response status:', response.status());
  console.log('Response headers:', response.headers());
  
  let responseBody;
  try {
    responseBody = await response.json();
    console.log('Registration response:', JSON.stringify(responseBody, null, 2));
  } catch (error) {
    const responseText = await response.text();
    console.log('Response text (not JSON):', responseText);
    console.log('JSON parse error:', error);
  }
  
  // Verificar que la respuesta sea exitosa (201 Created)
  expect(response.status()).toBe(201);
});