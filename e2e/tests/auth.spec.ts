import { test, expect } from '@playwright/test'
import { TEST_USER, TEST_PASSWORD } from '../global-setup'

test.describe('Authentication', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('ZeroWhisper')).toBeVisible()
    await expect(page.getByRole('tab', { name: 'Sign in' })).toBeVisible()
    await expect(page.getByRole('tab', { name: 'Register' })).toBeVisible()
  })

  test('rejects wrong credentials', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('your_username').fill('wronguser')
    await page.getByPlaceholder('••••••••').fill('wrongpassword')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText(/incorrect|invalid|unauthorized/i)).toBeVisible({ timeout: 5000 })
  })

  test('login with valid credentials navigates to dashboard', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('your_username').fill(TEST_USER)
    await page.getByPlaceholder('••••••••').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 })
    await expect(page.getByText('Overview')).toBeVisible()
  })

  test('protected routes redirect to login when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL('/login', { timeout: 5000 })
  })

  test('logout returns to login page', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('your_username').fill(TEST_USER)
    await page.getByPlaceholder('••••••••').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 })

    await page.getByText(TEST_USER).click()
    await page.getByText('Logout').click()
    await expect(page).toHaveURL('/login', { timeout: 5000 })
  })
})
