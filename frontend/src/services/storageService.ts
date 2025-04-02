import localforage from 'localforage';

// Initialize localForage
localforage.config({
    name: 'agentsociety',
    storeName: 'configurations',
    description: 'Agent Society Configuration Storage'
});

// Storage keys
export const STORAGE_KEYS = {
    ENVIRONMENTS: 'environments',
    MAPS: 'maps',
    AGENTS: 'agents',
    WORKFLOWS: 'workflows',
    LLMS: 'llms'
};

// Configuration item interface
export interface ConfigItem {
    id: string;
    name: string;
    description?: string;
    createdAt: string;
    updatedAt: string;
    config: Record<string, unknown>;
}

// Save configuration list
export const saveConfigs = async <T extends ConfigItem>(key: string, configs: T[]): Promise<void> => {
    try {
        await localforage.setItem(key, configs);
        console.log(`Saved ${configs.length} items to ${key}`);
    } catch (error) {
        console.error(`Error saving to ${key}:`, error);
        throw error;
    }
};

// Get configuration list
export const getConfigs = async <T extends ConfigItem>(key: string): Promise<T[]> => {
    try {
        const configs = await localforage.getItem<T[]>(key);
        return configs || [];
    } catch (error) {
        console.error(`Error getting from ${key}:`, error);
        return [];
    }
};

// Add or update a single configuration
export const saveConfig = async <T extends ConfigItem>(key: string, config: T): Promise<void> => {
    try {
        const configs = await getConfigs<T>(key);
        const index = configs.findIndex(item => item.id === config.id);

        if (index >= 0) {
            // Update existing configuration
            configs[index] = {
                ...config,
                updatedAt: new Date().toISOString()
            };
        } else {
            // Add new configuration
            configs.push({
                ...config,
                createdAt: config.createdAt || new Date().toISOString(),
                updatedAt: new Date().toISOString()
            });
        }

        await saveConfigs(key, configs);
    } catch (error) {
        console.error(`Error saving config to ${key}:`, error);
        throw error;
    }
};

// Delete a single configuration
export const deleteConfig = async <T extends ConfigItem>(key: string, id: string): Promise<void> => {
    try {
        const configs = await getConfigs<T>(key);
        const filteredConfigs = configs.filter(config => config.id !== id);
        await saveConfigs(key, filteredConfigs);
    } catch (error) {
        console.error(`Error deleting config from ${key}:`, error);
        throw error;
    }
};

// Clear all configurations
export const clearAllConfigs = async (): Promise<void> => {
    try {
        await localforage.clear();
        console.log('All configurations cleared');
    } catch (error) {
        console.error('Error clearing configurations:', error);
        throw error;
    }
};

// Initialize example data (only on first use)
export const initializeExampleData = async (): Promise<void> => {
    try {
        // Check if already initialized
        const initialized = localStorage.getItem('initialized');
        if (initialized) return;

        // Mark as initialized
        localStorage.setItem('initialized', 'true');
    } catch (error) {
        console.error('Error initializing example data:', error);
    }
};

// Get configuration by ID
export const getConfigById = async <T extends ConfigItem>(key: string, id: string): Promise<T | null> => {
    try {
        const configs = await getConfigs<T>(key);
        return configs.find(config => config.id === id) || null;
    } catch (error) {
        console.error(`Error getting config by ID from ${key}:`, error);
        return null;
    }
};

// Export default object
const storageService = {
    saveConfigs,
    getConfigs,
    saveConfig,
    deleteConfig,
    clearAllConfigs,
    initializeExampleData,
    getConfigById,
};

export default storageService; 