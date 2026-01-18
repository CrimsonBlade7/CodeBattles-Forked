import { useEffect } from 'react'

interface TestFeedbackProps {
    type: 'success' | 'error' | null
    message: string
    onDismiss: () => void
}

export function TestFeedback({ type, message, onDismiss }: TestFeedbackProps) {
    useEffect(() => {
        if (type) {
            const timer = setTimeout(() => {
                onDismiss()
            }, 5000) // Auto-dismiss after 5 seconds

            return () => clearTimeout(timer)
        }
    }, [type, onDismiss])

    if (!type) return null

    return (
        <div
            className={`mt-4 p-4 rounded-lg border ${type === 'success'
                    ? 'bg-green-900/30 border-green-700 text-green-300'
                    : 'bg-red-900/30 border-red-700 text-red-300'
                }`}
        >
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <h4 className="font-semibold mb-1">
                        {type === 'success' ? '✅ All Tests Passed!' : '❌ Test Failed'}
                    </h4>
                    <p className="text-sm whitespace-pre-wrap">{message}</p>
                </div>
                <button
                    onClick={onDismiss}
                    className="ml-4 text-gray-400 hover:text-white"
                >
                    ✕
                </button>
            </div>
        </div>
    )
}
