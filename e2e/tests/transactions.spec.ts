import { test, expect } from '@playwright/test'
import { TEST_USER, TEST_PASSWORD } from '../global-setup'

test.describe('Transactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('your_username').fill(TEST_USER)
    await page.getByPlaceholder('••••••••').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL('/dashboard', { timeout: 8000 })
    await page.goto('/transactions')
    await page.waitForLoadState('networkidle')
  })

  test('page renders with filters and action buttons', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Add Transaction/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Import CSV/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Apply/i })).toBeVisible()
  })

  test('opens Add Transaction dialog', async ({ page }) => {
    await page.getByRole('button', { name: /Add Transaction/i }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole('heading', { name: /Add Transaction/i })).toBeVisible()
  })

  test('creates a new transaction', async ({ page }) => {
    await page.getByRole('button', { name: /Add Transaction/i }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()

    await dialog.getByPlaceholder('0.00').fill('15.50')
    await dialog.getByPlaceholder('Enter description').fill('E2E test groceries')
    await dialog.locator('input[type="date"]').fill('2026-05-16')

    // Select category via Radix Select
    await dialog.getByRole('combobox').filter({ hasText: /category/i }).click()
    await page.getByRole('option', { name: 'Food' }).click()

    await dialog.getByRole('button', { name: /save|add|submit/i }).click()

    await expect(dialog).not.toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Transaction added')).toBeVisible({ timeout: 5000 })
  })

  test('transaction appears in the table after creation', async ({ page }) => {
    await expect(page.getByText('E2E test groceries')).toBeVisible({ timeout: 5000 })
  })

  test('filters by category', async ({ page }) => {
    const categorySelect = page.getByRole('combobox').first()
    await categorySelect.click()
    await page.getByRole('option', { name: 'Food' }).click()
    await page.getByRole('button', { name: /Apply/i }).click()
    await expect(page.getByText('No transactions found')).not.toBeVisible({ timeout: 5000 })
  })

  test('opens CSV import dialog', async ({ page }) => {
    await page.getByRole('button', { name: /Import CSV/i }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole('heading', { name: /Import Transactions from CSV/i })).toBeVisible()
    await page.keyboard.press('Escape')
  })

  test('can delete a transaction', async ({ page }) => {
    const deleteBtn = page.getByRole('button', { name: 'Delete transaction' }).first()
    await expect(deleteBtn).toBeVisible({ timeout: 5000 })
    await deleteBtn.click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await dialog.getByRole('button', { name: 'Delete' }).click()
    await expect(page.getByText('Transaction deleted')).toBeVisible({ timeout: 5000 })
  })
})
