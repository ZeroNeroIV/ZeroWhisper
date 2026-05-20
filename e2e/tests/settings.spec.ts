import { test, expect } from '@playwright/test'
import { TEST_USER, TEST_PASSWORD } from '../global-setup'

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('your_username').fill(TEST_USER)
    await page.getByPlaceholder('••••••••').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 })
    await page.goto('/settings')
  })

  test('renders settings tabs', async ({ page }) => {
    await expect(page.getByRole('tab', { name: /api.key/i })).toBeVisible()
  })

  test('can open the Generate Key dialog', async ({ page }) => {
    await page.getByRole('button', { name: /Generate New Key/i }).click()
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByRole('heading', { name: /Generate New API Key/i })).toBeVisible()
    await page.keyboard.press('Escape')
  })
})
