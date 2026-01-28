import { X, CheckCircle, XCircle, Info } from 'lucide-react'
import { useToast } from '../contexts/ToastContext'

export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 space-y-2 z-50">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 p-4 rounded-lg shadow-lg max-w-md animate-in slide-in-from-right ${
            toast.type === 'error'
              ? 'bg-red-600 text-white'
              : toast.type === 'success'
                ? 'bg-green-600 text-white'
                : 'bg-bizon-surface text-bizon-text border border-bizon-border'
          }`}
        >
          <div className="flex-shrink-0 mt-0.5">
            {toast.type === 'error' && <XCircle className="h-5 w-5" />}
            {toast.type === 'success' && <CheckCircle className="h-5 w-5" />}
            {toast.type === 'info' && <Info className="h-5 w-5" />}
          </div>
          <p className="flex-1 text-sm">{toast.message}</p>
          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 p-1 rounded hover:bg-black/10"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  )
}
