'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { agentAPI, campaignAPI } from '../../../src/lib/api';

// ==============================
// TYPES
// ==============================
type Platform = 'google' | 'meta' | 'both';
type Goal = 'conversions' | 'traffic' | 'awareness' | 'leads';
type Tone = 'professional' | 'casual' | 'urgent' | 'playful';

interface CampaignForm {
  message: string;
  platform: Platform;
  budget: string; // input value is string
  goal: Goal;
  tone: Tone;
}

interface AgentResult {
  ad_copy: string;
  strategy?: string;
  agent_log?: string[];
}

// ==============================
// COMPONENT
// ==============================
export default function NewCampaign() {
  const router = useRouter();
  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [form, setForm] = useState<CampaignForm>({
    message: '',
    platform: 'google',
    budget: '',
    goal: 'conversions',
    tone: 'professional',
  });

  const update = <K extends keyof CampaignForm>(key: K, value: CampaignForm[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const runAgent = async () => {
    if (!form.message || !form.budget) return;

    setLoading(true);
    setStep(2);

    try {
      const workspace_id =
        typeof window !== 'undefined'
          ? localStorage.getItem('workspace_id')
          : null;

      if (!workspace_id) throw new Error('Workspace ID not found');

      const res = await agentAPI.run({
        ...form,
        budget: parseFloat(form.budget),
        workspace_id,
        session_id: `new-${Date.now()}`,
      });

      setResult(res.data as AgentResult);
      setStep(3);
    } catch (e: any) {
      alert('Agent failed: ' + e.message);
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  const saveCampaign = async () => {
    try {
      const workspace_id =
        typeof window !== 'undefined'
          ? localStorage.getItem('workspace_id')
          : null;

      if (!workspace_id) throw new Error('Workspace ID not found');

      await campaignAPI.create({
        workspace_id,
        name: form.message.slice(0, 40),
        platform: form.platform,
        budget: parseFloat(form.budget),
        objective: form.goal,
        ad_copy: result?.ad_copy || '',
      });

      router.push('/dashboard');
    } catch (err: any) {
      alert('Failed to save campaign: ' + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-blue-400">New AI Campaign</h1>

      {/* STEP INDICATOR */}
      <div className="flex gap-2 mb-8">
        {['Brief', 'AI Processing', 'Review'].map((s, i) => (
          <div
            key={i}
            className={`flex-1 text-center py-2 rounded-lg text-sm font-medium ${
              step > i ? 'bg-blue-600' : 'bg-gray-700 text-gray-400'
            }`}
          >
            {i + 1}. {s}
          </div>
        ))}
      </div>

      {/* STEP 1 */}
      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Describe your campaign goal
            </label>
            <textarea
              value={form.message}
              onChange={(e) => update('message', e.target.value)}
              rows={4}
              placeholder='e.g. "Sell handmade leather bags to fashion-conscious men aged 25-45 in the USA with a $500 budget"'
              className="w-full bg-gray-800 rounded-lg p-3 outline-none border border-gray-600 focus:border-blue-500 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Platform</label>
              <select
                value={form.platform}
                onChange={(e) => update('platform', e.target.value as Platform)}
                className="w-full bg-gray-800 rounded-lg p-3 outline-none border border-gray-600"
              >
                <option value="google">Google Ads</option>
                <option value="meta">Meta Ads</option>
                <option value="both">Both</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Budget ($)</label>
              <input
                type="number"
                value={form.budget}
                onChange={(e) => update('budget', e.target.value)}
                placeholder="500"
                className="w-full bg-gray-800 rounded-lg p-3 outline-none border border-gray-600"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Goal</label>
              <select
                value={form.goal}
                onChange={(e) => update('goal', e.target.value as Goal)}
                className="w-full bg-gray-800 rounded-lg p-3 outline-none border border-gray-600"
              >
                <option value="conversions">Conversions</option>
                <option value="traffic">Traffic</option>
                <option value="awareness">Awareness</option>
                <option value="leads">Leads</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Tone</label>
              <select
                value={form.tone}
                onChange={(e) => update('tone', e.target.value as Tone)}
                className="w-full bg-gray-800 rounded-lg p-3 outline-none border border-gray-600"
              >
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="urgent">Urgent</option>
                <option value="playful">Playful</option>
              </select>
            </div>
          </div>

          <button
            onClick={runAgent}
            disabled={!form.message || !form.budget}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 py-4 rounded-lg font-bold text-lg"
          >
            🚀 Run AI Agents
          </button>
        </div>
      )}

      {/* STEP 2 */}
      {step === 2 && (
        <div className="text-center py-20 space-y-4">
          <div className="text-5xl animate-spin inline-block">⚙️</div>
          <p className="text-xl font-medium">AI Agents are working...</p>
          <div className="text-gray-400 space-y-1 text-sm">
            {[
              '🔍 Research Agent analyzing market...',
              '📋 Strategy Agent building plan...',
              '✍️  Copywriting Agent writing ads...',
              '✅ Validator Agent checking quality...',
            ].map((t, i) => (
              <p key={i}>{t}</p>
            ))}
          </div>
        </div>
      )}

      {/* STEP 3 */}
      {step === 3 && result && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-xl p-5 border border-green-700">
            <h3 className="font-bold text-green-400 mb-3">✅ AI Generated Ad Copy</h3>
            <pre className="text-sm text-gray-300 whitespace-pre-wrap">{result.ad_copy}</pre>
          </div>

          <div className="bg-gray-800 rounded-xl p-5 border border-blue-700">
            <h3 className="font-bold text-blue-400 mb-3">📋 Strategy</h3>
            <p className="text-sm text-gray-300">{result.strategy?.slice(0, 400)}...</p>
          </div>

          <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
            <h3 className="font-bold text-gray-300 mb-2">🤖 Agent Log</h3>
            {result.agent_log?.map((log, i) => (
              <p key={i} className="text-xs text-gray-400">
                ✔ {log}
              </p>
            ))}
          </div>

          <div className="flex gap-4">
            <button
              onClick={saveCampaign}
              className="flex-1 bg-green-600 hover:bg-green-700 py-3 rounded-lg font-bold"
            >
              💾 Save Campaign
            </button>
            <button
              onClick={() => setStep(1)}
              className="flex-1 bg-gray-700 hover:bg-gray-600 py-3 rounded-lg"
            >
              ← Redo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}