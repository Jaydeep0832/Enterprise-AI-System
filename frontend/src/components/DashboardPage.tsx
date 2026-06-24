import { useState, useEffect } from "react";
import {
  BarChart3, Activity, DollarSign, Zap, AlertTriangle,
  TrendingUp, Clock, CheckCircle, XCircle, RefreshCw,
  Bot, FlaskConical,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import api from "../services/api";

type MetricsSummary = {
  total_calls: number;
  success_count: number;
  error_count: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  providers: Record<string, number>;
  redis_memory_mb: number;
  latency_percentiles?: {
    p50: number; p95: number; p99: number;
    min: number; max: number; count: number;
  };
};

type FeedbackStats = {
  total: number;
  positive: number;
  negative: number;
  positive_rate: number;
};

const CHART_COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [recentCalls, setRecentCalls] = useState<any[]>([]);
  const [feedback, setFeedback] = useState<FeedbackStats | null>(null);
  const [costData, setCostData] = useState<any>(null);
  const [errorData, setErrorData] = useState<any>(null);
  const [agentMetrics, setAgentMetrics] = useState<Record<string, { calls: number; success: number; errors: number; avg_latency_ms: number; success_rate_pct: number }>>({});
  const [evalAlerts, setEvalAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [metricsRes, callsRes, fbRes, costRes, errorRes, agentRes, alertsRes] = await Promise.allSettled([
        api.get("/metrics"),
        api.get("/metrics/calls?limit=20"),
        api.get("/feedback/stats"),
        api.get("/metrics/cost"),
        api.get("/metrics/errors"),
        api.get("/metrics/agents"),
        api.get("/eval/alerts"),
      ]);

      if (metricsRes.status === "fulfilled") setMetrics(metricsRes.value.data);
      if (callsRes.status === "fulfilled") setRecentCalls(callsRes.value.data.calls || []);
      if (fbRes.status === "fulfilled") setFeedback(fbRes.value.data);
      if (costRes.status === "fulfilled") setCostData(costRes.value.data);
      if (errorRes.status === "fulfilled") setErrorData(errorRes.value.data);
      if (agentRes.status === "fulfilled") setAgentMetrics(agentRes.value.data?.agents || {});
      if (alertsRes.status === "fulfilled") setEvalAlerts(alertsRes.value.data?.alerts || []);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  // Prepare provider pie chart data
  const providerData = metrics?.providers
    ? Object.entries(metrics.providers).map(([name, count], idx) => ({
        name, value: count, fill: CHART_COLORS[idx % CHART_COLORS.length],
      }))
    : [];

  // Prepare daily cost chart data
  const dailyCostData = costData?.daily
    ? Object.entries(costData.daily)
        .slice(0, 14)
        .reverse()
        .map(([date, cost]) => ({
          date: date.slice(5),  // "MM-DD"
          cost: Number(cost),
        }))
    : [];

  // Prepare recent calls latency chart
  const latencyData = recentCalls
    .slice(0, 15)
    .reverse()
    .map((call, i) => ({
      index: i + 1,
      latency: call.latency_ms,
      provider: call.provider,
    }));

  const successRate = metrics
    ? Math.round((metrics.success_count / Math.max(metrics.total_calls, 1)) * 100)
    : 0;

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <BarChart3 size={28} className="text-blue-400" />
            System Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">Real-time observability & quality metrics</p>
        </div>
        <button
          onClick={fetchAll}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-sm text-slate-300 transition-colors border border-slate-700/50"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          icon={<Zap size={20} />}
          label="Total LLM Calls"
          value={metrics?.total_calls ?? 0}
          color="blue"
        />
        <KPICard
          icon={<CheckCircle size={20} />}
          label="Success Rate"
          value={`${successRate}%`}
          color="emerald"
          subtitle={`${metrics?.error_count ?? 0} errors`}
        />
        <KPICard
          icon={<Clock size={20} />}
          label="Avg Latency"
          value={`${(metrics?.avg_latency_ms ?? 0).toFixed(0)}ms`}
          color="amber"
          subtitle={metrics?.latency_percentiles ? `p95: ${metrics.latency_percentiles.p95.toFixed(0)}ms` : ""}
        />
        <KPICard
          icon={<DollarSign size={20} />}
          label="Total Cost"
          value={`$${(metrics?.total_cost_usd ?? 0).toFixed(4)}`}
          color="purple"
          subtitle={`${((metrics?.total_input_tokens ?? 0) + (metrics?.total_output_tokens ?? 0)).toLocaleString()} tokens`}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Provider Distribution */}
        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Activity size={16} className="text-blue-400" />
            Provider Distribution
          </h3>
          {providerData.length > 0 ? (
            <div className="flex items-center gap-6">
              <div className="w-40 h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={providerData}
                      cx="50%" cy="50%"
                      innerRadius={40} outerRadius={70}
                      dataKey="value"
                      stroke="none"
                    >
                      {providerData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: "#1e293b", border: "1px solid #334155",
                        borderRadius: "12px", color: "#f8fafc",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2 flex-1">
                {providerData.map((p) => (
                  <div key={p.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ background: p.fill }} />
                      <span className="text-slate-300 capitalize">{p.name}</span>
                    </div>
                    <span className="text-slate-400 font-mono">{p.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-sm italic">No provider data yet</p>
          )}
        </div>

        {/* Latency Chart */}
        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-emerald-400" />
            Recent Latency (ms)
          </h3>
          {latencyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={latencyData}>
                <defs>
                  <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="index" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "#1e293b", border: "1px solid #334155",
                    borderRadius: "12px", color: "#f8fafc", fontSize: "12px",
                  }}
                />
                <Area type="monotone" dataKey="latency" stroke="#10b981" fill="url(#latencyGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-500 text-sm italic">No latency data yet</p>
          )}
        </div>
      </div>

      {/* Cost & Feedback Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Cost Chart */}
        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <DollarSign size={16} className="text-purple-400" />
            Daily Cost Trend
          </h3>
          {dailyCostData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={dailyCostData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  contentStyle={{
                    background: "#1e293b", border: "1px solid #334155",
                    borderRadius: "12px", color: "#f8fafc", fontSize: "12px",
                  }}
                  formatter={(val: unknown) => [`$${Number(val).toFixed(6)}`, "Cost"]}
                />
                <Bar dataKey="cost" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-500 text-sm italic">No cost data yet</p>
          )}
        </div>

        {/* Feedback Stats */}
        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-400" />
            Feedback & Quality
          </h3>
          {feedback ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-800/60 rounded-xl p-3 text-center">
                  <div className="text-2xl font-bold text-white">{feedback.total}</div>
                  <div className="text-xs text-slate-400 mt-1">Total</div>
                </div>
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-center">
                  <div className="text-2xl font-bold text-emerald-400">{feedback.positive}</div>
                  <div className="text-xs text-emerald-400/70 mt-1">👍 Positive</div>
                </div>
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-center">
                  <div className="text-2xl font-bold text-red-400">{feedback.negative}</div>
                  <div className="text-xs text-red-400/70 mt-1">👎 Negative</div>
                </div>
              </div>
              {feedback.total > 0 && (
                <div>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Satisfaction Rate</span>
                    <span>{feedback.positive_rate}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2.5">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-emerald-400 h-2.5 rounded-full transition-all duration-500"
                      style={{ width: `${feedback.positive_rate}%` }}
                    />
                  </div>
                </div>
              )}
              {/* Error stats */}
              {errorData && (
                <div className="bg-slate-800/40 rounded-xl p-3 space-y-1">
                  <div className="text-xs text-slate-400 font-semibold">Error Rate</div>
                  <div className="flex gap-4 text-xs">
                    <span className="text-slate-300">Last 1h: <b className="text-amber-400">{errorData.last_1h?.errors ?? 0}</b></span>
                    <span className="text-slate-300">Last 24h: <b className="text-amber-400">{errorData.last_24h?.errors ?? 0}</b></span>
                    <span className="text-slate-300">Rate: <b className="text-amber-400">{errorData.error_rate_pct ?? 0}%</b></span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-slate-500 text-sm italic">No feedback data yet</p>
          )}
        </div>
      </div>

      {/* Agent Metrics & Eval Alerts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Performance */}
        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Bot size={16} className="text-cyan-400" />
            Agent Performance
          </h3>
          {Object.keys(agentMetrics).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(agentMetrics).map(([name, data]) => (
                <div key={name} className="flex items-center justify-between bg-slate-800/40 rounded-xl px-4 py-3 border border-slate-700/30">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-white capitalize">{name}</span>
                    <span className="text-xs text-slate-500">{data.calls} calls</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs">
                    <span className={data.success_rate_pct >= 90 ? "text-emerald-400" : data.success_rate_pct >= 70 ? "text-amber-400" : "text-red-400"}>
                      {data.success_rate_pct}% success
                    </span>
                    <span className="text-slate-400 font-mono">
                      {data.avg_latency_ms.toFixed(0)}ms avg
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 text-sm italic">No agent metrics yet</p>
          )}
        </div>

        {/* Eval Quality Alerts */}
        <div className="glass-panel rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <FlaskConical size={16} className="text-indigo-400" />
            Evaluation Quality
          </h3>
          {evalAlerts.length > 0 ? (
            <div className="space-y-2">
              {evalAlerts.map((alert: any, i: number) => (
                <div
                  key={i}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-xl border text-xs ${
                    alert.severity === "critical"
                      ? "bg-red-500/10 border-red-500/30 text-red-400"
                      : "bg-amber-500/10 border-amber-500/30 text-amber-400"
                  }`}
                >
                  <AlertTriangle size={14} />
                  <span className="font-medium capitalize">{alert.metric}</span>
                  <span className="text-slate-500">—</span>
                  <span className="flex-1 truncate">{alert.message}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 text-center">
              <CheckCircle size={24} className="text-emerald-400 mb-2" />
              <p className="text-sm text-emerald-400 font-medium">All Clear</p>
              <p className="text-xs text-slate-500 mt-1">No quality regressions detected</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Calls Table */}
      <div className="glass-panel rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Recent LLM Calls</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-slate-800">
                <th className="pb-3 pr-4">Time</th>
                <th className="pb-3 pr-4">Provider</th>
                <th className="pb-3 pr-4">Model</th>
                <th className="pb-3 pr-4">Latency</th>
                <th className="pb-3 pr-4">Tokens</th>
                <th className="pb-3 pr-4">Cost</th>
                <th className="pb-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {recentCalls.slice(0, 10).map((call, i) => (
                <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 pr-4 text-slate-400 font-mono text-xs">
                    {new Date(call.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-2.5 pr-4 capitalize text-slate-300">{call.provider}</td>
                  <td className="py-2.5 pr-4 text-slate-400 font-mono text-xs">{call.model}</td>
                  <td className="py-2.5 pr-4 font-mono">
                    <span className={call.latency_ms > 5000 ? "text-red-400" : call.latency_ms > 2000 ? "text-amber-400" : "text-emerald-400"}>
                      {call.latency_ms?.toFixed(0)}ms
                    </span>
                  </td>
                  <td className="py-2.5 pr-4 text-slate-400 font-mono text-xs">
                    {call.input_tokens + call.output_tokens}
                  </td>
                  <td className="py-2.5 pr-4 text-slate-400 font-mono text-xs">
                    ${call.cost_usd?.toFixed(6)}
                  </td>
                  <td className="py-2.5">
                    {call.success ? (
                      <CheckCircle size={14} className="text-emerald-400" />
                    ) : (
                      <XCircle size={14} className="text-red-400" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {recentCalls.length === 0 && (
            <p className="text-slate-500 text-sm italic text-center py-8">No LLM calls recorded yet</p>
          )}
        </div>
      </div>
    </div>
  );
}


// ── KPI Card Component ────────────────────────────────────────────────────────

function KPICard({
  icon, label, value, color, subtitle,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: "blue" | "emerald" | "amber" | "purple";
  subtitle?: string;
}) {
  const colorMap = {
    blue: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    amber: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    purple: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  };

  return (
    <div className={`rounded-2xl p-5 border ${colorMap[color]} transition-transform hover:scale-[1.02]`}>
      <div className={`${colorMap[color].split(" ")[0]} mb-3`}>{icon}</div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
      {subtitle && <div className="text-[10px] text-slate-500 mt-0.5">{subtitle}</div>}
    </div>
  );
}
