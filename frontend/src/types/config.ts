/**
 * Configuration type definitions for AgentSociety
 * These types match the backend configuration structures
 */

import { LLMProviderType, WorkflowType, MetricType, DistributionType } from '../utils/enums';

// LLM Configuration
export interface LLMConfig {
  provider: LLMProviderType;
  base_url?: string;
  api_key: string;
  model: string;
}

// Map Configuration
export interface MapConfig {
  file_path: string;
  cache_path?: string;
}

// Agent Configuration
export interface DistributionConfig {
  dist_type: DistributionType;
  choices?: string[];
  weights?: number[];
  min_value?: number;
  max_value?: number;
  mean?: number;
  std?: number;
  value?: any;
}

export interface MemoryConfig {
  memory_config_func?: string;
  memory_from_file?: string;
  memory_distributions?: Record<string, DistributionConfig>;
}

export interface AgentConfig {
  agent_class: string;
  number: number;
  agent_config?: Record<string, any>;
  memory_config_func?: string;
  memory_from_file?: string;
  memory_distributions?: Record<string, DistributionConfig>;
}

export interface AgentsConfig {
  citizens: AgentConfig[];
  firms?: AgentConfig[];
  banks?: AgentConfig[];
  nbs?: AgentConfig[];
  governments?: AgentConfig[];
  init_funcs?: string[];
}

// Experiment Configuration
export interface EnvironmentConfig {
  weather?: string;
  temperature?: string;
  workday?: boolean;
  other_information?: string;
  start_tick?: number;
  total_tick?: number;
}

export interface MessageInterceptConfig {
  mode?: 'point' | 'edge';
  max_violation_time: number;
  blocks?: string[];
  listener?: string;
}

export interface WorkflowStepConfig {
  type: WorkflowType;
  func?: string;
  steps?: number;
  ticks_per_step?: number;
  target_agent?: number[];
  interview_message?: string;
  survey?: any;
  key?: string;
  value?: any;
  intervene_message?: string;
  description?: string;
}

export interface MetricExtractorConfig {
  type: MetricType;
  func?: string;
  step_interval?: number;
  target_agent?: number[];
  key?: string;
  method?: 'mean' | 'sum' | 'max' | 'min';
  extract_time?: number;
  description?: string;
}

export interface ExpConfig {
  name: string;
  id?: string;
  workflow: WorkflowStepConfig[];
  environment: EnvironmentConfig;
  message_intercept?: MessageInterceptConfig;
  metric_extractors?: MetricExtractorConfig[];
}

// Root Configuration
export interface Config {
  llm: LLMConfig[];
  map: MapConfig;
  agents: AgentsConfig;
  exp: ExpConfig;
} 