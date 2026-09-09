// Shared helpers for post-generation feedback (credits + economy refresh).

// Tell the AppShell credits pill to refresh.
export const refreshEconomy = () => {
  try { window.dispatchEvent(new Event('khova:economy')); } catch (e) { /* noop */ }
};

// Build a human-friendly "credits used / remaining" description from a project
// response that may carry a non-persisted `_economy` field.
export const creditDescription = (resp, t) => {
  const eco = resp && resp._economy;
  if (!eco || eco.charged === undefined || eco.charged === null) return undefined;
  const parts = [];
  if (eco.charged > 0) parts.push(t ? t('credits.deducted', { n: eco.charged }) : `${eco.charged} credits used`);
  if (eco.credits !== undefined && eco.credits !== null) parts.push(t ? t('credits.remaining', { n: eco.credits }) : `${eco.credits} credits left`);
  return parts.join(' · ') || undefined;
};

// True when a request was blocked by the anonymous exploration rate limit.
export const isAnonLimit = (e) => {
  try {
    if (e && e.response && e.response.status === 429) return true;
    const d = e && e.response && e.response.data;
    if (d && d._structured && d._structured.anon_limited) return true;
    if (d && d._structured && String(d._structured.code || '').startsWith('anon_')) return true;
  } catch (_) { /* noop */ }
  return false;
};

// Call after any successful generation: refresh the pill and return the
// description string to attach to a success toast.
export const afterGeneration = (resp, t) => {
  refreshEconomy();
  return creditDescription(resp, t);
};

// Build the message for a FAILED generation. Only claims a refund when the
// server actually refunded credits (error.response.data._refund is present).
// Returns { message, description }.
export const generationErrorMessage = (e, t, fallback) => {
  const data = e && e.response && e.response.data;
  const detail = (data && data.detail) || fallback || (t ? t('gen.failed') : 'Generation failed. Please try again.');
  const refund = data && data._refund;
  if (refund && Number(refund.refunded) > 0) {
    refreshEconomy();
    const n = Number(refund.refunded);
    const bal = refund.balance;
    if (bal !== undefined && bal !== null) {
      return {
        message: t ? t('gen.refunded.full', { n, y: bal }) : `Generation failed. ${n} credits were refunded. Remaining credits: ${bal}.`,
        description: undefined,
      };
    }
    return {
      message: t ? t('gen.refunded', { n }) : `Generation failed. ${n} credits were refunded.`,
      description: undefined,
    };
  }
  return { message: detail, description: undefined };
};
