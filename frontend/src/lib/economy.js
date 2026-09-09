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

// Call after any successful generation: refresh the pill and return the
// description string to attach to a success toast.
export const afterGeneration = (resp, t) => {
  refreshEconomy();
  return creditDescription(resp, t);
};
