'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { campaignAPI } from '../../../src/lib/api';

// ==============================
// TYPES
// ==============================
interface Campaign {
  id: string;
  name: string;
  platform: 'google' | 'meta' | 'both';
  budget: number;
  objective: 'conversions' | 'traffic' | 'awareness' | 'leads';
  status: 'active' | 'paused' | 'draft' | 'failed';
  ad_copy?: string;
  ctr?: number;
}

// ==============================
// COMPONENT
// ==============================
export default function CampaignDetail() {
  const { id } = useParams() as { id: string };
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const workspace_id =
      typeof window !== 'undefined'
        ? localStorage.getItem('workspace_id')
        : null;

    if (!workspace_id) return;

    campaignAPI.list(workspace_id).then((res) => {
      const found = res.data.find((c: Campaign) => c.id === id);
      setCampaign(found || null);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="text-white text-center p-20">Loading...</div>;
  if (!campaign) return <div className="text-white text-center p-20">Campaign not found</div>;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-2 text-blue-400">{campaign.name}</h1>
      <span
        className={`text-xs px-3 py-1 rounded-full ${
          campaign.status === 'active' ? 'bg-green-600' : 'bg-gray-600'
        }`}
      >
        {campaign.status}
      </span>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 mb-8">
        {[
          { label: 'Platform', value: campaign.platform },
          { label: 'Budget', value: `$${campaign.budget.toFixed(2)}` },
          { label: 'Objective', value: campaign.objective },
          { label: 'CTR', value: `${campaign.ctr?.toFixed(1) || 0}%` },
        ].map((item, i) => (
          <div key={i} className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <p className="text-gray-400 text-xs">{item.label}</p>
            <p className="text-lg font-bold mt-1">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
        <h3 className="font-bold text-gray-300 mb-3">📝 Ad Copy</h3>
        <pre className="text-sm text-gray-300 whitespace-pre-wrap">
          {campaign.ad_copy || 'No ad copy generated yet'}
        </pre>
      </div>
    </div>
  );
}