export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role_name: string;
  is_active: boolean;
}

export interface KPICard {
  id: string;
  name: string;
  value: number;
  previous_value: number;
  change_percent: number | null;
  has_prior?: boolean;
  priority: string;
  status: string;
  trend: number[];
}

export interface Driver {
  id?: number;
  name: string;
  type?: string;
  contribution_percent: number;
  confidence: number;
  evidence_summary?: string;
  supporting_data: Record<string, unknown>;
  rank?: number;
  is_primary?: boolean;
  data_source?: string;
  change_percent?: number;
}

export interface Evidence {
  source: string;
  metric: string;
  metric_value?: number;
  previous_value?: number;
  change_percent?: number;
  analytical_method?: string;
  data_lineage?: Record<string, unknown>;
  timestamp?: string;
}

export interface Recommendation {
  id?: number;
  driver_name?: string;
  lever?: string;
  action: string;
  expected_impact?: string;
  expected_impact_value?: number;
  owner?: string;
  confidence: number;
  monitoring_plan?: string;
  priority?: string;
  status?: string;
  kpi_name?: string;
}

export interface Insight {
  kpi_name: string;
  kpi_description?: string;
  current_value: number;
  previous_value: number;
  change_percent: number | null;
  materiality: {
    priority: string;
    total_score: number;
    is_material: boolean;
  };
  anomaly: Record<string, unknown>;
  drivers: Driver[];
  total_drivers: number;
  explained_percent: number;
  evidence: Evidence[];
  confidence: {
    confidence_score: number;
    confidence_level: string;
    components: Record<string, number>;
    data_sources_missing?: string[];
  };
  abstention: {
    should_abstain: boolean;
    reasons: string[];
    suggested_actions: (string | null)[];
  };
  contradictions: {
    has_contradictions: boolean;
    contradictions: Array<Record<string, unknown>>;
    alternative_hypotheses: Array<Record<string, unknown>>;
  };
  recommendations: Recommendation[];
  narrative: string;
  persona: string;
  data_sources: string[];
  product_breakdown?: Array<Record<string, unknown>>;
  region_breakdown?: Array<Record<string, unknown>>;
  trend?: Array<{ date: string; value: number }>;
}

export interface DataSourceInfo {
  id: number;
  name: string;
  source_type: string;
  status: string;
  last_updated: string | null;
  refresh_frequency: string | null;
  row_count: number;
  data_quality_score: number;
  coverage_days: number;
  description: string | null;
}

export interface LineageNode {
  id: number;
  source_system: string;
  source_table: string | null;
  transformation: string | null;
  target_kpi: string | null;
  description: string | null;
}

export interface TelemetryData {
  average_latency_ms: number;
  total_llm_calls: number;
  total_tokens: number;
  estimated_cost: number;
  success_rate: number;
  cache_hits: number;
  failed_requests: number;
}

export interface AssistantMessage {
  response: string;
  evidence_used: Array<{ source: string; metric: string; change: number }>;
  confidence: number;
  data_sources_consulted: string[];
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
}

export interface FeedbackDashboard {
  total_feedback: number;
  positive_count: number;
  negative_count: number;
  positive_rate: number;
  most_common_correction: string | null;
  feedback_trend: Array<Record<string, unknown>>;
}

export interface LineageEdge {
  source: number;
  target: number;
}

export interface Lineage {
  nodes: Array<{ id: number; type: string; name: string }>;
  edges: LineageEdge[];
}

export interface UploadedTable {
  table_name: string;
  row_count: number;
  column_count: number;
  columns: Array<{ name: string; type: string }>;
  is_uploaded: boolean;
}

export interface FilePreview {
  filename: string;
  file_type: string;
  total_rows: number;
  total_columns: number;
  columns: Array<{
    name: string;
    sqlite_type: string;
    pandas_dtype: string;
    non_null_count: number;
    null_count: number;
    total_count: number;
    unique_count: number;
    sample_values: string[];
    min?: number;
    max?: number;
    mean?: number;
  }>;
  preview: Array<Record<string, unknown>>;
  row_count: number;
}

export interface UploadResult {
  success: boolean;
  table_name: string;
  rows_inserted: number;
  total_rows_in_table: number;
  columns: Array<{
    name: string;
    sqlite_type: string;
    non_null_count: number;
    null_count: number;
    total_count: number;
    unique_count: number;
    sample_values: string[];
  }>;
  filename: string;
}

export interface ColumnMapping {
  uploaded_column: string;
  target_field: string;
  confidence: number;
}

export interface AutoDetectResult {
  table_name: string;
  detected_type: string;
  confidence: number;
  field_mappings: Record<string, ColumnMapping>;
  missing_fields: string[];
  unmapped_columns: string[];
  all_columns: string[];
  row_count?: number;
  filename?: string;
}

export interface DataMapping {
  table_name: string;
  mapped_type: string;
  column_mapping: Record<string, string>;
  is_active: boolean;
}
