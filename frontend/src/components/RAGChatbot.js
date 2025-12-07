/*
 * RAG Chatbot Component for Physical AI & Humanoid Robotics Course
 * This component provides a chat interface that connects to the RAG backend
 */

import React, { useState, useEffect, useRef } from 'react';
import './RAGChatbot.css';

const RAGChatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentModule, setCurrentModule] = useState('');
  const [currentChapter, setCurrentChapter] = useState('');
  const messagesEndRef = useRef(null);

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

  useEffect(() => {
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
  useEffect(() => {
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
        <button className="chatbot-button" onClick={toggleChatbot}>
          <span>🤖 Ask CourseBot</span>
        </button>
      )}

      {/* Chatbot window */}
      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <div className="header-content">
              <h3>CourseBot</h3>
              <p>Ask anything about the Physical AI & Humanoid Robotics Course</p>
            </div>
            <button className="close-button" onClick={toggleChatbot}>
              ×
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.length === 0 ? (
              <div className="welcome-message">
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
                  className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
                >
                  <div className="message-content">
                    <div className="message-text">{message.text}</div>
                    {message.sender === 'bot' && !message.isError && (
                      <div className="message-meta">
                        <small>Confidence: {(message.confidence * 100).toFixed(0)}%</small>
                        {message.sources && message.sources.length > 0 && (
                          <details className="sources-details">
                            <summary>Sources</summary>
                            <ul>
                              {message.sources.slice(0, 3).map((source, idx) => (
                                <li key={idx}>{source}</li>
                              ))}
                              {message.sources.length > 3 && (
                                <li>... and {message.sources.length - 3} more</li>
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
              <div className="message bot-message">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chatbot-input-area">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about the course..."
              rows="2"
              disabled={isLoading}
            />
            <button 
              onClick={sendMessage} 
              disabled={!inputValue.trim() || isLoading}
              className="send-button"
            >
              Send
            </button>
          </div>
          
          <div className="chatbot-context">
            {currentModule && <span>Module: {currentModule}</span>}
            {currentChapter && <span>Chapter: {currentChapter}</span>}
          </div>
        </div>
      )}
    </div>
  );
};

export default RAGChatbot;