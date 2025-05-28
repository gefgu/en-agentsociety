import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

i18n
    // detect user language
    // learn more: https://github.com/i18next/i18next-browser-languageDetector
    .use(LanguageDetector)
    // pass the i18n instance to react-i18next.
    .use(initReactI18next)
    // init i18next
    // for all options read: https://www.i18next.com/overview/configuration-options
    .init({
        debug: true,
        fallbackLng: 'zh',
        interpolation: {
            escapeValue: false, // not needed for react as it escapes by default
        },
        resources: {
            en: {
                translation: {
                    menu: {
                        experiments: 'Experiments',
                        survey: 'Survey',
                        documentation: 'Documentation',
                        github: 'GitHub',
                        mlflow: 'MLFlow',
                        llmConfigs: 'LLM Configs',
                        maps: 'Maps',
                        agents: 'Agents',
                        agentConfigs: 'Agent Configs',
                        agentTemplates: 'Agent Templates',
                        workflows: 'Workflows',
                        create: 'Create',
                        login: 'Login',
                        logout: 'Logout',
                        account: 'Account',
                        demo: 'Demo',
                        demoUser: 'Demo User',
                        profiles: 'Profiles',
                    },
                    home: {
                        whatsNew: "What's New",
                        releaseNotes: "Release v1.3. Click here to view the release notes.",
                        getStarted: "Get Started",
                        stars: "Stars",
                        mainDescription: "Create your society with <strong><em>Large Model-driven Social Human Agent</em></strong> and <strong><em>Realistic Urban Social Environment</em></strong>"
                    },
                    survey: {
                        createSurvey: "Create Survey",
                        editSurvey: "Edit Survey",
                        surveyName: "Survey Name",
                        surveyJsonData: "Survey JSON Data",
                        onlineVisualEditor: "Online Visual Editor",
                        submit: "Submit",
                        delete: "Delete",
                        deleteConfirm: "Are you sure to delete this survey?",
                        createSuccess: "Create success!",
                        updateSuccess: "Update success!",
                        deleteSuccess: "Delete success!",
                        createFailed: "Create failed:",
                        updateFailed: "Update failed:",
                        deleteFailed: "Delete failed:",
                        fetchFailed: "Fetch surveys failed:",
                        invalidJson: "Invalid JSON format",
                        pleaseInputName: "Please input name",
                        pleaseInputData: "Please input data JSON",
                        table: {
                            id: "ID",
                            name: "Name",
                            data: "Data",
                            createdAt: "Created At",
                            updatedAt: "Updated At",
                            action: "Action",
                            edit: "Edit",
                            delete: "Delete"
                        },
                    },
                    console: {
                        table: {
                            id: "ID",
                            name: "Name",
                            numDay: "Num Day",
                            status: "Status",
                            currentDay: "Current Day",
                            currentTime: "Current Time",
                            config: "Config",
                            error: "Error",
                            inputTokens: "Input Tokens",
                            outputTokens: "Output Tokens",
                            createdAt: "Created At",
                            updatedAt: "Updated At",
                            action: "Action"
                        },
                        statusEnum: {
                            "0": "Not Started",
                            "1": "Running",
                            "2": "Completed",
                            "3": "Error Interrupted",
                            "4": "Stopped"
                        },
                        buttons: {
                            goto: "Goto",
                            stop: "Stop",
                            detail: "Detail",
                            viewLog: "View Log",
                            export: "Export",
                            delete: "Delete"
                        },
                        modals: {
                            experimentDetail: "Experiment Detail",
                            experimentLog: "Experiment Log",
                            refresh: "Refresh",
                            manualRefresh: "Manual refresh",
                            refreshing: "Refreshing...",
                            refreshIntervals: {
                                oneSecond: "Every 1 second",
                                fiveSeconds: "Every 5 seconds",
                                tenSeconds: "Every 10 seconds",
                                thirtySeconds: "Every 30 seconds"
                            }
                        },
                        confirmations: {
                            stopExperiment: "Are you sure to stop this experiment?",
                            deleteExperiment: "Are you sure to delete this experiment?"
                        },
                        messages: {
                            stopSuccess: "Stop experiment successfully",
                            stopFailed: "Failed to stop experiment:",
                            deleteSuccess: "Delete experiment successfully",
                            deleteFailed: "Failed to delete experiment:",
                            noToken: "No token found, please login"
                        }
                    },
                    replay: {
                        day: "Day {{day}}",
                        chatbox: {
                            tabs: {
                                reflection: "Reflection",
                                agent: "Agent",
                                user: "User",
                                survey: "Survey",
                                metrics: "Metrics"
                            },
                            survey: {
                                preview: "Preview",
                                surveyName: "Survey Name",
                                surveySent: "Survey sent, you should wait for the agent to save the survey into database and respond",
                                messageSent: "Message sent, you should wait for the agent to save the message into database and respond",
                                sendFailed: "Failed to send:"
                            },
                            dialog: {
                                sendSuccess: "Message sent, you should wait for the agent to save the message into database and respond"
                            },
                            metrics: {
                                noMetrics: "No metrics data available",
                                step: "Step",
                                value: "Value"
                            }
                        },
                        infoPanel: {
                            title: "Agent Information",
                            chooseAgent: "Please choose an agent in map",
                            unknown: "[Unknown]",
                            currentStatus: "Current Status",
                            statusHistory: "Status History",
                            name: "name",
                            id: "ID",
                            showAsHeatmap: "Click to show as heatmap"
                        },
                        timelinePlayer: {
                            replay: "Replay",
                            live: "Live",
                            stepSpeed: {
                                "10s": "10s/step",
                                "5s": "5s/step",
                                "2s": "2s/step",
                                "1s": "1s/step",
                                "0.5s": "0.5s/step",
                                "0.25s": "0.25s/step",
                                "0.1s": "0.1s/step"
                            }
                        }
                    },
                    form: {
                        agent: {
                            title: "Agent Configurations",
                            createNew: "Create New",
                            searchPlaceholder: "Search agents",
                            editTitle: "Edit Agent",
                            createTitle: "Create Agent",
                            metadataTitle: "Configuration Metadata",
                            settingsTitle: "Agent Settings",
                            citizenGroup: "Citizen Group",
                            firmGroup: "Firm Group",
                            governmentGroup: "Government Group",
                            bankGroup: "Bank Group",
                            nbsGroup: "NBS Group",
                            customGroup: "Custom Group",
                            addGroup: "Add Group",
                            removeGroup: "Remove Group",
                            numberLabel: "Number of Agents",
                            numberPlaceholder: "Please enter number of agents",
                            distributionTitle: "Distribution",
                            addDistribution: "Add Distribution",
                            removeDistribution: "Remove Distribution",
                            attributeName: "Attribute Name",
                            attributePlaceholder: "e.g. age, income, education",
                            distributionType: "Distribution Type",
                            choices: "Choices",
                            choicesPlaceholder: "e.g. red,green,blue",
                            minValue: "Minimum Value",
                            maxValue: "Maximum Value",
                            mean: "Mean",
                            std: "Standard Deviation",
                            constant: "Constant Value",
                            selectTemplate: "Select Template",
                            selectTemplatePlaceholder: "Please select a template",
                            configurationMode: "Configuration Mode",
                            manual: "Manual",
                            useProfile: "Use Profile",
                            selectProfile: "Select Profile",
                            selectProfilePlaceholder: "Please select a profile"
                        },
                        llm: {
                            title: "LLM Configurations",
                            createNew: "Create New",
                            searchPlaceholder: "Search LLM configs",
                            editTitle: "Edit LLM Config",
                            createTitle: "Create LLM Config",
                            metadataTitle: "Configuration Metadata",
                            settingsTitle: "LLM Config Settings",
                            providerTitle: "LLM Provider",
                            providerLabel: "Provider",
                            providerPlaceholder: "Select LLM provider",
                            baseUrl: "Base URL",
                            baseUrlPlaceholder: "Enter base URL if using a custom endpoint",
                            apiKey: "API Key",
                            apiKeyPlaceholder: "Enter API key",
                            model: "Model",
                            modelPlaceholder: "Select model",
                            vllmModelPlaceholder: "Enter vLLM model name",
                            addProvider: "Add LLM Provider"
                        },
                        map: {
                            title: "Map Configurations",
                            createNew: "Create New",
                            searchPlaceholder: "Search maps",
                            editTitle: "Edit Map",
                            createTitle: "Create Map",
                            metadataTitle: "Configuration Metadata",
                            settingsTitle: "Map Settings",
                            uploadTitle: "New Map File",
                            uploadHint: "Click or drag map file to this area to upload",
                            uploadDescription: "Please upload a single .pb file."
                        },
                        common: {
                            name: "Name",
                            namePlaceholder: "Enter configuration name",
                            nameRequired: "Please enter a name for this configuration",
                            description: "Description",
                            descriptionPlaceholder: "Enter a description for this configuration",
                            edit: "Edit",
                            delete: "Delete",
                            deleteConfirm: "Are you sure you want to delete this configuration?",
                            duplicate: "Duplicate",
                            export: "Export",
                            lastUpdated: "Last Updated",
                            actions: "Actions",
                            submit: "Submit",
                            cancel: "Cancel",
                            metadataTitle: "Basic Information",
                            view: "View"
                        },
                        template: {
                            title: "Agent Templates",
                            createNew: "Create New",
                            searchPlaceholder: "Search templates",
                            editTitle: "Edit Template",
                            createTitle: "Create Template",
                            basicInfo: "Basic Information",
                            namePlaceholder: "General Social Agent",
                            descriptionPlaceholder: "Enter template description",
                            profileSection: "Profile Configuration",
                            baseSection: "Base Configuration",
                            agentConfig: "Agent Configuration",
                            blockConfig: "Block Configuration",
                            messages: {
                                createSuccess: "Template created successfully",
                                createFailed: "Failed to create template",
                                updateSuccess: "Template updated successfully",
                                updateFailed: "Failed to update template",
                                fetchFailed: "Failed to fetch template"
                            }
                        }
                    }
                }
            },
            zh: {
                translation: {
                    menu: {
                        experiments: '实验',
                        survey: '问卷',
                        documentation: '文档',
                        github: 'GitHub',
                        mlflow: 'MLFlow',
                        llmConfigs: 'LLM配置',
                        maps: '地图',
                        agents: '智能体',
                        agentConfigs: '智能体配置',
                        agentTemplates: '智能体模板',
                        workflows: '工作流',
                        create: '创建',
                        login: '登录',
                        logout: '退出登录',
                        account: '账户',
                        demo: '示例',
                        demoUser: '示例用户',
                        profiles: '智能体配置',
                    },
                    home: {
                        whatsNew: "最新动态",
                        releaseNotes: "V1.3版本发布。点击此处查看发布说明。",
                        getStarted: "开始使用",
                        stars: "星标",
                        mainDescription: "使用<strong><em>大模型驱动的社会人智能体</em></strong>和<strong><em>真实城市社会环境</em></strong>构建虚拟社会"
                    },
                    survey: {
                        createSurvey: "创建问卷",
                        editSurvey: "编辑问卷",
                        surveyName: "问卷名称",
                        surveyJsonData: "问卷JSON数据",
                        onlineVisualEditor: "在线可视化编辑器",
                        submit: "提交",
                        delete: "删除",
                        deleteConfirm: "确定要删除这个问卷吗？",
                        createSuccess: "创建成功！",
                        updateSuccess: "更新成功！",
                        deleteSuccess: "删除成功！",
                        createFailed: "创建失败：",
                        updateFailed: "更新失败：",
                        deleteFailed: "删除失败：",
                        fetchFailed: "获取问卷失败：",
                        invalidJson: "JSON格式无效",
                        pleaseInputName: "请输入名称",
                        pleaseInputData: "请输入JSON数据",
                        table: {
                            id: "ID",
                            name: "名称",
                            data: "数据",
                            createdAt: "创建时间",
                            updatedAt: "更新时间",
                            action: "操作",
                            edit: "编辑",
                            delete: "删除"
                        },
                    },
                    console: {
                        table: {
                            id: "ID",
                            name: "名称",
                            numDay: "天数",
                            status: "状态",
                            currentDay: "当前天数",
                            currentTime: "当前时间",
                            config: "配置",
                            error: "报错",
                            inputTokens: "输入Token数",
                            outputTokens: "输出Token数",
                            createdAt: "创建时间",
                            updatedAt: "更新时间",
                            action: "操作"
                        },
                        statusEnum: {
                            "0": "未开始",
                            "1": "运行中",
                            "2": "已完成",
                            "3": "错误中断",
                            "4": "已停止"
                        },
                        buttons: {
                            goto: "查看",
                            stop: "停止",
                            detail: "详情",
                            viewLog: "查看日志",
                            export: "导出",
                            delete: "删除"
                        },
                        modals: {
                            experimentDetail: "实验详情",
                            experimentLog: "实验日志",
                            refresh: "刷新",
                            manualRefresh: "手动刷新",
                            refreshing: "正在刷新...",
                            refreshIntervals: {
                                oneSecond: "每秒刷新",
                                fiveSeconds: "每5秒刷新",
                                tenSeconds: "每10秒刷新",
                                thirtySeconds: "每30秒刷新"
                            }
                        },
                        confirmations: {
                            stopExperiment: "确定要停止这个实验吗？",
                            deleteExperiment: "确定要删除这个实验吗？"
                        },
                        messages: {
                            stopSuccess: "停止实验成功",
                            stopFailed: "停止实验失败：",
                            deleteSuccess: "删除实验成功",
                            deleteFailed: "删除实验失败：",
                            noToken: "未找到token，请登录"
                        }
                    },
                    replay: {
                        day: "第{{day}}天",
                        chatbox: {
                            tabs: {
                                reflection: "反思",
                                agent: "智能体",
                                user: "用户",
                                survey: "问卷",
                                metrics: "指标"
                            },
                            dialog: {
                                sendSuccess: "消息已发送，请等待智能体将消息保存到数据库并响应"
                            },
                            survey: {
                                preview: "预览",
                                surveyName: "问卷名称",
                                surveySent: "问卷已发送，请等待智能体将问卷保存到数据库并响应",
                                messageSent: "消息已发送，请等待智能体将消息保存到数据库并响应",
                                sendFailed: "发送失败："
                            },
                            metrics: {
                                noMetrics: "没有可用的指标数据",
                                step: "步数",
                                value: "值"
                            }
                        },
                        infoPanel: {
                            title: "智能体信息",
                            chooseAgent: "请在地图中选择一个智能体",
                            unknown: "[未知]",
                            currentStatus: "当前状态",
                            statusHistory: "状态历史",
                            name: "名称",
                            id: "ID",
                            showAsHeatmap: "点击显示为热力图"
                        },
                        timelinePlayer: {
                            replay: "回放",
                            live: "直播",
                            stepSpeed: {
                                "10s": "10秒/步",
                                "5s": "5秒/步",
                                "2s": "2秒/步",
                                "1s": "1秒/步",
                                "0.5s": "0.5秒/步",
                                "0.25s": "0.25秒/步",
                                "0.1s": "0.1秒/步"
                            }
                        }
                    },
                    form: {
                        agent: {
                            title: "智能体配置",
                            createNew: "新建",
                            searchPlaceholder: "搜索智能体",
                            editTitle: "编辑智能体",
                            createTitle: "创建智能体",
                            metadataTitle: "配置元数据",
                            settingsTitle: "智能体设置",
                            citizenGroup: "公民组",
                            firmGroup: "企业组",
                            governmentGroup: "政府组",
                            bankGroup: "银行组",
                            nbsGroup: "统计局组",
                            customGroup: "自定义组",
                            addGroup: "添加组",
                            removeGroup: "移除组",
                            numberLabel: "智能体数量",
                            numberPlaceholder: "请输入智能体数量",
                            distributionTitle: "分布",
                            addDistribution: "添加分布",
                            removeDistribution: "移除分布",
                            attributeName: "属性名称",
                            attributePlaceholder: "例如：年龄、收入、教育",
                            distributionType: "分布类型",
                            choices: "选项",
                            choicesPlaceholder: "例如：红色,绿色,蓝色",
                            minValue: "最小值",
                            maxValue: "最大值",
                            mean: "均值",
                            std: "标准差",
                            constant: "常量值",
                            selectTemplate: "选择模板",
                            selectTemplatePlaceholder: "请选择一个模板",
                            configurationMode: "配置模式",
                            manual: "手动",
                            useProfile: "使用配置文件",
                            selectProfile: "选择配置文件",
                            selectProfilePlaceholder: "请选择一个配置文件"
                        },
                        llm: {
                            title: "LLM配置",
                            createNew: "新建",
                            searchPlaceholder: "搜索LLM配置",
                            editTitle: "编辑LLM配置",
                            createTitle: "创建LLM配置",
                            metadataTitle: "配置元数据",
                            settingsTitle: "LLM配置设置",
                            providerTitle: "LLM提供商",
                            providerLabel: "提供商",
                            providerPlaceholder: "选择LLM提供商",
                            baseUrl: "Base URL",
                            baseUrlPlaceholder: "如使用自定义端点请输入Base URL",
                            apiKey: "API密钥",
                            apiKeyPlaceholder: "请输入API密钥",
                            model: "模型",
                            modelPlaceholder: "选择模型",
                            vllmModelPlaceholder: "输入vLLM模型名称",
                            addProvider: "添加LLM提供商"
                        },
                        map: {
                            title: "地图配置",
                            createNew: "新建",
                            searchPlaceholder: "搜索地图",
                            editTitle: "编辑地图",
                            createTitle: "创建地图",
                            metadataTitle: "配置元数据",
                            settingsTitle: "地图设置",
                            uploadTitle: "新地图文件",
                            uploadHint: "点击或拖拽地图文件到此区域上传",
                            uploadDescription: "上传单个.pb文件。"
                        },
                        common: {
                            name: "名称",
                            namePlaceholder: "请输入配置名称",
                            nameRequired: "请输入配置名称",
                            description: "描述",
                            descriptionPlaceholder: "请输入配置描述",
                            edit: "编辑",
                            delete: "删除",
                            deleteConfirm: "确定要删除此配置吗？",
                            duplicate: "复制",
                            export: "导出",
                            lastUpdated: "最后更新时间",
                            actions: "操作",
                            submit: "提交",
                            cancel: "取消",
                            metadataTitle: "基本信息",
                            view: "查看"
                        },
                        template: {
                            title: "智能体模板",
                            createNew: "新建",
                            searchPlaceholder: "搜索模板",
                            editTitle: "编辑模板",
                            createTitle: "创建模板",
                            basicInfo: "基本信息",
                            namePlaceholder: "通用社会智能体",
                            descriptionPlaceholder: "请输入模板描述",
                            profileSection: "配置文件配置",
                            baseSection: "基础配置",
                            agentConfig: "智能体配置",
                            blockConfig: "区块配置",
                            messages: {
                                createSuccess: "模板创建成功",
                                createFailed: "模板创建失败",
                                updateSuccess: "模板更新成功",
                                updateFailed: "模板更新失败",
                                fetchFailed: "获取模板失败"
                            }
                        }
                    }
                }
            }
        }
    });

export default i18n;