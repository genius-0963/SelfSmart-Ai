import React from 'react'

export default function Debug() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Debug Page</h1>
      <p>If you can see this, React is working!</p>
      <p>Current URL: {window.location.href}</p>
      <p>Time: {new Date().toLocaleString()}</p>
      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0' }}>
        <h3>Environment Check:</h3>
        <p>React: ✅ Loaded</p>
        <p>JavaScript: ✅ Running</p>
        <p>Styles: ✅ Applied</p>
      </div>
    </div>
  )
}
