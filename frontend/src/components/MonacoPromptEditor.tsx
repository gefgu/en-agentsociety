import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';

interface MonacoPromptEditorProps {
  value?: string;
  onChange?: (value: string | undefined) => void;
  height?: string;
  suggestions?: Array<{
    label: string;
    detail?: string;
    children?: Array<{
      label: string;
      detail?: string;
      children?: Array<any>;  // Support infinite levels
    }>;
  }>;
  editorId?: string;
}

const MonacoPromptEditor: React.FC<MonacoPromptEditorProps> = ({
  value = '',
  onChange,
  height = '200px',
  suggestions = [],
  editorId = 'default'
}) => {
  // Use useRef to ensure provider is registered only once
  const providerRef = useRef<any>(null);
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);

  // Register completion provider
  const registerCompletionProvider = (monaco: any) => {
    // Remove existing provider if it exists
    if (providerRef.current) {
      providerRef.current.dispose();
      providerRef.current = null;
    }
    
    // Use unique language ID
    const uniqueLanguageId = `markdown-${editorId}`;
    
    // Register custom language
    if (!monaco.languages.getLanguages().some((lang: any) => lang.id === uniqueLanguageId)) {
      monaco.languages.register({ 
        id: uniqueLanguageId,
        extensions: ['.md'],
        aliases: ['Markdown', uniqueLanguageId],
        mimetypes: ['text/markdown']
      });
    }
    
    // Register new provider
    providerRef.current = monaco.languages.registerCompletionItemProvider(uniqueLanguageId, {
      triggerCharacters: ['$', '.'],
      provideCompletionItems: (model: any, position: any) => {
        const textUntilPosition = model.getValueInRange({
          startLineNumber: position.lineNumber,
          startColumn: 1,
          endLineNumber: position.lineNumber,
          endColumn: position.column
        });
        
        const hasDollar = textUntilPosition.endsWith('$');
        const hasDot = textUntilPosition.endsWith('.');
        const word = model.getWordUntilPosition(position);
        
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: hasDollar || hasDot ? position.column : word.startColumn,
          endColumn: position.column
        };

        // Get current input path
        const currentPath = getCurrentPath(textUntilPosition);
        let currentSuggestions = getSuggestionsForPath(currentPath, suggestions);

        return {
          suggestions: currentSuggestions.map((item, index) => {
            let insertText = item.label;
            
            // Check if it's the last level (no children or empty children)
            const isLastLevel = !item.children || item.children.length === 0;
            const hasChildren = item.children && item.children.length > 0;
            
            // If triggered by dot
            if (hasDot) {
              if (hasChildren) {
                // If has children, add dot
                insertText = `${insertText}.`;
              } else {
                // If it's the last level, add closing brace
                insertText = `${insertText}}`;
              }
            } else {
              // If triggered by $ or other
              if (isLastLevel) {
                // Always wrap with braces for last level
                insertText = `{${insertText}}`;
              } else {
                // Not last level, add dot
                insertText = `{${insertText}.`;
              }
            }
            
            return {
              label: item.label,
              kind: monaco.languages.CompletionItemKind.Field,
              insertText: insertText,
              detail: item.detail || '',
              range: range,
              sortText: `${index}`.padStart(5, '0'),
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              command: hasChildren ? { id: 'editor.action.triggerSuggest', title: 'Trigger Suggest' } : undefined
            };
          })
        };
      }
    });
  };
  
  // Handle editor mount
  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    
    // Register completion provider
    registerCompletionProvider(monaco);
    
    // Configure editor options
    editor.updateOptions({
      fontSize: 14,
      lineHeight: 20,
      quickSuggestions: {
        other: true,
        comments: true,
        strings: true
      },
      suggestOnTriggerCharacters: true,
      acceptSuggestionOnEnter: 'on',
      tabCompletion: 'on',
      wordBasedSuggestions: 'on',
      autoClosingBrackets: 'always',  // Add auto-closing brackets configuration
      autoClosingQuotes: 'always',    // Add auto-closing quotes configuration
      suggest: {
        showIcons: true,
        insertMode: 'insert',
        filterGraceful: true,
        snippetsPreventQuickSuggestions: false,
        localityBonus: true,
        shareSuggestSelections: true,
        showMethods: true,
        showFunctions: true,
        showVariables: true,
        showClasses: true,
        showWords: true,
        preview: true,
        previewMode: 'prefix',
        showInlineDetails: true
      }
    });

    // Set editor background color
    monaco.editor.defineTheme('vs-gray', {
      base: 'vs',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#f0f0f0',  // Light gray background
      }
    });
    monaco.editor.setTheme('vs-gray');
  };
  
  // Re-register provider when suggestions change
  useEffect(() => {
    if (monacoRef.current) {
      registerCompletionProvider(monacoRef.current);
    }
  }, [suggestions]);
  
  // Cleanup when component unmounts
  useEffect(() => {
    return () => {
      if (providerRef.current) {
        providerRef.current.dispose();
      }
    };
  }, []);

  // Get current input path
  const getCurrentPath = (textUntilPosition: string): string[] => {
    const match = textUntilPosition.match(/[\w.]+$/);
    return match ? match[0].split('.') : [];
  };

  // Get suggestions based on current path
  const getSuggestionsForPath = (path: string[], suggestions: any[]): any[] => {
    if (path.length <= 1) {
      return suggestions;
    }

    let currentSuggestions = suggestions;
    for (let i = 0; i < path.length - 1; i++) {
      const currentSegment = path[i];
      const matchingSuggestion = currentSuggestions.find(s => s.label === currentSegment);
      if (matchingSuggestion && matchingSuggestion.children) {
        currentSuggestions = matchingSuggestion.children;
      } else {
        return [];
      }
    }
    return currentSuggestions;
  };

  return (
    <Editor
      height={height}
      defaultLanguage={`markdown-${editorId}`}
      theme="vs-gray"
      value={value}
      onChange={onChange}
      onMount={handleEditorDidMount}
      options={{
        minimap: { enabled: false },
        lineNumbers: 'on',
        folding: false,
        wordWrap: 'on',
        contextmenu: false,
        scrollBeyondLastLine: false,
        automaticLayout: true,
        fontSize: 16,
        fontFamily: "'Menlo', 'Monaco', 'Courier New', monospace",
        lineHeight: 22,
        padding: { top: 10, bottom: 10 },
        renderLineHighlight: 'none',
        overviewRulerLanes: 0,
        hideCursorInOverviewRuler: true,
        overviewRulerBorder: false,
        quickSuggestions: true,
        suggestOnTriggerCharacters: true,
        acceptSuggestionOnEnter: 'on',
        tabCompletion: 'on',
        links: true,
        formatOnType: true
      }}
    />
  );
};

export default MonacoPromptEditor; 