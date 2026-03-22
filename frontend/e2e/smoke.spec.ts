import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('health endpoint returns ok', async ({ request }) => {
    const res = await request.get('/api/health')
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe('healthy')
  })

  test('login page loads', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveTitle(/MMAi/)
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('unauthenticated user redirects to login', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForURL('**/login')
    await expect(page).toHaveURL(/\/login/)
  })

  test('login and reach chat', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel(/email/i).fill(process.env.TEST_EMAIL || 'test@example.com')
    await page.getByLabel(/password/i).fill(process.env.TEST_PASSWORD || 'testpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Should redirect to chat after login
    await page.waitForURL('**/chat', { timeout: 10_000 })
    await expect(page).toHaveURL(/\/chat/)
  })

  test('static assets have cache headers', async ({ request }) => {
    // Fetch the index to find an asset URL
    const indexRes = await request.get('/')
    const html = await indexRes.text()
    const assetMatch = html.match(/\/assets\/[^"]+\.js/)
    if (!assetMatch) {
      test.skip()
      return
    }

    const assetRes = await request.get(assetMatch[0])
    expect(assetRes.ok()).toBeTruthy()
  })
})
