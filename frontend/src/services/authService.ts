/**
 * Demo only, replace with backend auth.
 *
 * Accounts are stored in localStorage as an array of { email, salt, passwordHash }.
 * Passwords are never stored in plain text: we store SHA-256(salt + password).
 */

const ACCOUNTS_KEY = 'up_accounts_v1'
const SESSION_KEY = 'up_session_v1'

interface Account {
  email: string       // always lowercase
  salt: string        // hex-encoded random bytes
  passwordHash: string // hex-encoded SHA-256(salt + password)
}

async function sha256hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

function generateSalt(): string {
  const bytes = new Uint8Array(16)
  crypto.getRandomValues(bytes)
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

function loadAccounts(): Account[] {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY)
    return raw ? (JSON.parse(raw) as Account[]) : []
  } catch {
    return []
  }
}

function saveAccounts(accounts: Account[]): void {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts))
}

function findAccount(email: string): Account | undefined {
  return loadAccounts().find((a) => a.email === email)
}

export type AuthErrorCode =
  | 'EMAIL_EXISTS'
  | 'EMAIL_NOT_FOUND'
  | 'WRONG_PASSWORD'
  | 'SAME_PASSWORD'

export interface AuthResult {
  ok: boolean
  error?: AuthErrorCode
}

export const authService = {
  /** Register a new account. Rejects if email already exists. */
  async signUp(email: string, password: string): Promise<AuthResult> {
    const normalized = email.trim().toLowerCase()
    if (findAccount(normalized)) {
      return { ok: false, error: 'EMAIL_EXISTS' }
    }
    const salt = generateSalt()
    const passwordHash = await sha256hex(salt + password)
    const accounts = loadAccounts()
    accounts.push({ email: normalized, salt, passwordHash })
    saveAccounts(accounts)
    localStorage.setItem(SESSION_KEY, normalized)
    return { ok: true }
  },

  /** Verify credentials and start a session. */
  async signIn(email: string, password: string): Promise<AuthResult> {
    const normalized = email.trim().toLowerCase()
    const account = findAccount(normalized)
    if (!account) return { ok: false, error: 'EMAIL_NOT_FOUND' }
    const hash = await sha256hex(account.salt + password)
    if (hash !== account.passwordHash) return { ok: false, error: 'WRONG_PASSWORD' }
    localStorage.setItem(SESSION_KEY, normalized)
    return { ok: true }
  },

  /**
   * Change password. Verifies current password first. Logs out the session
   * so the user must sign in with the new password.
   */
  async changePassword(
    email: string,
    currentPassword: string,
    newPassword: string,
  ): Promise<AuthResult> {
    const normalized = email.trim().toLowerCase()
    const accounts = loadAccounts()
    const idx = accounts.findIndex((a) => a.email === normalized)
    if (idx === -1) return { ok: false, error: 'EMAIL_NOT_FOUND' }

    const account = accounts[idx]
    const currentHash = await sha256hex(account.salt + currentPassword)
    if (currentHash !== account.passwordHash) return { ok: false, error: 'WRONG_PASSWORD' }
    if (currentPassword === newPassword) return { ok: false, error: 'SAME_PASSWORD' }

    const newSalt = generateSalt()
    const newHash = await sha256hex(newSalt + newPassword)
    accounts[idx] = { ...account, salt: newSalt, passwordHash: newHash }
    saveAccounts(accounts)

    // Log out any active session for this email
    if (localStorage.getItem(SESSION_KEY) === normalized) {
      localStorage.removeItem(SESSION_KEY)
    }
    return { ok: true }
  },

  signOut(): void {
    localStorage.removeItem(SESSION_KEY)
  },

  /** Returns the logged-in email, or null. */
  getSession(): string | null {
    return localStorage.getItem(SESSION_KEY)
  },
}
