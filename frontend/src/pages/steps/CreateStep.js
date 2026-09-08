import React from 'react';
import { useLang } from '@/lib/i18n';
import EbookCreator from '@/pages/steps/EbookCreator';
import SpreadsheetCreator from '@/pages/steps/SpreadsheetCreator';
import WebsiteCreator from '@/pages/steps/WebsiteCreator';
import { Button } from '@/components/ui/button';

export default function CreateStep(props) {
  const { t } = useLang();
  const { project, goTo } = props;
  if (!project.format) {
    return (
      <div className="max-w-xl">
        <h2 className="font-display text-2xl mb-2">{t('create.title')}</h2>
        <p className="text-muted-foreground mb-5">Pilih format produk terlebih dahulu.</p>
        <Button onClick={() => goTo('format')} data-testid="create-choose-format">Pilih Format</Button>
      </div>
    );
  }
  if (project.format === 'ebook') return <EbookCreator {...props} />;
  if (project.format === 'spreadsheet') return <SpreadsheetCreator {...props} />;
  if (project.format === 'website') return <WebsiteCreator {...props} />;
  return null;
}
