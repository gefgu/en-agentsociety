import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translations
import enCommon from './locales/en/common';
import enLLM from './locales/en/llm';
import enHome from './locales/en/home';
import enSurvey from './locales/en/survey';
import enConsole from './locales/en/console';
import enReplay from './locales/en/replay';
import enBill from './locales/en/bill';
import enAgent from './locales/en/agent';
import enMap from './locales/en/map';
import enWorkflow from './locales/en/workflow';
import enTemplate from './locales/en/template';
import enProfile from './locales/en/profile';
import enExperiment from './locales/en/experiment';
import enCharts from './locales/en/charts';

// Combine translations
const resources = {
    en: {
        translation: {
            ...enCommon,
            llm: enLLM,
            home: enHome,
            survey: enSurvey,
            console: enConsole,
            replay: enReplay,
            bill: enBill,
            agent: enAgent,
            map: enMap,
            workflow: enWorkflow,
            template: enTemplate,
            profile: enProfile,
            experiment: enExperiment,
            charts: enCharts,
        } 
    }
};

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        debug: true,
        // The en-agentsociety distribution is English-only.  Do not let a
        // browser's locale or a missing key silently put Chinese text back
        // into the UI.
        lng: 'en',
        fallbackLng: 'en',
        supportedLngs: ['en'],
        load: 'languageOnly',
        interpolation: {
            escapeValue: false,
        },
        resources
    });

export default i18n;
