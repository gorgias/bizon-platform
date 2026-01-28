import { Routes, Route } from 'react-router-dom'
import { PageShell } from './components/layout'
import { ToastProvider } from './contexts/ToastContext'
import { ToastContainer } from './components/Toast'
import {
  DashboardPage,
  PipelinesPage,
  PipelineDetailPage,
  PipelineCreatePage,
  ConnectorsPage,
  SavedPage,
  CustomSourcesPage,
} from './pages'

function App() {
  return (
    <ToastProvider>
      <PageShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/pipelines" element={<PipelinesPage />} />
          <Route path="/pipelines/new" element={<PipelineCreatePage />} />
          <Route path="/pipelines/:id" element={<PipelineDetailPage />} />
          <Route path="/pipelines/:id/edit" element={<PipelineCreatePage />} />
          <Route path="/connectors" element={<ConnectorsPage />} />
          <Route path="/custom-sources" element={<CustomSourcesPage />} />
          <Route path="/saved" element={<SavedPage />} />
        </Routes>
      </PageShell>
      <ToastContainer />
    </ToastProvider>
  )
}

export default App
