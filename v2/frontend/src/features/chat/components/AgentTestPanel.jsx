import React from 'react';

const AgentTestPanel = ({ currentMessage }) => {
  return (
    <div className="agent-test-panel p-4 border border-gray-200 rounded-lg bg-gray-50">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Agent Test Panel</h3>
      <p className="text-xs text-gray-500">
        {currentMessage ? `Current message: ${currentMessage.substring(0, 50)}...` : 'No message'}
      </p>
    </div>
  );
};

export default AgentTestPanel;
