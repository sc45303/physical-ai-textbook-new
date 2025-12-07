/*
 * Docusaurus Chatbot Widget
 * Wrapper for the RAGChatbot component to integrate with Docusaurus
 */

import React, { useEffect } from 'react';
import ReactDom from 'react-dom/client';
import './ChatbotWidget.css';

// Since the original RAGChatbot is in the frontend directory, we'll implement the same functionality here
const ChatbotWidget = () => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [messages, setMessages] = React.useState([]);
  const [inputValue, setInputValue] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [currentModule, setCurrentModule] = React.useState('');
  const [currentChapter, setCurrentChapter] = React.useState('');
  const messagesEndRef = React.useRef(null);

  // API configuration
  const API_BASE_URL = process.env.REACT_APP_CHATBOT_API_URL || 'http://localhost:8000';

  // Toggle chatbot open/close
  const toggleChatbot = () => {
    setIsOpen(!isOpen);
  };

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Function to send message to the RAG backend
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    // Add user message to the conversation
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Prepare the request payload
      const requestBody = {
        question: inputValue,
        module_context: currentModule || undefined,
        chapter_context: currentChapter || undefined
      };

      // Make API call to RAG backend
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();

      // Create bot message from API response
      const botMessage = {
        id: Date.now() + 1,
        text: data.answer,
        sender: 'bot',
        sources: data.sources,
        confidence: data.confidence,
        timestamp: new Date().toISOString()
      };

      // Add bot response to the conversation
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);

      // Add error message to the conversation
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your question. Please try again.',
        sender: 'bot',
        isError: true,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key press for sending message
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Function to get current page context (module/chapter)
  React.useEffect(() => {
    // Extract module and chapter from URL
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length >= 3) {
      const modulePart = pathParts[1]; // e.g., 'modules'
      const moduleSection = pathParts[2]; // e.g., 'ros2', 'simulation', etc.

      if (moduleSection !== 'modules') {
        setCurrentModule(moduleSection);
      }

      if (pathParts.length >= 4) {
        // Extract chapter name
        const chapterPart = pathParts[3];
        setCurrentChapter(chapterPart);
      }
    }
  }, []);

  return (
    <div className={`rag-chatbot ${isOpen ? 'open' : ''}`}>
      {/* Chatbot button */}
      {!isOpen && (
        <button 
          className="chatbot-button" 
          onClick={toggleChatbot}
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            backgroundColor: '#007cba',
            color: 'white',
            border: 'none',
            borderRadius: '50%',
            width: '60px',
            height: '60px',
            fontSize: '24px',
            cursor: 'pointer',
            zIndex: 1000,
            boxShadow: '0 4px 8px rgba(0,0,0,0.3)'
          }}
        >
          🤖
        </button>
      )}

      {/* Chatbot window */}
      {isOpen && (
        <div 
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            zIndex: 1000,
            width: '400px',
            height: '500px',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'white',
            borderRadius: '8px',
            overflow: 'hidden',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
          }}
        >
          <div 
            style={{
              backgroundColor: '#007cba',
              color: 'white',
              padding: '12px 16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <div>
              <h3 style={{ margin: 0, fontSize: '16px' }}>CourseBot</h3>
              <p style={{ margin: 0, fontSize: '12px', opacity: 0.9 }}>Ask anything about the Physical AI & Humanoid Robotics Course</p>
            </div>
            <button 
              onClick={toggleChatbot}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                fontSize: '20px',
                cursor: 'pointer'
              }}
            >
              ×
            </button>
          </div>

          <div 
            style={{
              flex: 1,
              padding: '16px',
              overflowY: 'auto',
              backgroundColor: '#f9f9f9',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            {messages.length === 0 ? (
              <div>
                <h4>Welcome to CourseBot!</h4>
                <p>I can answer questions about the Physical AI & Humanoid Robotics Course.</p>
                <p>Ask me about:</p>
                <ul>
                  <li>ROS 2 concepts and implementation</li>
                  <li>Simulation environments (Gazebo, Unity)</li>
                  <li>NVIDIA Isaac and perception systems</li>
                  <li>Vision-Language-Action integration</li>
                  <li>Any other course content</li>
                </ul>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  style={{
                    marginBottom: '12px',
                    textAlign: message.sender === 'user' ? 'right' : 'left'
                  }}
                >
                  <div
                    style={{
                      display: 'inline-block',
                      padding: '8px 12px',
                      borderRadius: '18px',
                      backgroundColor: message.sender === 'user' ? '#007cba' : '#e5e5ea',
                      color: message.sender === 'user' ? 'white' : 'black'
                    }}
                  >
                    <div style={{ marginBottom: '4px' }}>{message.text}</div>
                    {message.sender === 'bot' && !message.isError && (
                      <div style={{ fontSize: '12px', opacity: 0.7 }}>
                        <div>Confidence: {(message.confidence * 100).toFixed(0)}%</div>
                        {message.sources && message.sources.length > 0 && (
                          <details style={{ marginTop: '4px' }}>
                            <summary>Sources</summary>
                            <ul style={{ textAlign: 'left', paddingLeft: '20px' }}>
                              {message.sources.slice(0, 3).map((source, idx) => (
                                <li key={idx} style={{ fontSize: '11px' }}>{source}</li>
                              ))}
                              {message.sources.length > 3 && (
                                <li style={{ fontSize: '11px' }}>... and {message.sources.length - 3} more</li>
                              )}
                            </ul>
                          </details>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div style={{ textAlign: 'left', marginBottom: '12px' }}>
                <div
                  style={{
                    display: 'inline-block',
                    padding: '8px 12px',
                    borderRadius: '18px',
                    backgroundColor: '#e5e5ea',
                    color: 'black'
                  }}
                >
                  <div className="typing-indicator">
                    <span style={{ display: 'inline-block', margin: '0 2px' }}>●</span>
                    <span style={{ display: 'inline-block', margin: '0 2px' }}>●</span>
                    <span style={{ display: 'inline-block', margin: '0 2px' }}>●</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div 
            style={{
              padding: '12px',
              backgroundColor: 'white',
              borderTop: '1px solid #e0e0e0',
              display: 'flex'
            }}
          >
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about the course..."
              rows={2}
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                resize: 'none'
              }}
            />
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              style={{
                marginLeft: '8px',
                padding: '8px 16px',
                backgroundColor: inputValue.trim() && !isLoading ? '#007cba' : '#ccc',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: inputValue.trim() && !isLoading ? 'pointer' : 'not-allowed'
              }}
            >
              Send
            </button>
          </div>

          <div 
            style={{
              padding: '4px 12px 8px',
              fontSize: '12px',
              color: '#666',
              textAlign: 'center',
              backgroundColor: 'white'
            }}
          >
            {currentModule && <span>Module: {currentModule} </span>}
            {currentChapter && <span>Chapter: {currentChapter}</span>}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotWidget;