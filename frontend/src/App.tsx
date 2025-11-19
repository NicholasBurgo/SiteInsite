import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Generator } from './pages/Generator';
import { Review } from './pages/Review';
import { RunView } from './pages/RunView';
import ConfirmPage from './pages/ConfirmPage';
import SiteGenerator from './pages/SiteGenerator';
import ThemeDesigner from './pages/ThemeDesigner';
import PreviousRuns from './components/PreviousRuns';
import InsightReport from './pages/InsightReport';
import { DarkModeProvider } from './contexts/DarkModeContext';
import { DarkModeToggle } from './components/DarkModeToggle';

export default function App() {
  return (
    <DarkModeProvider>
      <div className="min-h-screen bg-white dark:bg-gray-900 transition-colors duration-200">
        <Router>
          <Routes>
            <Route path="/" element={<SiteGenerator />} />
            <Route path="/generator" element={<Generator />} />
            <Route path="/review/:runId" element={<Review />} />
            <Route path="/confirm/:runId" element={<ConfirmPage />} />
            <Route path="/theme-designer" element={<ThemeDesigner />} />
            <Route path="/runs/:runId" element={<RunView />} />
            <Route path="/runs/:runId/previous" element={<PreviousRuns />} />
            <Route path="/runs/:runId/insights" element={<InsightReport />} />
          </Routes>
        </Router>
        <DarkModeToggle />
      </div>
    </DarkModeProvider>
  );
}