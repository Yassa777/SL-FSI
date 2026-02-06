import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Area, AreaChart, ComposedChart, Bar, Legend } from 'recharts';

// Reserve data with key events
const reserveData = [
  { date: '2019-04', reserves: 7214, importCover: 4.52, event: 'Easter Sunday bombings' },
  { date: '2019-07', reserves: 7495, importCover: 4.69 },
  { date: '2019-10', reserves: 7642, importCover: 4.78 },
  { date: '2020-01', reserves: 7584, importCover: 6.08 },
  { date: '2020-03', reserves: 7534, importCover: 6.25, event: 'COVID-19 begins' },
  { date: '2020-06', reserves: 6693, importCover: 5.02 },
  { date: '2020-09', reserves: 5885, importCover: 4.12 },
  { date: '2020-12', reserves: 5664, importCover: 3.46 },
  { date: '2021-01', reserves: 4849, importCover: 2.96 },
  { date: '2021-03', reserves: 4055, importCover: 2.11, event: 'PBOC swap activated' },
  { date: '2021-05', reserves: 4012, importCover: 2.09 },
  { date: '2021-07', reserves: 2806, importCover: 1.64, event: 'Food emergency' },
  { date: '2021-09', reserves: 2704, importCover: 1.77, event: 'Economic emergency' },
  { date: '2021-11', reserves: 1588, importCover: 0.90, event: 'Critical low' },
  { date: '2022-01', reserves: 2361, importCover: 1.28 },
  { date: '2022-03', reserves: 1917, importCover: 1.05 },
  { date: '2022-04', reserves: 1812, importCover: 1.07, event: 'SOVEREIGN DEFAULT', isDefault: true },
  { date: '2022-06', reserves: 1854, importCover: 1.25 },
  { date: '2022-07', reserves: 1817, importCover: 1.25, event: 'New president' },
  { date: '2022-09', reserves: 1779, importCover: 1.22 },
  { date: '2022-12', reserves: 1898, importCover: 1.31 },
  { date: '2023-03', reserves: 2694, importCover: 1.86, event: 'IMF EFF approved' },
  { date: '2023-06', reserves: 3529, importCover: 2.05 },
  { date: '2023-09', reserves: 3599, importCover: 2.09 },
  { date: '2023-12', reserves: 4401, importCover: 2.55 },
  { date: '2024-06', reserves: 5498, importCover: 2.85 },
  { date: '2024-12', reserves: 6122, importCover: 3.18, event: 'Recovery milestone' },
  { date: '2025-09', reserves: 6244, importCover: 3.05 },
];

// Quarterly ARA data
const araData = [
  { quarter: 'Q1 2021', reserves: 4055, araReq: 4520, araRatio: 89.7, ggRatio: 2.15 },
  { quarter: 'Q2 2021', reserves: 4012, araReq: 4200, araRatio: 95.5, ggRatio: 1.85 },
  { quarter: 'Q3 2021', reserves: 2704, araReq: 3809, araRatio: 71.0, ggRatio: 1.02 },
  { quarter: 'Q4 2021', reserves: 3139, araReq: 3691, araRatio: 85.1, ggRatio: 1.31 },
  { quarter: 'Q1 2022', reserves: 1917, araReq: 2821, araRatio: 68.0, ggRatio: 1.18 },
  { quarter: 'Q2 2022', reserves: 1854, araReq: 2257, araRatio: 82.1, ggRatio: 1.25 },
  { quarter: 'Q3 2022', reserves: 1779, araReq: 2272, araRatio: 78.3, ggRatio: 1.39 },
  { quarter: 'Q4 2022', reserves: 1898, araReq: 2164, araRatio: 87.7, ggRatio: 1.48 },
  { quarter: 'Q1 2023', reserves: 2694, araReq: 2548, araRatio: 105.7, ggRatio: 2.10 },
  { quarter: 'Q2 2023', reserves: 3529, araReq: 2680, araRatio: 131.7, ggRatio: 2.45 },
];

// Lead time comparison data
const leadTimeData = [
  { metric: 'Import Cover < 2 mo', months: 9, category: 'actionable', threshold: '< 2 months' },
  { metric: 'IMF ARA < 100%', months: 6, category: 'actionable', threshold: '< 100%' },
  { metric: 'GG Ratio < 1.5', months: 6, category: 'warning', threshold: '< 1.5' },
  { metric: 'Import Cover < 1 mo', months: 5, category: 'critical', threshold: '< 1 month' },
];

// Threshold analysis data with loss function calculations
// L(τ) = α × I[Lead Time < 6 months] + (1-α) × False Alarm Rate
const thresholdAnalysisData = [
  { threshold: 1.0, leadTime: 5, falseAlarmMonths: 0, falseAlarmRate: 0.0 },
  { threshold: 1.5, leadTime: 7, falseAlarmMonths: 0, falseAlarmRate: 0.0 },
  { threshold: 2.0, leadTime: 9, falseAlarmMonths: 0, falseAlarmRate: 0.0 },
  { threshold: 2.5, leadTime: 12, falseAlarmMonths: 0, falseAlarmRate: 0.0 },
  { threshold: 3.0, leadTime: 62, falseAlarmMonths: 0, falseAlarmRate: 0.0 },
  { threshold: 3.5, leadTime: 66, falseAlarmMonths: 4, falseAlarmRate: 5.6 },
  { threshold: 4.0, leadTime: 68, falseAlarmMonths: 8, falseAlarmRate: 11.1 },
  { threshold: 4.5, leadTime: 70, falseAlarmMonths: 14, falseAlarmRate: 19.4 },
  { threshold: 5.0, leadTime: 74, falseAlarmMonths: 22, falseAlarmRate: 30.6 },
].map(d => {
  // Calculate L(τ) for different α values
  const indicator = d.leadTime < 6 ? 1 : 0;
  const far = d.falseAlarmRate / 100;
  return {
    ...d,
    L_0_6: +(0.6 * indicator + 0.4 * far).toFixed(3),
    L_0_7: +(0.7 * indicator + 0.3 * far).toFixed(3),
    L_0_75: +(0.75 * indicator + 0.25 * far).toFixed(3),
    L_0_8: +(0.8 * indicator + 0.2 * far).toFixed(3),
    L_0_9: +(0.9 * indicator + 0.1 * far).toFixed(3),
  };
});

// ARA component breakdown
const araComponents = [
  { component: 'Broad Money (M2)', weight: '5%', value: 44000, contribution: 2200, color: '#3B82F6' },
  { component: 'Short-term Debt', weight: '30%', value: 2661, contribution: 798, color: '#EF4444' },
  { component: 'Portfolio Liabilities', weight: '15%', value: 4040, contribution: 606, color: '#F59E0B' },
  { component: 'Annual Exports', weight: '5%', value: 4100, contribution: 205, color: '#10B981' },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div style={{
        background: 'rgba(15, 23, 42, 0.95)',
        border: '1px solid rgba(148, 163, 184, 0.2)',
        borderRadius: '8px',
        padding: '12px 16px',
        boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
        backdropFilter: 'blur(8px)',
      }}>
        <p style={{ color: '#94A3B8', fontSize: '12px', marginBottom: '8px', fontFamily: 'JetBrains Mono, monospace' }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color, fontSize: '14px', fontWeight: 600, margin: '4px 0' }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}{p.name.includes('Cover') ? ' mo' : p.name.includes('Ratio') || p.name.includes('%') ? '%' : 'M'}
          </p>
        ))}
        {data.event && (
          <p style={{ 
            color: data.isDefault ? '#EF4444' : '#F59E0B', 
            fontSize: '11px', 
            marginTop: '8px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ⚡ {data.event}
          </p>
        )}
      </div>
    );
  }
  return null;
};

const MetricCard = ({ title, value, subtitle, trend, color = '#3B82F6', delay = 0 }) => (
  <div style={{
    background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
    borderRadius: '16px',
    padding: '24px',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    animation: `slideUp 0.6s ease-out ${delay}s both`,
    position: 'relative',
    overflow: 'hidden',
  }}>
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '3px',
      background: `linear-gradient(90deg, ${color}, transparent)`,
    }} />
    <p style={{ 
      color: '#64748B', 
      fontSize: '12px', 
      textTransform: 'uppercase', 
      letterSpacing: '1.5px',
      marginBottom: '8px',
      fontWeight: 500,
    }}>{title}</p>
    <p style={{ 
      color: '#F1F5F9', 
      fontSize: '36px', 
      fontWeight: 700,
      fontFamily: 'JetBrains Mono, monospace',
      marginBottom: '4px',
    }}>{value}</p>
    <p style={{ color: '#94A3B8', fontSize: '13px' }}>{subtitle}</p>
    {trend && (
      <span style={{
        position: 'absolute',
        top: '24px',
        right: '24px',
        color: trend > 0 ? '#10B981' : '#EF4444',
        fontSize: '12px',
        fontWeight: 600,
      }}>
        {trend > 0 ? '↑' : '↓'} {Math.abs(trend)} months
      </span>
    )}
  </div>
);

const Section = ({ title, children, id }) => (
  <section id={id} style={{ marginBottom: '64px' }}>
    <h2 style={{
      color: '#F1F5F9',
      fontSize: '24px',
      fontWeight: 600,
      marginBottom: '24px',
      paddingBottom: '12px',
      borderBottom: '1px solid rgba(148, 163, 184, 0.15)',
      fontFamily: 'Newsreader, Georgia, serif',
    }}>{title}</h2>
    {children}
  </section>
);

const NavItem = ({ label, active, onClick }) => (
  <button
    onClick={onClick}
    style={{
      background: active ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
      border: 'none',
      color: active ? '#3B82F6' : '#64748B',
      padding: '8px 16px',
      borderRadius: '6px',
      cursor: 'pointer',
      fontSize: '13px',
      fontWeight: 500,
      transition: 'all 0.2s ease',
      whiteSpace: 'nowrap',
    }}
  >
    {label}
  </button>
);

export default function App() {
  const [activeSection, setActiveSection] = useState('overview');
  const [selectedMetric, setSelectedMetric] = useState('importCover');
  const [showAnnotations, setShowAnnotations] = useState(true);

  const scrollToSection = (id) => {
    setActiveSection(id);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #0F172A 0%, #1E293B 50%, #0F172A 100%)',
      color: '#E2E8F0',
      fontFamily: 'system-ui, -apple-system, sans-serif',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;500;600&display=swap');
        
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        @keyframes drawLine {
          from { stroke-dashoffset: 1000; }
          to { stroke-dashoffset: 0; }
        }

        ::-webkit-scrollbar {
          width: 8px;
        }
        ::-webkit-scrollbar-track {
          background: rgba(30, 41, 59, 0.5);
        }
        ::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.5);
          border-radius: 4px;
        }
      `}</style>

      {/* Header */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: 'rgba(15, 23, 42, 0.9)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
        padding: '16px 32px',
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ 
              fontSize: '18px', 
              fontWeight: 600, 
              color: '#F1F5F9',
              fontFamily: 'Newsreader, Georgia, serif',
            }}>
              Reserve Adequacy Benchmarking
            </h1>
            <p style={{ fontSize: '12px', color: '#64748B' }}>Sri Lanka 2022 Default — Predictive Power Assessment</p>
          </div>
          <nav style={{ display: 'flex', gap: '4px' }}>
            <NavItem label="Overview" active={activeSection === 'overview'} onClick={() => scrollToSection('overview')} />
            <NavItem label="Timeline" active={activeSection === 'timeline'} onClick={() => scrollToSection('timeline')} />
            <NavItem label="Benchmarks" active={activeSection === 'benchmarks'} onClick={() => scrollToSection('benchmarks')} />
            <NavItem label="Lead Time" active={activeSection === 'leadtime'} onClick={() => scrollToSection('leadtime')} />
            <NavItem label="Threshold" active={activeSection === 'threshold'} onClick={() => scrollToSection('threshold')} />
            <NavItem label="Framework" active={activeSection === 'framework'} onClick={() => scrollToSection('framework')} />
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '48px 32px' }}>
        
        {/* Hero Section */}
        <Section title="" id="overview">
          <div style={{
            textAlign: 'center',
            marginBottom: '64px',
            animation: 'fadeIn 1s ease-out',
          }}>
            <p style={{ 
              color: '#3B82F6', 
              fontSize: '13px', 
              textTransform: 'uppercase', 
              letterSpacing: '3px',
              marginBottom: '16px',
              fontWeight: 500,
            }}>
              Research Preview
            </p>
            <h1 style={{
              fontSize: '48px',
              fontWeight: 600,
              color: '#F1F5F9',
              marginBottom: '24px',
              fontFamily: 'Newsreader, Georgia, serif',
              lineHeight: 1.2,
            }}>
              Could the Default<br />Have Been Predicted?
            </h1>
            <p style={{
              fontSize: '18px',
              color: '#94A3B8',
              maxWidth: '600px',
              margin: '0 auto 32px',
              lineHeight: 1.6,
            }}>
              Multiple reserve adequacy benchmarks provided <strong style={{ color: '#F59E0B' }}>6–9 months</strong> of 
              actionable warning before Sri Lanka's April 2022 sovereign default.
            </p>
          </div>

          {/* Key Metrics Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '20px',
            marginBottom: '48px',
          }}>
            <MetricCard 
              title="Maximum Lead Time" 
              value="9 mo" 
              subtitle="Import Cover < 2 months"
              color="#10B981"
              delay={0.1}
            />
            <MetricCard 
              title="IMF ARA Warning" 
              value="6 mo" 
              subtitle="Below 100% threshold"
              color="#3B82F6"
              delay={0.2}
            />
            <MetricCard 
              title="Critical Alert" 
              value="5 mo" 
              subtitle="Import Cover < 1 month"
              color="#EF4444"
              delay={0.3}
            />
            <MetricCard 
              title="Reserve Low" 
              value="$1.6B" 
              subtitle="November 2021"
              color="#F59E0B"
              delay={0.4}
            />
          </div>
        </Section>

        {/* Timeline Visualization */}
        <Section title="Reserve Trajectory & Crisis Events" id="timeline">
          <div style={{
            background: 'rgba(30, 41, 59, 0.5)',
            borderRadius: '16px',
            padding: '32px',
            border: '1px solid rgba(148, 163, 184, 0.1)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => setSelectedMetric('reserves')}
                  style={{
                    background: selectedMetric === 'reserves' ? '#3B82F6' : 'rgba(59, 130, 246, 0.1)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    color: selectedMetric === 'reserves' ? '#fff' : '#3B82F6',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 500,
                  }}
                >
                  Gross Reserves (USD)
                </button>
                <button
                  onClick={() => setSelectedMetric('importCover')}
                  style={{
                    background: selectedMetric === 'importCover' ? '#10B981' : 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    color: selectedMetric === 'importCover' ? '#fff' : '#10B981',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 500,
                  }}
                >
                  Import Cover (months)
                </button>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={showAnnotations} 
                  onChange={(e) => setShowAnnotations(e.target.checked)}
                  style={{ accentColor: '#3B82F6' }}
                />
                <span style={{ fontSize: '13px', color: '#94A3B8' }}>Show events</span>
              </label>
            </div>

            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={reserveData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <defs>
                  <linearGradient id="reserveGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="coverGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                <XAxis 
                  dataKey="date" 
                  stroke="#64748B" 
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }}
                />
                <YAxis 
                  yAxisId="left"
                  stroke="#64748B" 
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }}
                  tickFormatter={(v) => selectedMetric === 'reserves' ? `$${(v/1000).toFixed(1)}B` : `${v} mo`}
                  domain={selectedMetric === 'reserves' ? [0, 8000] : [0, 7]}
                />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Threshold reference lines */}
                {selectedMetric === 'importCover' && (
                  <>
                    <ReferenceLine yAxisId="left" y={3} stroke="#F59E0B" strokeDasharray="5 5" label={{ value: '3 mo (IMF min)', fill: '#F59E0B', fontSize: 10, position: 'right' }} />
                    <ReferenceLine yAxisId="left" y={2} stroke="#EF4444" strokeDasharray="5 5" label={{ value: '2 mo (warning)', fill: '#EF4444', fontSize: 10, position: 'right' }} />
                    <ReferenceLine yAxisId="left" y={1} stroke="#DC2626" strokeDasharray="5 5" label={{ value: '1 mo (critical)', fill: '#DC2626', fontSize: 10, position: 'right' }} />
                  </>
                )}
                
                {/* Default line */}
                <ReferenceLine 
                  yAxisId="left"
                  x="2022-04" 
                  stroke="#EF4444" 
                  strokeWidth={2}
                  label={{ value: 'DEFAULT', fill: '#EF4444', fontSize: 11, fontWeight: 600, position: 'top' }}
                />

                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey={selectedMetric}
                  stroke={selectedMetric === 'reserves' ? '#3B82F6' : '#10B981'}
                  strokeWidth={2}
                  fill={selectedMetric === 'reserves' ? 'url(#reserveGradient)' : 'url(#coverGradient)'}
                />

                {/* Event markers */}
                {showAnnotations && reserveData.filter(d => d.event && !d.isDefault).map((d, i) => (
                  <ReferenceLine
                    key={i}
                    yAxisId="left"
                    x={d.date}
                    stroke="rgba(245, 158, 11, 0.5)"
                    strokeDasharray="3 3"
                  />
                ))}
              </ComposedChart>
            </ResponsiveContainer>

            {/* Event Legend */}
            {showAnnotations && (
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '16px',
                marginTop: '24px',
                padding: '16px',
                background: 'rgba(15, 23, 42, 0.5)',
                borderRadius: '8px',
              }}>
                {reserveData.filter(d => d.event).map((d, i) => (
                  <div key={i} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    padding: '4px 12px',
                    background: d.isDefault ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.1)',
                    borderRadius: '4px',
                    border: `1px solid ${d.isDefault ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.2)'}`,
                  }}>
                    <span style={{ 
                      fontSize: '11px', 
                      color: '#64748B',
                      fontFamily: 'JetBrains Mono, monospace',
                    }}>{d.date}</span>
                    <span style={{ 
                      fontSize: '12px', 
                      color: d.isDefault ? '#EF4444' : '#F59E0B',
                      fontWeight: 500,
                    }}>{d.event}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Section>

        {/* Benchmark Comparison */}
        <Section title="Benchmark Performance Comparison" id="benchmarks">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            {/* IMF ARA Chart */}
            <div style={{
              background: 'rgba(30, 41, 59, 0.5)',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid rgba(148, 163, 184, 0.1)',
            }}>
              <h3 style={{ 
                color: '#F1F5F9', 
                fontSize: '16px', 
                marginBottom: '20px',
                fontWeight: 500,
              }}>IMF ARA Ratio vs 100% Threshold</h3>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={araData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis dataKey="quarter" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={10} tickLine={false} domain={[0, 140]} tickFormatter={(v) => `${v}%`} />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={100} stroke="#10B981" strokeDasharray="5 5" label={{ value: '100% adequate', fill: '#10B981', fontSize: 10 }} />
                  <Bar dataKey="araRatio" fill="#3B82F6" radius={[4, 4, 0, 0]} name="ARA Ratio" />
                </ComposedChart>
              </ResponsiveContainer>
              <p style={{ fontSize: '12px', color: '#64748B', marginTop: '12px' }}>
                First breach: Q3 2021 at 71% — <strong style={{ color: '#F59E0B' }}>6 months before default</strong>
              </p>
            </div>

            {/* GG Ratio Chart */}
            <div style={{
              background: 'rgba(30, 41, 59, 0.5)',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid rgba(148, 163, 184, 0.1)',
            }}>
              <h3 style={{ 
                color: '#F1F5F9', 
                fontSize: '16px', 
                marginBottom: '20px',
                fontWeight: 500,
              }}>Greenspan-Guidotti Ratio</h3>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={araData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis dataKey="quarter" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={10} tickLine={false} domain={[0, 3]} />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={1.5} stroke="#F59E0B" strokeDasharray="5 5" label={{ value: 'Warning (1.5)', fill: '#F59E0B', fontSize: 10 }} />
                  <ReferenceLine y={1.0} stroke="#EF4444" strokeDasharray="5 5" label={{ value: 'Critical (1.0)', fill: '#EF4444', fontSize: 10 }} />
                  <Area type="monotone" dataKey="ggRatio" stroke="#8B5CF6" fill="rgba(139, 92, 246, 0.2)" name="GG Ratio" />
                  <Line type="monotone" dataKey="ggRatio" stroke="#8B5CF6" strokeWidth={2} dot={{ fill: '#8B5CF6', r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
              <p style={{ fontSize: '12px', color: '#64748B', marginTop: '12px' }}>
                Near-breach: Q3 2021 at 1.02 — <strong style={{ color: '#F59E0B' }}>6 months before default</strong>
              </p>
            </div>
          </div>

          {/* ARA Component Breakdown */}
          <div style={{
            background: 'rgba(30, 41, 59, 0.5)',
            borderRadius: '16px',
            padding: '24px',
            border: '1px solid rgba(148, 163, 184, 0.1)',
            marginTop: '24px',
          }}>
            <h3 style={{ 
              color: '#F1F5F9', 
              fontSize: '16px', 
              marginBottom: '20px',
              fontWeight: 500,
            }}>IMF ARA Component Breakdown — Q3 2021 (Crisis Quarter)</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
              {araComponents.map((c, i) => (
                <div key={i} style={{
                  background: 'rgba(15, 23, 42, 0.5)',
                  borderRadius: '12px',
                  padding: '20px',
                  borderLeft: `4px solid ${c.color}`,
                }}>
                  <p style={{ color: '#94A3B8', fontSize: '12px', marginBottom: '8px' }}>{c.component}</p>
                  <p style={{ 
                    color: '#F1F5F9', 
                    fontSize: '24px', 
                    fontWeight: 600,
                    fontFamily: 'JetBrains Mono, monospace',
                  }}>${c.contribution}M</p>
                  <p style={{ color: '#64748B', fontSize: '11px', marginTop: '4px' }}>
                    {c.weight} × ${(c.value/1000).toFixed(1)}B
                  </p>
                </div>
              ))}
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '20px',
              padding: '16px',
              background: 'rgba(239, 68, 68, 0.1)',
              borderRadius: '8px',
              border: '1px solid rgba(239, 68, 68, 0.2)',
            }}>
              <div>
                <span style={{ color: '#94A3B8', fontSize: '13px' }}>Total ARA Requirement:</span>
                <span style={{ color: '#F1F5F9', fontSize: '18px', fontWeight: 600, marginLeft: '12px', fontFamily: 'JetBrains Mono, monospace' }}>$3,809M</span>
              </div>
              <div>
                <span style={{ color: '#94A3B8', fontSize: '13px' }}>Actual Reserves:</span>
                <span style={{ color: '#EF4444', fontSize: '18px', fontWeight: 600, marginLeft: '12px', fontFamily: 'JetBrains Mono, monospace' }}>$2,704M</span>
              </div>
              <div>
                <span style={{ color: '#94A3B8', fontSize: '13px' }}>Coverage:</span>
                <span style={{ color: '#EF4444', fontSize: '18px', fontWeight: 600, marginLeft: '12px', fontFamily: 'JetBrains Mono, monospace' }}>71%</span>
              </div>
            </div>
          </div>
        </Section>

        {/* Lead Time Analysis */}
        <Section title="Early Warning Lead Time Analysis" id="leadtime">
          <div style={{
            background: 'rgba(30, 41, 59, 0.5)',
            borderRadius: '16px',
            padding: '32px',
            border: '1px solid rgba(148, 163, 184, 0.1)',
          }}>
            <div style={{ display: 'flex', gap: '32px' }}>
              {/* Lead time bars */}
              <div style={{ flex: 1 }}>
                {leadTimeData.map((d, i) => (
                  <div key={i} style={{ marginBottom: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ color: '#E2E8F0', fontSize: '14px', fontWeight: 500 }}>{d.metric}</span>
                      <span style={{ 
                        color: d.category === 'actionable' ? '#10B981' : d.category === 'warning' ? '#F59E0B' : '#EF4444',
                        fontSize: '14px',
                        fontWeight: 600,
                        fontFamily: 'JetBrains Mono, monospace',
                      }}>{d.months} months</span>
                    </div>
                    <div style={{
                      height: '32px',
                      background: 'rgba(15, 23, 42, 0.8)',
                      borderRadius: '6px',
                      overflow: 'hidden',
                      position: 'relative',
                    }}>
                      <div style={{
                        height: '100%',
                        width: `${(d.months / 12) * 100}%`,
                        background: d.category === 'actionable' 
                          ? 'linear-gradient(90deg, #10B981, #059669)' 
                          : d.category === 'warning'
                          ? 'linear-gradient(90deg, #F59E0B, #D97706)'
                          : 'linear-gradient(90deg, #EF4444, #DC2626)',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        paddingLeft: '12px',
                        animation: `slideRight 0.8s ease-out ${i * 0.15}s both`,
                      }}>
                        <span style={{ color: '#fff', fontSize: '11px', fontWeight: 500 }}>{d.threshold}</span>
                      </div>
                    </div>
                  </div>
                ))}
                <style>{`
                  @keyframes slideRight {
                    from { width: 0; }
                  }
                `}</style>
              </div>

              {/* Timeline visualization */}
              <div style={{ width: '320px' }}>
                <h4 style={{ color: '#94A3B8', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px' }}>
                  Optimal Warning Window
                </h4>
                <div style={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  borderRadius: '12px',
                  padding: '20px',
                }}>
                  <div style={{ borderLeft: '2px solid #3B82F6', paddingLeft: '20px' }}>
                    <div style={{ marginBottom: '20px', position: 'relative' }}>
                      <div style={{
                        position: 'absolute',
                        left: '-26px',
                        top: '4px',
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: '#F59E0B',
                      }} />
                      <p style={{ color: '#F59E0B', fontSize: '12px', fontWeight: 600 }}>July 2021</p>
                      <p style={{ color: '#94A3B8', fontSize: '12px' }}>Import Cover falls below 2 months (1.64 mo)</p>
                    </div>
                    <div style={{ marginBottom: '20px', position: 'relative' }}>
                      <div style={{
                        position: 'absolute',
                        left: '-26px',
                        top: '4px',
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: '#3B82F6',
                      }} />
                      <p style={{ color: '#3B82F6', fontSize: '12px', fontWeight: 600 }}>September 2021</p>
                      <p style={{ color: '#94A3B8', fontSize: '12px' }}>IMF ARA falls below 100% (71%)</p>
                      <p style={{ color: '#94A3B8', fontSize: '12px' }}>GG Ratio approaches 1.0 (1.02)</p>
                    </div>
                    <div style={{ marginBottom: '20px', position: 'relative' }}>
                      <div style={{
                        position: 'absolute',
                        left: '-26px',
                        top: '4px',
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: '#EF4444',
                      }} />
                      <p style={{ color: '#EF4444', fontSize: '12px', fontWeight: 600 }}>November 2021</p>
                      <p style={{ color: '#94A3B8', fontSize: '12px' }}>Import Cover below 1 month (0.90 mo)</p>
                    </div>
                    <div style={{ position: 'relative' }}>
                      <div style={{
                        position: 'absolute',
                        left: '-26px',
                        top: '4px',
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: '#EF4444',
                        animation: 'pulse 2s infinite',
                      }} />
                      <p style={{ color: '#EF4444', fontSize: '12px', fontWeight: 600 }}>April 12, 2022</p>
                      <p style={{ color: '#EF4444', fontSize: '13px', fontWeight: 600 }}>SOVEREIGN DEFAULT</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Section>

        {/* Threshold Optimization Analysis */}
        <Section title="Threshold Optimization & Loss Function Analysis" id="threshold">
          <div style={{
            background: 'rgba(30, 41, 59, 0.5)',
            borderRadius: '16px',
            padding: '32px',
            border: '1px solid rgba(148, 163, 184, 0.1)',
            marginBottom: '24px',
          }}>
            {/* Loss Function Explanation */}
            <div style={{
              background: 'rgba(59, 130, 246, 0.1)',
              borderRadius: '12px',
              padding: '20px',
              marginBottom: '24px',
              border: '1px solid rgba(59, 130, 246, 0.2)',
            }}>
              <h4 style={{ color: '#3B82F6', fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>
                Loss Function Definition
              </h4>
              <p style={{ color: '#94A3B8', fontSize: '13px', lineHeight: 1.6, fontFamily: 'JetBrains Mono, monospace' }}>
                L(τ) = α × I[Lead Time &lt; 6 months] + (1-α) × False Alarm Rate
              </p>
              <p style={{ color: '#64748B', fontSize: '12px', marginTop: '8px' }}>
                Where α weights the penalty for insufficient lead time vs. false alarm costs. 
                Higher α prioritizes early warning; lower α prioritizes precision.
              </p>
            </div>

            {/* Loss Function Chart */}
            <h3 style={{ 
              color: '#F1F5F9', 
              fontSize: '16px', 
              marginBottom: '20px',
              fontWeight: 500,
            }}>Loss Function L(τ) Across α Values</h3>
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart data={thresholdAnalysisData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <defs>
                  <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                <XAxis 
                  dataKey="threshold" 
                  stroke="#64748B" 
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }}
                  tickFormatter={(v) => `${v} mo`}
                  label={{ value: 'Import Cover Threshold (τ)', position: 'bottom', offset: -5, fill: '#64748B', fontSize: 11 }}
                />
                <YAxis 
                  stroke="#64748B" 
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }}
                  domain={[0, 1]}
                  label={{ value: 'Loss L(τ)', angle: -90, position: 'insideLeft', fill: '#64748B', fontSize: 11 }}
                />
                <Tooltip 
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div style={{
                          background: 'rgba(15, 23, 42, 0.95)',
                          border: '1px solid rgba(148, 163, 184, 0.2)',
                          borderRadius: '8px',
                          padding: '12px 16px',
                          boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
                        }}>
                          <p style={{ color: '#F1F5F9', fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
                            Threshold: {label} months
                          </p>
                          {payload.map((p, i) => (
                            <p key={i} style={{ color: p.color, fontSize: '12px', margin: '4px 0' }}>
                              {p.name}: {p.value.toFixed(3)}
                            </p>
                          ))}
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend 
                  wrapperStyle={{ paddingTop: '20px' }}
                  formatter={(value) => <span style={{ color: '#94A3B8', fontSize: '11px' }}>{value}</span>}
                />
                <ReferenceLine y={0.1} stroke="#10B981" strokeDasharray="5 5" label={{ value: 'Optimal zone', fill: '#10B981', fontSize: 10, position: 'right' }} />
                <Line type="monotone" dataKey="L_0_6" stroke="#F59E0B" strokeWidth={2} dot={{ fill: '#F59E0B', r: 4 }} name="α = 0.6" />
                <Line type="monotone" dataKey="L_0_7" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6', r: 4 }} name="α = 0.7" />
                <Line type="monotone" dataKey="L_0_8" stroke="#8B5CF6" strokeWidth={2} dot={{ fill: '#8B5CF6', r: 4 }} name="α = 0.8" />
                <Line type="monotone" dataKey="L_0_9" stroke="#EF4444" strokeWidth={2} dot={{ fill: '#EF4444', r: 4 }} name="α = 0.9" />
              </ComposedChart>
            </ResponsiveContainer>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '16px',
              marginTop: '24px',
            }}>
              {[
                { alpha: 0.6, optimal: '1.5–2.0 mo', loss: 0.00, color: '#F59E0B', note: 'Balanced precision' },
                { alpha: 0.7, optimal: '1.5–2.0 mo', loss: 0.00, color: '#3B82F6', note: 'Moderate early warning' },
                { alpha: 0.8, optimal: '1.5–2.0 mo', loss: 0.00, color: '#8B5CF6', note: 'Strong early warning' },
                { alpha: 0.9, optimal: '1.5–2.0 mo', loss: 0.00, color: '#EF4444', note: 'Maximum early warning' },
              ].map((item, i) => (
                <div key={i} style={{
                  background: 'rgba(15, 23, 42, 0.5)',
                  borderRadius: '12px',
                  padding: '16px',
                  borderTop: `3px solid ${item.color}`,
                }}>
                  <p style={{ color: item.color, fontSize: '14px', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>
                    α = {item.alpha}
                  </p>
                  <p style={{ color: '#F1F5F9', fontSize: '18px', fontWeight: 600, marginTop: '8px' }}>
                    {item.optimal}
                  </p>
                  <p style={{ color: '#64748B', fontSize: '11px', marginTop: '4px' }}>
                    {item.note}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Threshold Analysis Table */}
          <div style={{
            background: 'rgba(30, 41, 59, 0.5)',
            borderRadius: '16px',
            padding: '24px',
            border: '1px solid rgba(148, 163, 184, 0.1)',
          }}>
            <h3 style={{ 
              color: '#F1F5F9', 
              fontSize: '16px', 
              marginBottom: '20px',
              fontWeight: 500,
            }}>Import Cover Threshold Analysis</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '900px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid rgba(148, 163, 184, 0.2)', background: 'rgba(15, 23, 42, 0.5)' }}>
                    <th style={{ textAlign: 'left', padding: '14px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Threshold (τ)</th>
                    <th style={{ textAlign: 'left', padding: '14px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Lead Time</th>
                    <th style={{ textAlign: 'left', padding: '14px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>False Alarm Months</th>
                    <th style={{ textAlign: 'left', padding: '14px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>False Alarm Rate</th>
                    <th style={{ textAlign: 'center', padding: '14px 16px', color: '#F59E0B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>L(τ) α=0.6</th>
                    <th style={{ textAlign: 'center', padding: '14px 16px', color: '#3B82F6', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>L(τ) α=0.7</th>
                    <th style={{ textAlign: 'center', padding: '14px 16px', color: '#8B5CF6', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>L(τ) α=0.8</th>
                    <th style={{ textAlign: 'center', padding: '14px 16px', color: '#EF4444', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>L(τ) α=0.9</th>
                  </tr>
                </thead>
                <tbody>
                  {thresholdAnalysisData.map((row, i) => {
                    const isOptimal = row.threshold >= 1.5 && row.threshold <= 2.5;
                    const hasLeadTimePenalty = row.leadTime < 6;
                    return (
                      <tr key={i} style={{ 
                        borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                        background: isOptimal ? 'rgba(16, 185, 129, 0.08)' : i % 2 === 0 ? 'transparent' : 'rgba(15, 23, 42, 0.3)',
                      }}>
                        <td style={{ padding: '14px 16px' }}>
                          <span style={{
                            color: isOptimal ? '#10B981' : '#E2E8F0',
                            fontSize: '14px',
                            fontWeight: isOptimal ? 600 : 500,
                            fontFamily: 'JetBrains Mono, monospace',
                          }}>
                            {row.threshold.toFixed(1)} months
                            {isOptimal && <span style={{ marginLeft: '8px', fontSize: '10px' }}>★</span>}
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px' }}>
                          <span style={{
                            color: hasLeadTimePenalty ? '#EF4444' : '#10B981',
                            fontSize: '14px',
                            fontWeight: 500,
                            fontFamily: 'JetBrains Mono, monospace',
                          }}>
                            {row.leadTime} months
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', color: '#F1F5F9', fontSize: '14px', fontFamily: 'JetBrains Mono, monospace' }}>
                          {row.falseAlarmMonths}
                        </td>
                        <td style={{ padding: '14px 16px' }}>
                          <span style={{
                            color: row.falseAlarmRate > 10 ? '#EF4444' : row.falseAlarmRate > 0 ? '#F59E0B' : '#10B981',
                            fontSize: '14px',
                            fontFamily: 'JetBrains Mono, monospace',
                          }}>
                            {row.falseAlarmRate.toFixed(1)}%
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                          <span style={{
                            display: 'inline-block',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 600,
                            fontFamily: 'JetBrains Mono, monospace',
                            background: row.L_0_6 === 0 ? 'rgba(16, 185, 129, 0.15)' : row.L_0_6 < 0.1 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: row.L_0_6 === 0 ? '#10B981' : row.L_0_6 < 0.1 ? '#F59E0B' : '#EF4444',
                          }}>
                            {row.L_0_6.toFixed(3)}
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                          <span style={{
                            display: 'inline-block',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 600,
                            fontFamily: 'JetBrains Mono, monospace',
                            background: row.L_0_7 === 0 ? 'rgba(16, 185, 129, 0.15)' : row.L_0_7 < 0.1 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: row.L_0_7 === 0 ? '#10B981' : row.L_0_7 < 0.1 ? '#F59E0B' : '#EF4444',
                          }}>
                            {row.L_0_7.toFixed(3)}
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                          <span style={{
                            display: 'inline-block',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 600,
                            fontFamily: 'JetBrains Mono, monospace',
                            background: row.L_0_8 === 0 ? 'rgba(16, 185, 129, 0.15)' : row.L_0_8 < 0.1 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: row.L_0_8 === 0 ? '#10B981' : row.L_0_8 < 0.1 ? '#F59E0B' : '#EF4444',
                          }}>
                            {row.L_0_8.toFixed(3)}
                          </span>
                        </td>
                        <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                          <span style={{
                            display: 'inline-block',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 600,
                            fontFamily: 'JetBrains Mono, monospace',
                            background: row.L_0_9 === 0 ? 'rgba(16, 185, 129, 0.15)' : row.L_0_9 < 0.1 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: row.L_0_9 === 0 ? '#10B981' : row.L_0_9 < 0.1 ? '#F59E0B' : '#EF4444',
                          }}>
                            {row.L_0_9.toFixed(3)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p style={{ fontSize: '11px', color: '#64748B', marginTop: '16px', fontStyle: 'italic' }}>
              Note: Non-crisis period defined as Nov 2013 – Dec 2016 and Jan 2018 – Dec 2019 (72 months total). 
              Lead time measured from first breach to default date (April 2022). ★ indicates optimal thresholds with zero loss.
            </p>
          </div>

          {/* Key Insights */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
            borderRadius: '16px',
            padding: '24px',
            marginTop: '24px',
            border: '1px solid rgba(16, 185, 129, 0.2)',
          }}>
            <h4 style={{ color: '#10B981', fontSize: '14px', fontWeight: 600, marginBottom: '16px' }}>
              Key Finding: Optimal Threshold Range
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '24px' }}>
              <div>
                <p style={{ color: '#F1F5F9', fontSize: '24px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                  1.5 – 2.5 months
                </p>
                <p style={{ color: '#94A3B8', fontSize: '12px', marginTop: '4px' }}>
                  Achieves L(τ) = 0 for all α values
                </p>
              </div>
              <div>
                <p style={{ color: '#F1F5F9', fontSize: '24px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                  0% false alarms
                </p>
                <p style={{ color: '#94A3B8', fontSize: '12px', marginTop: '4px' }}>
                  Perfect precision in historical data
                </p>
              </div>
              <div>
                <p style={{ color: '#F1F5F9', fontSize: '24px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                  7–12 months
                </p>
                <p style={{ color: '#94A3B8', fontSize: '12px', marginTop: '4px' }}>
                  Sufficient lead time for intervention
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* Recommended Framework */}
        <Section title="Proposed Early Warning Framework" id="framework">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
            {[
              { 
                level: 'Yellow Alert', 
                criteria: 'Import Cover < 3 months OR ARA < 150%',
                color: '#F59E0B',
                action: 'Heightened monitoring, policy review',
              },
              { 
                level: 'Orange Alert', 
                criteria: 'Import Cover < 2 months OR ARA < 100% OR GG < 1.5',
                color: '#F97316',
                action: 'Preemptive IMF engagement, debt management',
              },
              { 
                level: 'Red Alert', 
                criteria: 'Import Cover < 1 month AND ARA < 80%',
                color: '#EF4444',
                action: 'Emergency measures, restructuring initiation',
              },
            ].map((alert, i) => (
              <div key={i} style={{
                background: 'rgba(30, 41, 59, 0.5)',
                borderRadius: '16px',
                padding: '24px',
                border: `1px solid ${alert.color}33`,
                borderTop: `4px solid ${alert.color}`,
              }}>
                <div style={{
                  display: 'inline-block',
                  background: `${alert.color}22`,
                  color: alert.color,
                  padding: '4px 12px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  marginBottom: '16px',
                }}>
                  {alert.level}
                </div>
                <p style={{ color: '#E2E8F0', fontSize: '14px', marginBottom: '16px', lineHeight: 1.5 }}>
                  {alert.criteria}
                </p>
                <p style={{ color: '#64748B', fontSize: '13px' }}>
                  <strong style={{ color: '#94A3B8' }}>Action:</strong> {alert.action}
                </p>
              </div>
            ))}
          </div>

          {/* Benchmark Ranking Table */}
          <div style={{
            background: 'rgba(30, 41, 59, 0.5)',
            borderRadius: '16px',
            padding: '24px',
            border: '1px solid rgba(148, 163, 184, 0.1)',
            marginTop: '24px',
          }}>
            <h3 style={{ 
              color: '#F1F5F9', 
              fontSize: '16px', 
              marginBottom: '20px',
              fontWeight: 500,
            }}>Benchmark Effectiveness Ranking</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(148, 163, 184, 0.2)' }}>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Rank</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Benchmark</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Lead Time</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Specificity</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: '#64748B', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { rank: 1, bench: 'Import Cover < 2 mo', lead: '9 months', spec: 'High', rec: 'Primary early warning', color: '#10B981' },
                  { rank: 2, bench: 'IMF ARA < 100%', lead: '6 months', spec: 'High', rec: 'Comprehensive metric', color: '#3B82F6' },
                  { rank: 3, bench: 'GG Ratio < 1.5', lead: '6 months', spec: 'Medium', rec: 'Debt-focused warning', color: '#8B5CF6' },
                  { rank: 4, bench: 'Import Cover < 1 mo', lead: '5 months', spec: 'Very High', rec: 'Imminent crisis', color: '#EF4444' },
                  { rank: 5, bench: 'Import Cover < 3 mo', lead: '62 months', spec: 'Low', rec: 'Background indicator', color: '#64748B' },
                ].map((row, i) => (
                  <tr key={i} style={{ 
                    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                    background: i % 2 === 0 ? 'transparent' : 'rgba(15, 23, 42, 0.3)',
                  }}>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        background: row.color,
                        color: '#fff',
                        fontSize: '12px',
                        fontWeight: 600,
                      }}>{row.rank}</span>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#E2E8F0', fontSize: '14px', fontWeight: 500 }}>{row.bench}</td>
                    <td style={{ padding: '14px 16px', color: '#F1F5F9', fontSize: '14px', fontFamily: 'JetBrains Mono, monospace' }}>{row.lead}</td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 500,
                        background: row.spec === 'Very High' ? 'rgba(16, 185, 129, 0.15)' : row.spec === 'High' ? 'rgba(59, 130, 246, 0.15)' : row.spec === 'Medium' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(100, 116, 139, 0.15)',
                        color: row.spec === 'Very High' ? '#10B981' : row.spec === 'High' ? '#3B82F6' : row.spec === 'Medium' ? '#F59E0B' : '#64748B',
                      }}>{row.spec}</span>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#94A3B8', fontSize: '13px' }}>{row.rec}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        {/* Footer */}
        <footer style={{
          textAlign: 'center',
          paddingTop: '48px',
          borderTop: '1px solid rgba(148, 163, 184, 0.1)',
          marginTop: '48px',
        }}>
          <p style={{ color: '#64748B', fontSize: '12px' }}>
            University of Colombo · Data Analytics & Visualization Lab
          </p>
          <p style={{ color: '#475569', fontSize: '11px', marginTop: '8px' }}>
            Data: CBSL Historical Series · Nov 2013 – Nov 2025
          </p>
        </footer>
      </main>
    </div>
  );
}
