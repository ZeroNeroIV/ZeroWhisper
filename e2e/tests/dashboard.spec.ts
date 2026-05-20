import { test, expect } from '@playwright/test'
import { TEST_USER, TEST_PASSWORD } from '../global-setup'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('your_username').fill(TEST_USER)
    await page.getByPlaceholder('••••••••').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 })
  })

  test('shows three summary cards', async ({ page }) => {
    await expect(page.getByText('Balance')).toBeVisible()
    await expect(page.getByText('Spent this month')).toBeVisible()
    await expect(page.getByText('Income this month')).toBeVisible()
  })

  test('shows recent transactions section', async ({ page }) => {
    await expect(page.getByText('Recent Transactions')).toBeVisible()
  })

  test('sidebar navigation links present', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Transactions' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Whisper' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Visualizations' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible()
  })

  test('can navigate to transactions page', async ({ page }) => {
    await page.getByRole('link', { name: 'Transactions' }).click()
    await expect(page).toHaveURL('/transactions')
    await expect(page.getByRole('heading', { name: 'Transactions' })).toBeVisible()
  })
})
