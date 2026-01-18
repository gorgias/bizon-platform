import { useState, useRef } from 'react'
import { Upload, CheckCircle, FileCode } from 'lucide-react'
import { Modal, Button, LoadingSpinner } from '../ui'
import { useUploadCustomSource } from '../../hooks'

interface UploadSourceModalProps {
  isOpen: boolean
  onClose: () => void
}

export function UploadSourceModal({ isOpen, onClose }: UploadSourceModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadSource = useUploadCustomSource()

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0])
    }
  }

  const handleFileSelection = (file: File) => {
    if (file.name.endsWith('.py') || file.name.endsWith('.zip')) {
      setSelectedFile(file)
      uploadSource.reset()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0])
    }
  }

  const handleUpload = () => {
    if (selectedFile) {
      uploadSource.mutate(selectedFile)
    }
  }

  const handleClose = () => {
    setSelectedFile(null)
    uploadSource.reset()
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Upload Custom Source" size="md">
      <div className="p-6 space-y-4">
        <p className="text-sm text-bizon-textSecondary">
          Upload a Python file (.py) or a zip archive containing a source.py file.
        </p>

        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-bizon-primary bg-bizon-primary/5'
              : 'border-bizon-border hover:border-bizon-primary/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".py,.zip"
            onChange={handleInputChange}
            className="hidden"
          />

          {selectedFile ? (
            <div className="space-y-3">
              <FileCode className="h-12 w-12 text-bizon-primary mx-auto" />
              <p className="font-medium text-bizon-text">{selectedFile.name}</p>
              <p className="text-sm text-bizon-muted">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSelectedFile(null)
                  uploadSource.reset()
                }}
              >
                Choose different file
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              <Upload className="h-12 w-12 text-bizon-muted mx-auto" />
              <p className="text-bizon-text">
                Drag and drop a file here, or{' '}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-bizon-primary hover:underline"
                >
                  browse
                </button>
              </p>
              <p className="text-sm text-bizon-muted">Supports .py and .zip files</p>
            </div>
          )}
        </div>

        {selectedFile && !uploadSource.isSuccess && (
          <Button
            onClick={handleUpload}
            disabled={uploadSource.isPending}
            className="w-full"
          >
            {uploadSource.isPending ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload Source
              </>
            )}
          </Button>
        )}

        {uploadSource.isSuccess && uploadSource.data && (
          <div className="p-4 rounded-lg bg-bizon-success/10 border border-bizon-success/30">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-bizon-success flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-bizon-success">Upload Successful</p>
                <p className="text-sm text-bizon-textSecondary mt-1">
                  Source "{uploadSource.data.name}" uploaded with{' '}
                  {uploadSource.data.streams.length} stream
                  {uploadSource.data.streams.length !== 1 ? 's' : ''}:
                </p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {uploadSource.data.streams.map((stream) => (
                    <span
                      key={stream}
                      className="px-2 py-0.5 text-xs bg-bizon-bg text-bizon-textSecondary rounded"
                    >
                      {stream}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {uploadSource.error && (
          <div className="p-4 rounded-lg bg-bizon-danger/10 border border-bizon-danger/30">
            <p className="text-bizon-danger font-medium">Upload Failed</p>
            <p className="text-sm text-bizon-textSecondary mt-1">
              {uploadSource.error instanceof Error
                ? uploadSource.error.message
                : 'An error occurred'}
            </p>
          </div>
        )}

        {uploadSource.isSuccess && (
          <Button variant="secondary" onClick={handleClose} className="w-full">
            Close
          </Button>
        )}
      </div>
    </Modal>
  )
}
