import React from 'react'

interface KpiCardProps {
  label: string
  sublabel?: string
  value: string | number
  unit?: string
  contextText: string
  badgeText?: string
  badgeVariant?: 'safe' | 'warning' | 'danger' | 'info' | 'neutral'
  valueColorClass?: string
  icon?: React.ElementType
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  sublabel,
  value,
  unit,
  contextText,
  badgeText,
  badgeVariant = 'neutral',
  valueColorClass = 'text-[#16324F]',
  icon: Icon
}) => {
  const badgeClasses = {
    safe: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    warning: 'bg-amber-50 text-amber-800 border-amber-200',
    danger: 'bg-red-50 text-red-800 border-red-200',
    info: 'bg-blue-50 text-[#0B78B5] border-blue-200',
    neutral: 'bg-slate-100 text-[#64748B] border-slate-200'
  }[badgeVariant]

  return (
    <div className="card-base card-hover p-4 flex flex-col justify-between h-full">
      {/* Top Header */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 truncate">
          {Icon && <Icon className="w-3.5 h-3.5 text-[#64748B] shrink-0" />}
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B] truncate">
            {label}
          </span>
        </div>
        {badgeText && (
          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border shrink-0 ${badgeClasses}`}>
            {badgeText}
          </span>
        )}
      </div>

      {/* Main Metric Value */}
      <div className="my-1">
        <div className="flex items-baseline gap-1.5 flex-wrap">
          <span className={`text-2xl sm:text-[1.75rem] font-extrabold font-mono tracking-tight leading-none ${valueColorClass}`}>
            {value}
          </span>
          {unit && <span className="text-xs font-bold text-[#64748B] uppercase">{unit}</span>}
        </div>
        {sublabel && <div className="text-[11px] text-[#64748B] font-medium mt-1">{sublabel}</div>}
      </div>

      {/* Footer Subtitle */}
      <div className="pt-2 border-t border-[#F1F5F9] mt-2 flex items-center justify-between text-[11px] text-[#64748B]">
        <span className="truncate">{contextText}</span>
      </div>
    </div>
  )
}
