import { Channel, SignalMessage } from '../types'

// SYNTHETIC DEMO DATA. All channels, authors and messages below are entirely
// fictional and generated for demonstration purposes only. SignalWatch does
// not connect to any real private messaging platform.

export const channels: Channel[] = [
  { id: 'chan-01', name: 'Forest Logistics', memberCount: 14, lastActivity: '21 min ago' },
  { id: 'chan-02', name: 'Transit Group', memberCount: 9, lastActivity: '1 hr ago' },
  { id: 'chan-03', name: 'Wild Goods', memberCount: 22, lastActivity: '3 hr ago' },
  { id: 'chan-04', name: 'Transport Network', memberCount: 11, lastActivity: '6 hr ago' },
]

export const messages: SignalMessage[] = [
  {
    id: 'msg-01',
    channelId: 'chan-01',
    author: 'Synthetic User A1',
    timestamp: '2026-03-19T21:02:00Z',
    text: 'Brown parcels can move after the rain.',
    flaggedTerms: [{ term: 'brown parcels', confidence: 61 }],
  },
  {
    id: 'msg-02',
    channelId: 'chan-01',
    author: 'Synthetic User A2',
    timestamp: '2026-03-19T21:05:00Z',
    text: 'Same route as last time, blue bird confirmed.',
    flaggedTerms: [{ term: 'blue bird', confidence: 68 }],
    locationMention: { locationId: 'loc-03', label: 'Northern Crossing' },
  },
  {
    id: 'msg-03',
    channelId: 'chan-01',
    author: 'Synthetic User A1',
    timestamp: '2026-03-19T21:07:00Z',
    text: 'Meet near the northern crossing after midnight.',
    flaggedTerms: [{ term: 'northern crossing', confidence: 74 }],
    locationMention: { locationId: 'loc-03', label: 'Northern Crossing' },
  },
  {
    id: 'msg-04',
    channelId: 'chan-02',
    author: 'Synthetic User B3',
    timestamp: '2026-03-18T15:40:00Z',
    text: 'Weight looks light this cycle, buyer already asking.',
    flaggedTerms: [{ term: 'weight looks light', confidence: 41 }],
  },
  {
    id: 'msg-05',
    channelId: 'chan-02',
    author: 'Synthetic User B1',
    timestamp: '2026-03-18T15:44:00Z',
    text: 'Corridor checkpoint moved, use the Mae Sot side instead.',
    flaggedTerms: [{ term: 'checkpoint moved', confidence: 58 }],
    locationMention: { locationId: 'loc-06', label: 'Mae Sot Corridor' },
  },
  {
    id: 'msg-06',
    channelId: 'chan-03',
    author: 'Synthetic User C4',
    timestamp: '2026-03-17T10:12:00Z',
    text: 'New listing up, ask for details privately.',
    flaggedTerms: [{ term: 'ask for details privately', confidence: 36 }],
  },
  {
    id: 'msg-07',
    channelId: 'chan-03',
    author: 'Synthetic User C2',
    timestamp: '2026-03-17T10:20:00Z',
    text: 'Depot count was off again this week.',
    flaggedTerms: [{ term: 'depot count was off', confidence: 44 }],
    locationMention: { locationId: 'loc-08', label: 'Kunming Depot' },
  },
  {
    id: 'msg-08',
    channelId: 'chan-04',
    author: 'Synthetic User D1',
    timestamp: '2026-03-15T08:05:00Z',
    text: 'Documents ready, forwarder confirmed on the usual terminal.',
    flaggedTerms: [{ term: 'forwarder confirmed', confidence: 39 }],
    locationMention: { locationId: 'loc-10', label: 'Entebbe Cargo Hub' },
  },
  {
    id: 'msg-09',
    channelId: 'chan-04',
    author: 'Synthetic User D2',
    timestamp: '2026-03-15T08:11:00Z',
    text: 'Tusks packed under the usual cover load.',
    flaggedTerms: [{ term: 'tusks', confidence: 71 }, { term: 'cover load', confidence: 52 }],
  },
  {
    id: 'msg-10',
    channelId: 'chan-02',
    author: 'Synthetic User B3',
    timestamp: '2026-03-18T15:52:00Z',
    text: 'Second load queued, same buyer as February.',
    flaggedTerms: [{ term: 'second load queued', confidence: 33 }],
  },
]

export const messagesByChannel = (channelId: string) =>
  messages.filter((m) => m.channelId === channelId)
