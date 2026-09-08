import React from 'react';
import { Loader2 } from 'lucide-react';

export const Working = ({ label, sub }) => (
  <div className="flex flex-col items-center justify-center py-16 text-center" data-testid="working-indicator">
    <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
    <p className="font-medium">{label || 'Memproses...'}</p>
    {sub && <p className="text-sm text-muted-foreground mt-1 max-w-md">{sub}</p>}
  </div>
);
