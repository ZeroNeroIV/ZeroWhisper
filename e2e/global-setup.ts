import { request } from '@playwright/test'

const BASE = 'http://localhost'
export const TEST_PASSPHRASE = 'TestPassphrase123!'
export const TEST_USER = 'e2euser'
export const TEST_EMAIL = 'e2e@test.com'
export const TEST_PASSWORD = 'E2ePassword1!'

export default async function globalSetup() {
  const ctx = await request.newContext({ baseURL: BASE })

  // Check if DB is already initialized
  const statusRes = await ctx.get('/setup/status')
  const status = await statusRes.json()

  if (status.state === 'UNINITIALIZED') {
    console.log('  [setup] Initializing database…')
    const initRes = await ctx.post('/setup/initialize', {
      data: { passphrase: TEST_PASSPHRASE },
    })
    if (!initRes.ok()) {
      throw new Error(`DB init failed: ${await initRes.text()}`)
    }
    console.log('  [setup] Database initialized.')
  } else if (!status.db_ready) {
    console.log('  [setup] Unlocking database…')
    const unlockRes = await ctx.post('/setup/unlock', {
      data: { passphrase: TEST_PASSPHRASE },
    })
    if (!unlockRes.ok()) {
      throw new Error(`DB unlock failed: ${await unlockRes.text()}`)
    }
    console.log('  [setup] Database unlocked.')
  } else {
    console.log('  [setup] Database already ready.')
  }

  // Register test user (ignore 409 / already-exists errors)
  const regRes = await ctx.post('/auth/register', {
    data: { username: TEST_USER, email: TEST_EMAIL, password: TEST_PASSWORD },
  })
  if (!regRes.ok() && regRes.status() !== 409) {
    const body = await regRes.text()
    // 400 with "already" is fine too
    if (!body.includes('already')) {
      throw new Error(`Register failed: ${body}`)
    }
  }
  console.log('  [setup] Test user ready.')

  await ctx.dispose()
}
