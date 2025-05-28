// Configuration item interface
export interface ConfigItem {
    tenant_id?: string;
    id?: string;
    name: string;
    description?: string;
    created_at?: string;
    updated_at?: string;
    config: any;
}
