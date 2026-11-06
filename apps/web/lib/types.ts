export type Org = { id: string; name: string; role: string };

export type User = {
  id: string;
  name: string;
  email: string;
  verified: boolean;
};

export type Me = { user: User; csrf: string; organizations: Org[] };

export type Doc = {
  id: string;
  name: string;
  status: string;
  size: number;
  created_at: string;
  chunks: number;
  visibility: string;
  workspace_id: string | null;
  error: string | null;
  attempts: number;
  passages?: Source[];
};

export type Workspace = { id: string; name: string; description: string };

export type Source = {
  id: string;
  document_id?: string;
  name?: string;
  text: string;
  page: number | null;
  ordinal: number;
  number?: number;
};

export type Msg = {
  id?: string;
  role: string;
  content: string;
  citations: Source[];
};

export type Conv = { id: string; title: string; created_at: string };

export type Stat = {
  documents: number;
  ready: number;
  failed: number;
  processing: number;
  chunks: number;
  storage_bytes: number;
  conversations: number;
  provider_configured: boolean;
  retrieval: string;
};

export type Member = { id: string; name: string; email: string; role: string };

export type Audit = {
  id: string;
  action: string;
  detail: string;
  created_at: string;
};
