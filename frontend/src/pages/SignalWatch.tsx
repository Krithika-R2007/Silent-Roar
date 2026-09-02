import { useEffect, useState } from 'react'
import { ShieldAlert } from 'lucide-react'
import { Channel, SignalMessage } from '../types'
import { apiClient } from '../services/apiClient'
import { LoadingState } from '../components/ui/States'
import { ChannelList } from '../components/signalwatch/ChannelList'
import { ConversationWindow } from '../components/signalwatch/ConversationWindow'
import { LinguisticAnalysisPanel } from '../components/signalwatch/LinguisticAnalysisPanel'

export default function SignalWatch() {
  const [channels, setChannels] = useState<Channel[] | null>(null)
  const [activeChannelId, setActiveChannelId] = useState<string | null>(null)
  const [messages, setMessages] = useState<SignalMessage[]>([])
  const [selected, setSelected] = useState<SignalMessage | null>(null)

  useEffect(() => {
    apiClient.getChannels().then((data) => {
      setChannels(data)
      setActiveChannelId(data[0]?.id ?? null)
    })
  }, [])

  useEffect(() => {
    if (!activeChannelId) return
    apiClient.getMessages(activeChannelId).then((data) => {
      setMessages(data)
      setSelected(null)
    })
  }, [activeChannelId])

  function handleAddToInvestigation(message: SignalMessage) {
    setMessages((prev) => prev.map((m) => (m.id === message.id ? { ...m, addedToInvestigation: true } : m)))
    setSelected((prev) => (prev && prev.id === message.id ? { ...prev, addedToInvestigation: true } : prev))
    sessionStorage.setItem('boosted:inv-01', 'true')
  }

  if (!channels) return <LoadingState />

  return (
    <div className="mx-auto flex h-[calc(100vh-64px)] max-w-[1400px] flex-col gap-4 p-6">
      <div className="flex items-center gap-2 rounded-md border border-amber-500/25 bg-amber-500/5 px-3.5 py-2.5 font-ui text-[12.5px] text-amber-600">
        <ShieldAlert className="h-4 w-4 shrink-0" />
        This is a simulated demonstration environment. SignalWatch does not connect to real private messaging platforms — every message shown is synthetic.
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[220px_1fr_320px]">
        <ChannelList channels={channels} activeId={activeChannelId} onSelect={setActiveChannelId} />
        <ConversationWindow messages={messages} selectedId={selected?.id ?? null} onSelect={setSelected} />
        <LinguisticAnalysisPanel message={selected} onAddToInvestigation={handleAddToInvestigation} />
      </div>
    </div>
  )
}
