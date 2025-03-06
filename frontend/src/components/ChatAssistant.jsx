import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const ChatAssistant = ({ fileId }) => {
  const [messages, setMessages] = useState([
    { 
      type: 'system', 
      content: 'Hello! I can answer questions about your article summaries. What would you like to know?' 
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    // Add user message to chat
    const userMessage = { type: 'user', content: inputValue };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setIsLoading(true);
    
    try {
      // Make API call to your backend
      const response = await axios.post('http://127.0.0.1:8000/invoke-agent/', {
        input_query: inputValue,
        file_id: fileId // Optional: Include file_id if your API needs it for context
      });
      
      // Add AI response to chat
      if (response.data && response.data.response && response.data.response.output) {
        const aiMessage = { type: 'assistant', content: response.data.response.output };
        setMessages(prevMessages => [...prevMessages, aiMessage]);
      } else {
        // Handle unexpected response format
        const errorMessage = { type: 'error', content: 'Sorry, I received an invalid response. Please try again.' };
        setMessages(prevMessages => [...prevMessages, errorMessage]);
      }
    } catch (error) {
      console.error('Error querying the assistant:', error);
      const errorMessage = { 
        type: 'error', 
        content: `Sorry, there was an error: ${error.response?.data?.detail || error.message}` 
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
      setInputValue('');
    }
  };

  return (
    <div style={{ border: '1px solid #e0e0e0' }} className="rounded-lg overflow-hidden shadow-lg bg-white">
      <div className="bg-blue-600 text-white p-4">
        <h2 className="text-xl font-semibold">Data Assistant</h2>
      </div>
      
      {/* Messages container */}
      <div className="h-80 overflow-y-auto p-4 bg-gray-50">
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`mb-4 ${
              message.type === 'user' 
                ? 'ml-auto bg-blue-500 text-white' 
                : message.type === 'error'
                  ? 'bg-red-100 border-l-4 border-red-500 text-red-700'
                  : 'bg-white border border-gray-200'
            } p-3 rounded-lg max-w-3/4 shadow-sm`}
          >
            {message.content}
          </div>
        ))}
        {isLoading && (
          <div className="flex items-center text-gray-500 p-3">
            <div className="w-2 h-2 bg-gray-400 rounded-full mr-1 animate-pulse"></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full mr-1 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input form */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="flex-grow p-2 border rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Ask a question about your data..."
            disabled={isLoading}
          />
          <button
            type="submit"
            className={`px-4 py-2 ${
              isLoading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
            } text-white rounded-r focus:outline-none`}
            disabled={isLoading}
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatAssistant;