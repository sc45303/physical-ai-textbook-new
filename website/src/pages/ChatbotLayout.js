import React from 'react';
import ChatbotWidget from '../components/ChatbotWidget/ChatbotWidget';

// A wrapper layout that includes the chatbot widget
const ChatbotLayout = ({ children }) => {
  return (
    <>
      {children}
      <ChatbotWidget />
    </>
  );
};

export default ChatbotLayout;