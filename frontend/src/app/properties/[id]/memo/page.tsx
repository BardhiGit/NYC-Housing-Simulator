"use client";

import { use, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { financialApi } from "@/lib/api/financial";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils/format";
import { FileText, CheckCircle, XCircle, AlertTriangle, HelpCircle, Play, DollarSign } from "lucide-react";

function MemoSection({ title, icon, bullets, narrative, iconColor }: {
  title: string; icon: React.ReactNode; bullets: string[];
  narrative: string; iconColor: string;
}) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-3">
        <div className={iconColor}>{icon}</div>
        <h3 className="text-sm font-semibold text-gray-100">{title}</h3>
      </div>
      <p className="text-xs text-gray-400 leading-relaxed mb-3">{narrative}</p>
      {bullets.length > 0 && (
        <ul className="space-y-1.5">
          {bullets.map((b, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
              <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-none ${iconColor.replace("text-", "bg-")}`} />
              {b}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function MemoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [generate, setGenerate] = useState(false);

  const { data: memo, isPending } = useQuery({
    queryKey: ["memo", id],
    queryFn: () => financialApi.memo(id),
    enabled: generate,
  });

  if (!generate) {
    return (
      <div className="max-w-3xl">
        <div className="card flex flex-col items-center text-center py-16">
          <div className="w-14 h-14 rounded-2xl bg-indigo-600/15 border border-indigo-500/20 flex items-center justify-center mb-4">
            <FileText size={24} className="text-indigo-400" />
          </div>
          <h2 className="text-base font-semibold text-gray-100 mb-2">Investment Memo</h2>
          <p className="text-sm text-gray-500 max-w-sm mb-6">
            Generate a plain-English deal summary covering strengths, risks, red flags,
            suggested offer price, negotiation points, and due diligence questions.
          </p>
          <Button size="lg" onClick={() => setGenerate(true)}>
            <Play size={14} /> Generate Memo
          </Button>
        </div>
      </div>
    );
  }

  if (isPending) {
    return (
      <div className="max-w-3xl card flex items-center justify-center h-40 gap-3 text-gray-500">
        <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        Generating investment memo…
      </div>
    );
  }

  if (!memo) return null;

  return (
    <div className="max-w-3xl space-y-5">
      {/* Header */}
      <div className="card border-indigo-500/20">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs text-indigo-400 font-medium mb-1">INVESTMENT MEMO</div>
            <h1 className="text-lg font-bold text-white">{memo.property_name}</h1>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs bg-indigo-600/20 text-indigo-300 border border-indigo-500/20 px-2 py-0.5 rounded-full">
                {memo.deal_type}
              </span>
              <span className="text-xs text-gray-500">Generated {memo.generated_at}</span>
            </div>
          </div>
          <FileText size={20} className="text-indigo-400 flex-none" />
        </div>
        <p className="text-sm text-gray-300 leading-relaxed mt-4 pt-4 border-t border-gray-800">
          {memo.executive_summary}
        </p>
      </div>

      {/* Deal overview */}
      <MemoSection
        title="Deal Overview"
        icon={<FileText size={15} />}
        iconColor="text-indigo-400"
        bullets={memo.deal_overview.bullets}
        narrative={memo.deal_overview.narrative}
      />

      <div className="grid md:grid-cols-2 gap-4">
        <MemoSection
          title="Strengths"
          icon={<CheckCircle size={15} />}
          iconColor="text-emerald-400"
          bullets={memo.strengths.bullets}
          narrative={memo.strengths.narrative}
        />
        <MemoSection
          title="Weaknesses"
          icon={<XCircle size={15} />}
          iconColor="text-red-400"
          bullets={memo.weaknesses.bullets}
          narrative={memo.weaknesses.narrative}
        />
      </div>

      <MemoSection
        title="Key Risks"
        icon={<AlertTriangle size={15} />}
        iconColor="text-amber-400"
        bullets={memo.key_risks.bullets}
        narrative={memo.key_risks.narrative}
      />

      <MemoSection
        title="What Would Make This Deal Work"
        icon={<CheckCircle size={15} />}
        iconColor="text-blue-400"
        bullets={memo.what_makes_it_work.bullets}
        narrative={memo.what_makes_it_work.narrative}
      />

      {/* Offer price */}
      {memo.suggested_offer_price && (
        <div className="card border-emerald-500/20 bg-emerald-500/5">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign size={15} className="text-emerald-400" />
            <h3 className="text-sm font-semibold text-emerald-300">Suggested Offer Price</h3>
          </div>
          <div className="text-3xl font-bold mono text-emerald-400 mb-2">
            {formatCurrency(memo.suggested_offer_price)}
          </div>
          <p className="text-xs text-gray-400">{memo.suggested_offer_rationale}</p>
        </div>
      )}

      {/* Negotiation */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-100 mb-3">Negotiation Points</h3>
        <ul className="space-y-2">
          {memo.negotiation_points.map((p, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
              <span className="text-gray-600 mono">{i + 1}.</span>{p}
            </li>
          ))}
        </ul>
      </div>

      {/* Due diligence */}
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <HelpCircle size={15} className="text-blue-400" />
          <h3 className="text-sm font-semibold text-gray-100">Questions Before Buying</h3>
        </div>
        <ul className="space-y-2">
          {memo.questions_before_buying.map((q, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
              <span className="text-gray-600">□</span>{q}
            </li>
          ))}
        </ul>
      </div>

      {/* Disclaimer */}
      <div className="text-xs text-gray-600 text-center pb-4">{memo.disclaimer}</div>
    </div>
  );
}
