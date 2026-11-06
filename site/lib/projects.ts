export type Project = {
  name: string;
  code: string;
  role: string;
  description: string;
  highlight: string;
  stack: string[];
  repository: string | null;
  live: string;
};

export const projects: Project[] = [
  {
    name: 'DEVCON Kids Hub 2.0', code: 'DK', role: 'Team lead · Backend developer',
    description: 'A centralized operations platform for volunteer management, approvals, reporting, and AI-assisted knowledge retrieval.',
    highlight: 'Traceable operational handoffs with a retrieval layer for organizational knowledge.',
    stack: ['Next.js', 'TypeScript', 'Supabase', 'RAG'], repository: 'https://github.com/Debb1ie/DEVCON-Kids-Hub-2.0', live: 'https://devcon-kids-hub-2-0.vercel.app/'
  },
  {
    name: 'C.A.G.E.', code: 'CG', role: 'AI security framework',
    description: 'Causal Authorization and Governance Engine for AI agents, policy enforcement, and MCP security testing.',
    highlight: 'Inspectable agent actions through explicit authorization decisions and governance controls.',
    stack: ['AI security', 'MCP', 'Policy', 'Authorization'], repository: null, live: 'https://cage-agent-security.vercel.app/'
  },
  {
    name: 'Bulldogs Xchange', code: 'BX', role: 'Full-stack developer',
    description: 'A campus marketplace with reservations, inventory management, authentication, admin workflows, and AI assistance.',
    highlight: 'Inventory state, reservation rules, and role-aware operations in one campus workflow.',
    stack: ['React', 'Supabase', 'PostgreSQL', 'AI'], repository: 'https://github.com/sinagdevv/bulldogs-xchange', live: 'https://bulldogs-xchange-live-demo.vercel.app/'
  },
  {
    name: 'MAT-AH', code: 'MA', role: 'Local-first systems work',
    description: 'An AI-powered file intelligence and knowledge retrieval system designed around local-first workflows.',
    highlight: 'Useful retrieval without making a remote service the default boundary for personal files.',
    stack: ['Python', 'Embeddings', 'RAG', 'Local-first'], repository: 'https://github.com/Gabi-comm/MAT-AH', live: 'https://mat-ah-showcase.vercel.app/'
  },
  {
    name: 'TripWise', code: 'TW', role: 'Decision-support systems',
    description: 'Fishermen safety and economic decision support with weather intelligence, risk assessment, and interactive maps.',
    highlight: 'Environmental signals shaped into a practical planning surface for field decisions.',
    stack: ['Maps', 'Weather data', 'Risk', 'React'], repository: 'https://github.com/Alvin187187/TripWise', live: 'https://tripwise-sooty.vercel.app/'
  },
  {
    name: 'Mantika Check', code: 'MC', role: 'Explainable ML product',
    description: 'Cooking-oil quality monitoring using explainable decision logic and mathematical degradation models.',
    highlight: 'An understandable decision surface that exposes the signals behind a quality assessment.',
    stack: ['React', 'Decision logic', 'Computer vision', 'PWA'], repository: 'https://github.com/Gabi-comm/mantika-check', live: 'https://mantika-check.vercel.app/'
  }
];
