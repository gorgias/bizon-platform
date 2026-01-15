import { Routes, Route } from 'react-router-dom'
import { PageShell } from './components/layout'
import {
  DashboardPage,
  PipelinesPage,
  PipelineDetailPage,
  PipelineCreatePage,
  ConnectorsPage,
  SavedPage,
} from './pages'

function App() {
  return (
    <PageShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/pipelines" element={<PipelinesPage />} />
        <Route path="/pipelines/new" element={<PipelineCreatePage />} />
        <Route path="/pipelines/:id" element={<PipelineDetailPage />} />
        <Route path="/connectors" element={<ConnectorsPage />} />
        <Route path="/saved" element={<SavedPage />} />
      </Routes>
    </PageShell>
  )
}

export default App
