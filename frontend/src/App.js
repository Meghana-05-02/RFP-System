import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import CreateRFP from './components/CreateRFP';
import RFPDetail from './components/RFPDetail';
import ComparisonTable from './components/ComparisonTable';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CreateRFP />} />
        <Route path="/rfp/:id" element={<RFPDetail />} />
        <Route path="/comparison/:id" element={<ComparisonTable />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
