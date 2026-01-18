import { useState, useRef } from 'react'
import Editor from '@monaco-editor/react'

interface CodeEditorProps {
  onSubmit: (code: string) => void
  disabled?: boolean
}

export function CodeEditor({ onSubmit, disabled }: CodeEditorProps) {
  const [code, setCode] = useState('')
  const editorRef = useRef<any>(null)

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor
  }

  const handleSubmit = () => {
    if (code.trim() && !disabled) {
      onSubmit(code)
      // Don't clear the editor - keep the code visible
    }
  }

  const handleEditorChange = (value: string | undefined) => {
    setCode(value || '')
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">Code Editor</h3>
        <div className="flex gap-2">
          {/* Debug Mode: Skip solving */}
          <button
            onClick={() => onSubmit('# DEBUG: Auto-complete')}
            disabled={disabled}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Debug: Auto-complete this card"
          >
            🐛 Skip
          </button>
          <button
            onClick={handleSubmit}
            disabled={disabled || !code.trim()}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Submit Solution
          </button>
        </div>
      </div>
      <div className="border border-gray-700 rounded-lg overflow-hidden">
        <Editor
          height="400px"
          defaultLanguage="python"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            scrollBeyondLastLine: false,
            readOnly: disabled,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollbar: {
              vertical: 'auto',
              horizontal: 'auto',
            },
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  )
}