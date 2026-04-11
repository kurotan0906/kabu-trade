import { KpiRow } from '@/components/home/KpiRow';
import { TopScoresCard } from '@/components/home/TopScoresCard';
import { HoldingsQuickCard } from '@/components/home/HoldingsQuickCard';
import { LatestSignalsCard } from '@/components/home/LatestSignalsCard';
import { QuickSimulatorCard } from '@/components/home/QuickSimulatorCard';
import { PageHeader } from '@/components/ui';

const HomePage = () => (
  <>
    <PageHeader title="ダッシュボード" description="ポートフォリオとスコアの俯瞰" />
    <div className="space-y-6">
      <KpiRow />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TopScoresCard />
        </div>
        <HoldingsQuickCard />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <LatestSignalsCard />
        <QuickSimulatorCard />
      </div>
    </div>
  </>
);

export default HomePage;
