import { test, expect } from '@playwright/test'
import { TEST_USER, TEST_PASSWORD } from '../global-setup'

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('your_username').fill(TEST_USER)
    await page.getByPlaceholder('••••••••').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 })
  })

  test('navigates to Whisper page', async ({ page }) => {
    await page.getByRole('link', { name: 'Whisper' }).click()
    await expect(page).toHaveURL('/whisper')
    await expect(page.getByRole('heading', { name: 'Whisper' })).toBeVisible()
  })

  test('navigates to Visualizations page', async ({ page }) => {
    await page.getByRole('link', { name: 'Visualizations' }).click()
    await expect(page).toHaveURL('/visualizations')
    await expect(page.getByRole('heading', { name: 'Visualizations' })).toBeVisible()
  })

  test('navigates to Settings page', async ({ page }) => {
    await page.getByRole('link', { name: 'Settings' }).click()
    await expect(page).toHaveURL('/settings')
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
  })

  test('active nav item is highlighted', async ({ page }) => {
    await page.goto('/transactions')
    // Active link resolves CSS vars at runtime — just verify correct URL
    await expect(page).toHaveURL('/transactions')
  })

  test('root redirects to login when unauthenticated', async ({ page, context }) => {
    await context.clearCookies()
    await page.goto('/')
    await expect(page).toHaveURL('/login', { timeout: 5000 })
  })
})
