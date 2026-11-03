import React, { useState } from 'react'
import {
  BotMessageSquare,
  Send,
  Sparkles,
  ChevronDown,
  ChevronUp,
  User,
  Activity,
  Layers
} from 'lucide-react'
import type { VillageMeta, PredictDemandResponse } from '../types'
import { api } from '../services/api'
import { formatLitres } from '../utils/formatters'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sourceLabel?: string
  isFallback?: boolean
  timestamp: string
}

interface AIAssistantPageProps {
  selectedVillage?: VillageMeta
  prediction?: PredictDemandResponse
}

export const AIAssistantPage: React.FC<AIAssistantPageProps> = ({
  selectedVillage,
  prediction
}) => {
  const villageName = selectedVillage?.name || 'Selected Village'
  const villageId = selectedVillage?.id || 'VILL001'

  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `Hello! I am your JalSense Hydrological Decision Assistant for **${villageName}**.\n\n` +
        (prediction
          ? `Tomorrow's predicted demand is **${formatLitres(prediction.water_balance.predicted_demand_litres)}** with a **${prediction.water_balance.risk_category}** shortage risk category. `
          : '') +
        `Ask me any analytical question regarding water demand forecasts, shortage risks, weather stresses, or scenario responses.`,
      sourceLabel: 'System Initialization',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ])

  const [inputVal, setInputVal] = useState<string>('')
  const [isSending, setIsSending] = useState<boolean>(false)
  const [showGrounding, setShowGrounding] = useState<boolean>(false)

  const quickQuestions = [
    'Will there be a shortage tomorrow?',
    'Why is the current shortage risk high?',
    'What is tomorrow\'s predicted demand?',
    'What happens if rainfall increases?',
    'Summarize today\'s water situation.'
  ]

  const handleSend = async (qText?: string) => {
    const question = (qText || inputVal).trim()
    if (!question || isSending) return

    const userMsg: Message = {
      role: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages((prev) => [...prev, userMsg])
    setInputVal('')
    setIsSending(true)

    try {
      const resp = await api.queryAssistant({
        question,
        village_id: villageId,
        mode: 'auto'
      })

      const botMsg: Message = {
        role: 'assistant',
        content: resp.answer,
        sourceLabel: resp.source_label,
        isFallback: resp.is_fallback,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      setMessages((prev) => [...prev, botMsg])
    } catch (err: any) {
      const errorMsg: Message = {
        role: 'assistant',
        content: `Apologies, I encountered an error communicating with the assistant service: ${err.message || 'Service unavailable'}. Please verify backend status.`,
        sourceLabel: 'System Error',
        isFallback: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="space-y-4 pb-8 max-w-5xl mx-auto">
      {/* Top Header Card */}
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-lg bg-blue-50 text-[#0B78B5] shrink-0">
              <BotMessageSquare className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-[#0B78B5] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  AI Hydrological Assistant
                </span>
                <span className="text-xs text-[#64748B]">• Factual Decision Support</span>
              </div>
              <h2 className="text-xl font-extrabold text-[#16324F] mt-0.5">
                JalSense Analytical Assistant
              </h2>
              <p className="text-xs text-[#64748B] max-w-2xl leading-relaxed">
                Natural-language explanations grounded strictly in computed model metrics and Open-Meteo telemetry. Powered by configured LLM with local deterministic hydrological fallback.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1.5 shrink-0">
              <span className="w-2 h-2 rounded-full bg-emerald-600" />
              Zero Hallucination Grounding
            </span>
          </div>
        </div>
      </div>

      {/* Quick Questions Chips */}
      <div>
        <div className="text-[11px] font-bold uppercase tracking-wider text-[#64748B] mb-2 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-[#0B78B5]" />
          Quick Inquiries
        </div>
        <div className="flex flex-wrap gap-2">
          {quickQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => handleSend(q)}
              disabled={isSending}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-white border border-[#CBD5E1] text-[#16324F] hover:border-[#0B78B5] hover:text-[#0B78B5] hover:bg-[#F5F8FC] transition-all disabled:opacity-50 text-left cursor-pointer shadow-2xs"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Panel */}
      <div className="card-base p-4 sm:p-5 min-h-[400px] flex flex-col justify-between">
        <div className="space-y-4 overflow-y-auto max-h-[520px] pr-1">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-[#0B78B5] text-white flex items-center justify-center shrink-0 shadow-2xs text-xs font-bold">
                  💧
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-xl p-3.5 text-xs sm:text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-[#0B78B5] text-white rounded-tr-none'
                    : 'bg-[#F8FAFC] text-[#16324F] border border-[#E2E8F0] rounded-tl-none'
                }`}
              >
                {m.role === 'assistant' && m.sourceLabel && (
                  <div className="flex items-center justify-between gap-3 pb-1.5 mb-2 border-b border-slate-200/60 text-[10px]">
                    <span className="font-bold text-[#0B78B5] bg-white px-2 py-0.5 rounded border border-blue-200">
                      {m.sourceLabel}
                    </span>
                    <span className="text-[#94A3B8] font-mono">{m.timestamp}</span>
                  </div>
                )}

                <div className="whitespace-pre-wrap font-normal">
                  {m.content}
                </div>

                {m.role === 'user' && (
                  <div className="text-[10px] text-blue-100 text-right mt-1 font-mono">
                    {m.timestamp}
                  </div>
                )}
              </div>

              {m.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-[#16324F] text-white flex items-center justify-center shrink-0 shadow-2xs text-xs">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {isSending && (
            <div className="flex items-center gap-2 text-xs text-[#64748B] pl-11">
              <Activity className="w-4 h-4 animate-spin text-[#0B78B5]" />
              <span>Analyzing telemetry context and generating grounded response...</span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSend()
          }}
          className="mt-4 pt-3 border-t border-[#F1F5F9] flex items-center gap-2"
        >
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder={`Ask a question about ${villageName}'s water demand or shortage risk...`}
            disabled={isSending}
            className="flex-1 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl px-4 py-2.5 text-xs sm:text-sm text-[#16324F] focus:outline-none focus:border-[#0B78B5] focus:bg-white transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isSending || !inputVal.trim()}
            className="px-4 py-2.5 rounded-xl bg-[#0B78B5] hover:bg-[#09669B] active:bg-[#075683] text-white font-bold text-xs flex items-center gap-1.5 transition-all disabled:opacity-40 cursor-pointer shadow-xs shrink-0"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
      </div>

      {/* Collapsible Grounding Data Inspector */}
      {prediction && (
        <div className="card-base p-4">
          <button
            onClick={() => setShowGrounding(!showGrounding)}
            className="w-full flex items-center justify-between text-xs font-bold text-[#64748B] hover:text-[#16324F] transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-[#0B78B5]" />
              View Grounding Situation Context (Zero-Hallucination Telemetry)
            </span>
            {showGrounding ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showGrounding && (
            <div className="mt-3 pt-3 border-t border-[#F1F5F9] font-mono text-[11px] text-[#16324F] bg-[#F8FAFC] p-3 rounded-lg overflow-x-auto">
              <pre>{JSON.stringify(
                {
                  village_id: prediction.village_id,
                  village_name: prediction.village_name,
                  forecast_date: prediction.forecast_date,
                  predicted_demand_litres: prediction.predicted_demand_litres,
                  predicted_lpcd: prediction.predicted_lpcd,
                  estimated_supply_litres: prediction.estimated_supply_litres,
                  deficit_litres: prediction.deficit_litres,
                  surplus_litres: prediction.surplus_litres,
                  shortage_risk: prediction.shortage_risk,
                  shortage_probability_pct: prediction.water_balance.shortage_probability_pct,
                  tankers_needed: prediction.water_balance.tankers_needed,
                  weather: prediction.weather
                },
                null,
                2
              )}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
