export function validateUserPayload(payload: { name?: string; email?: string }): {
  valid: boolean;
  error?: string;
} {
  const name = typeof payload.name === 'string' ? payload.name.trim() : '';
  const email = typeof payload.email === 'string' ? payload.email.trim() : '';
  if (name.length < 2 || !email.includes('@')) {
    return { valid: false, error: 'Invalid name or email' };
  }
  return { valid: true };
}
