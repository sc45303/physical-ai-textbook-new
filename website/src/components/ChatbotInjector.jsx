import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import ChatbotWidget from './ChatbotWidget/ChatbotWidget';

const ChatbotInjector: React.FC = () => {
  useEffect(() => {
    // Create a container for the chatbot
    const container = document.createElement('div');
    container.id = 'chatbot-container';
    document.body.appendChild(container);

    // Cleanup function
    return () => {
      const existingContainer = document.getElementById('chatbot-container');
      if (existingContainer) {
        document.body.removeChild(existingContainer);
      }
    };
  }, []);

  // Find the container and render the widget into it
  const container = document.getElementById('chatbot-container');

  return container ? createPortal(<ChatbotWidget />, container) : null;
};

export default ChatbotInjector;