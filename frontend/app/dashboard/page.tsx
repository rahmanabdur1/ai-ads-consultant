'use client';

import { useState, useEffect } from 'react';
import { campaignAPI } from '../../src/lib/api';

// ==============================
// TYPES
// ==============================
type CampaignStatus = 'active' | 'paused' | 'draft' | 'failed';

interface Campaign {
  id: string;
  name: string;
  platform: string;
  budget: number;
  spend?: number;
  roi?: number;
  status: CampaignStatus;
}

interface Stats {
  total: number;
  active: number;
  spend: number;
  roi: number;
}

// ==============================
// COMPONENT
// ==============================
export default function Dashboard() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [stats, setStats] = useState<Stats>({
    total: 0,
    active: 0,
    spend: 0,
    roi: 0,
  });
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const workspace_id =
        typeof window !== 'undefined'
          ? localStorage.getItem('workspace_id')
          : null;

      if (!workspace_id) return;

      const res = await campaignAPI.list(workspace_id);

      const data: Campaign[] = res.data;

      setCampaigns(data);

      const totalSpend = data.reduce((sum, c) => sum + (c.spend || 0), 0);
      const totalROI = data.reduce((sum, c) => sum + (c.roi || 0), 0);

      setStats({
        total: data.length,
        active: data.filter((c) => c.status === 'active').length,
        spend: totalSpend,
        roi: data.length ? parseFloat((totalROI / data.length).toFixed(1)) : 0,
      });
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
    } finally {
      setLoading(false);
    }
  };

  const statusColor = (status: CampaignStatus) =>
    ({
      active: 'bg-green-500',
      paused: 'bg-yellow-500',
      draft: 'bg-gray-400',
      failed: 'bg-red-500',
    }[status] || 'bg-gray-400');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white text-xl">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-8 text-blue-400">
        AI Ads Dashboard
      </h1>

      {/* STATS CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Total Campaigns', value: stats.total, color: 'blue' },
          { label: 'Active', value: stats.active, color: 'green' },
          {
            label: 'Total Spend',
            value: `$${stats.spend.toFixed(2)}`,
            color: 'purple',
          },
          { label: 'Avg ROI', value: `${stats.roi}%`, color: 'orange' },
        ].map((card, i) => (
          <div
            key={i}
            className="bg-gray-800 rounded-xl p-5 border border-gray-700"
          >
            <p className="text-gray-400 text-sm">{card.label}</p>
            <p className={`text-3xl font-bold text-${card.color}-400 mt-1`}>
              {card.value}
            </p>
          </div>
        ))}
      </div>

      {/* CAMPAIGNS TABLE */}
      <div className="bg-gray-800 rounded-xl border border-gray-700">
        <div className="flex justify-between items-center p-5 border-b border-gray-700">
          <h2 className="text-xl font-semibold">Campaigns</h2>
          <a
            href="/campaigns/new"
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium"
          >
            + New Campaign
          </a>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                {['Name', 'Platform', 'Budget', 'Status', 'Actions'].map(
                  (h) => (
                    <th key={h} className="text-left p-4">
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>

            <tbody>
              {campaigns.map((c) => (
                <tr
                  key={c.id}
                  className="border-b border-gray-700 hover:bg-gray-750"
                >
                  <td className="p-4 font-medium">{c.name}</td>
                  <td className="p-4 capitalize">{c.platform}</td>
                  <td className="p-4">${c.budget}</td>
                  <td className="p-4">
                    <span
                      className={`${statusColor(
                        c.status
                      )} px-2 py-1 rounded-full text-xs text-white`}
                    >
                      {c.status}
                    </span>
                  </td>
                  <td className="p-4">
                    <a
                      href={`/campaigns/${c.id}`}
                      className="text-blue-400 hover:underline mr-3"
                    >
                      View
                    </a>
                    <button
                      onClick={() =>
                        campaignAPI.delete(c.id).then(fetchCampaigns)
                      }
                      className="text-red-400 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}

              {campaigns.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="p-8 text-center text-gray-500"
                  >
                    No campaigns yet. Create your first one!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}