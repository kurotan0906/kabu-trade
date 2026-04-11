import { useState } from 'react';
import {
  Button, Card, CardHeader, CardTitle, CardBody, Stat, Badge,
  Table, Thead, Tbody, Tr, Th, Td, Input, Field, Select, NumberInput,
  Dialog, EmptyState, PageHeader, Toolbar, Progress,
  Tabs, TabsList, TabsTrigger, TabsContent,
} from '@/components/ui';

const UiSandboxPage = () => {
  const [open, setOpen] = useState(false);
  const [num, setNum] = useState(100);
  return (
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <PageHeader
        title="UI Sandbox"
        description="プリミティブ確認用。リリースビルドでは削除する"
        actions={<Button onClick={() => setOpen(true)}>Dialog を開く</Button>}
      />

      <Toolbar>
        <Badge tone="brand">Brand</Badge>
        <Badge tone="success">Success</Badge>
        <Badge tone="warn">Warn</Badge>
        <Badge tone="danger">Danger</Badge>
      </Toolbar>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="評価額" value="¥640,800" accent="brand" hint="前日比 +0.0%" />
        <Stat label="目標進捗" value="32.04%" accent="success" />
        <Stat label="フェーズ" value={<Badge tone="brand">成長期</Badge>} />
        <Stat label="NISA残枠" value="¥2,272,000" hint="年間上限 ¥2,400,000" />
      </div>

      <Card>
        <CardHeader><CardTitle>Buttons</CardTitle></CardHeader>
        <CardBody className="flex flex-wrap gap-2">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="accent">Accent</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Progress</CardTitle></CardHeader>
        <CardBody className="space-y-3">
          <Progress value={32} showLabel />
          <Progress value={72} tone="success" showLabel />
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Form</CardTitle></CardHeader>
        <CardBody className="grid gap-3 sm:grid-cols-3">
          <Field label="銘柄コード"><Input placeholder="7203" /></Field>
          <Field label="口座種別">
            <Select defaultValue="general">
              <option value="general">特定</option>
              <option value="nisa">NISA</option>
            </Select>
          </Field>
          <Field label="数量"><NumberInput value={num} onChange={setNum} /></Field>
        </CardBody>
      </Card>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="chart">チャート</TabsTrigger>
          <TabsTrigger value="analysis">分析軸</TabsTrigger>
        </TabsList>
        <TabsContent value="overview"><Card><CardBody>概要タブ</CardBody></Card></TabsContent>
        <TabsContent value="chart"><Card><CardBody>チャートタブ</CardBody></Card></TabsContent>
        <TabsContent value="analysis"><Card><CardBody>分析軸タブ</CardBody></Card></TabsContent>
      </Tabs>

      <Table>
        <Thead>
          <Tr><Th>#</Th><Th>銘柄</Th><Th>スコア</Th><Th>レーティング</Th></Tr>
        </Thead>
        <Tbody>
          <Tr><Td>1</Td><Td>7203 トヨタ</Td><Td>82</Td><Td><Badge tone="success">買い</Badge></Td></Tr>
          <Tr><Td>2</Td><Td>9433 KDDI</Td><Td>78</Td><Td><Badge tone="brand">強い買い</Badge></Td></Tr>
        </Tbody>
      </Table>

      <EmptyState
        title="データがありません"
        description="スコアリングを実行するとここに表示されます"
        action={<Button variant="accent">▶ スコアリング実行</Button>}
      />

      <Dialog open={open} onClose={() => setOpen(false)} title="テスト Dialog" description="Esc / 背景クリックで閉じる">
        <p className="text-sm text-slate-600">コンテンツサンプル</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>キャンセル</Button>
          <Button onClick={() => setOpen(false)}>OK</Button>
        </div>
      </Dialog>
    </div>
  );
};

export default UiSandboxPage;
