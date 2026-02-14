import React from 'react';
import Dashboard from '../components/Dashboard';

const DashboardContainer = ({ selectedEngine, onBack }) => {
  return <Dashboard selectedEngine={selectedEngine} onBack={onBack} />;
};

export default DashboardContainer;