// Configuration item interface
export interface ConfigItem {
    id?: string;
    name: string;
    description?: string;
    createdAt?: string;
    updatedAt?: string;
    config: any;
}
