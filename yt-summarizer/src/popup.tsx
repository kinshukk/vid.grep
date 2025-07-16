import React from 'react';
import './index.css';
import { createRoot } from 'react-dom/client';

const Popup = () => {
  const [summary, setSummary] = React.useState('');
  const [error, setError] = React.useState('');

  const summarize = async () => {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tabs[0].url;

    if (url && url.includes('youtube.com/watch')) {
      try {
        const response = await new Promise((resolve, reject) => {
          chrome.runtime.sendNativeMessage(
            'com.google.chrome.example.echo',
            { text: url },
            (response) => {
              if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
              } else {
                resolve(response);
              }
            }
          );
        });
        setSummary(response.text);
      } catch (e) {
        setError(e.message);
      }
    } else {
      setError('Not a YouTube video page.');
    }
  };

  return (
    <div className="p-4 w-80">
      <h1 className="text-lg font-bold mb-4">YouTube Summarizer</h1>
      <button
        onClick={summarize}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
      >
        Summarize
      </button>
      {summary && (
        <div className="mt-4">
          <h2 className="text-md font-bold">Summary:</h2>
          <pre className="whitespace-pre-wrap bg-gray-100 p-2 rounded">
            {summary}
          </pre>
        </div>
      )}
      {error && <p className="text-red-500 mt-4">{error}</p>}
    </div>
  );
};

const root = createRoot(document.getElementById('root')!);
root.render(<Popup />);