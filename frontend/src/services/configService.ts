/**
 * Service for handling configuration operations
 */

import { LLMConfig, AgentConfig, AgentsConfig, MapConfig, ExpConfig, Config } from '../types/config';
import storageService, { STORAGE_KEYS, ConfigItem } from './storageService';

class ConfigService {
  /**
   * Builds a complete experiment configuration from selected components
   * following the format in config.json
   */
  async buildExperimentConfig(
    llmId: string,
    agentId: string,
    workflowId: string,
    mapId: string,
    experimentName: string
  ): Promise<Config | null> {
    try {
      // Load all required configurations
      const llms = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.LLMS);
      const agents = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.AGENTS);
      const workflows = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.WORKFLOWS);
      const maps = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.MAPS);
      
      // Find selected configurations
      const llm = llms.find(l => l.id === llmId);
      const agent = agents.find(a => a.id === agentId);
      const workflow = workflows.find(w => w.id === workflowId);
      const map = maps.find(m => m.id === mapId);
      
      if (!llm || !agent || !workflow || !map) {
        console.error('One or more required configurations not found');
        return null;
      }
      
      // Process agent configuration
      let config: Config = {
        llm: [],
        map: {
          file_path: typeof map.config.file_path === 'string' ? map.config.file_path : "maps/default.pb",
          cache_path: typeof map.config.cache_path === 'string' ? map.config.cache_path : null
        },
        agents: {
          citizens: [],
          firms: [],
          governments: [],
          banks: [],
          nbs: [],
          init_funcs: []
        },
        exp: {
          name: experimentName || workflow.name,
          workflow: Array.isArray(workflow.config.workflow) ? workflow.config.workflow : [
            {
              func: null,
              type: "step",
              times: 10
            }
          ],
          environment: workflow.config.environment || {
            start_tick: 28800,
            total_tick: 7200
          },
          message_intercept: workflow.config.message_intercept && 
            typeof workflow.config.message_intercept === 'object' ? 
              {
                listener: null,
                mode: "point",
                max_violation_time: 100,
                ...(workflow.config.message_intercept as Record<string, any>)
              } : 
              {
                listener: null,
                mode: "point",
                max_violation_time: 100
              }
        }
      };
      
      try {
        // Extract agent configuration from the form data
        const agentConfig = agent.config;
        
        // Use the agent config directly if it matches the expected structure
        if (agentConfig.citizens && Array.isArray(agentConfig.citizens)) {
          config.agents = {
            citizens: Array.isArray(agentConfig.citizens) ? agentConfig.citizens : [],
            firms: Array.isArray(agentConfig.firms) ? agentConfig.firms : [],
            governments: Array.isArray(agentConfig.governments) ? agentConfig.governments : [],
            banks: Array.isArray(agentConfig.banks) ? agentConfig.banks : [],
            nbs: Array.isArray(agentConfig.nbs) ? agentConfig.nbs : [],
            init_funcs: Array.isArray(agentConfig.init_funcs) ? agentConfig.init_funcs : []
          };
        } else {
          // Fallback to default structure if needed
          config.agents = {
            citizens: [
              {
                agent_class: 'citizen',
                number: 10,
                memory_config_func: null,
                memory_distributions: null
              }
            ],
            firms: [
              {
                agent_class: 'firm',
                number: 5,
                memory_config_func: null,
                memory_distributions: null
              }
            ],
            governments: [
              {
                agent_class: 'government',
                number: 1,
                memory_config_func: null,
                memory_distributions: null
              }
            ],
            banks: [
              {
                agent_class: 'bank',
                number: 1,
                memory_config_func: null,
                memory_distributions: null
              }
            ],
            nbs: [],
            init_funcs: []
          };
        }
      } catch (error) {
        console.warn('Error parsing agent config:', error);
        throw new Error('Invalid agent configuration');
      }
      
      // Process LLM configuration
      let llmConfigs = [];
      try {
        // Check if llm.config is already an array of LLM configs
        if (Array.isArray(llm.config)) {
          llmConfigs = llm.config;
        } 
        // Check if llm.config has llm_configs array
        else if (llm.config.llm_configs && Array.isArray(llm.config.llm_configs)) {
          llmConfigs = llm.config.llm_configs;
        }
        // Check if llm.config is a single LLM config object
        else if (llm.config.provider && llm.config.model) {
          llmConfigs = [llm.config];
        }
        // If none of the above, throw an error
        else {
          console.warn('LLM config format not recognized');
          throw new Error('Invalid LLM configuration: No valid provider or model found');
        }
      } catch (error) {
        console.warn('Error parsing LLM config:', error);
        throw new Error('Invalid LLM configuration');
      }
      
      // Build config object following config.json format
      config.llm = llmConfigs;
      
      return config;
    } catch (error) {
      console.error('Error building experiment configuration:', error);
      return null;
    }
  }
  
  /**
   * Validates a configuration object against required fields
   */
  validateConfig(config: any, requiredFields: string[]): boolean {
    for (const field of requiredFields) {
      if (config[field] === undefined || config[field] === null) {
        return false;
      }
    }
    return true;
  }
}

export default new ConfigService(); 