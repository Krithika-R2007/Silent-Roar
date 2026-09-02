import { riskBarColor, riskTone, cx } from '../../utils/format'

export function RiskBar({ score, label }: { score: number; label?: string }) {
  return (
    <div className="w-full">
      {label && (
        <div className="mb-1 flex items-center justify-between">
          <span className="text-micro text-ink-500">{label}</span>
          <span className={cx('text-micro font-semibold', riskTone(score))}>{score}</span>
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-base-700">
        <div
          className={cx('h-full rounded-full transition-all duration-700', riskBarColor(score))}
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
    </div>
  )
}

export function RiskDial({ score, size = 64 }: { score: number; size?: number }) {
  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.min(100, score) / 100) * circumference
  const strokeColor =
    score >= 80 ? '#C4433D' : score >= 60 ? '#D19A3E' : score >= 40 ? '#3E9AB0' : '#149447'

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#E1E7E4" strokeWidth={5} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={5}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span
          className="font-bold leading-none tabular-nums"
          style={{
            color: strokeColor,
            fontSize: (() => {
              const digits = String(Math.round(score)).length
              const base = size * 0.28
              // shrink for more digits or smaller circles
              const scaled = digits >= 3 ? base * 0.72 : digits === 2 ? base * 0.88 : base
              return `${Math.max(9, scaled)}px`
            })(),
          }}
        >
          {score}
        </span>
      </div>
    </div>
  )
}
