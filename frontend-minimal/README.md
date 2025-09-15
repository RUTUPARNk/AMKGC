# Node LLM System - Minimal Frontend

A minimal but production-ready frontend for the Node LLM System backend, built with React, Vite, TailwindCSS, and ShadCN UI.

## Features

- Authentication with JWT storage
- Dashboard layout with navbar, sidebar, and main panel
- Chat window with message bubbles and input bar
- Cache management modal
- Responsive design

## Tech Stack

- React 18 with TypeScript
- Vite for fast development and building
- TailwindCSS for styling
- Axios for API requests
- React Router for navigation

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Development

- The development server runs on http://localhost:3001
- API requests are proxied to http://localhost:8000
- Environment variables can be set in a `.env` file

## Project Structure

```
src/
  components/
    ChatWindow.tsx
    MessageBubble.tsx
    SearchBar.tsx
    CacheModal.tsx
    LoginForm.tsx
  pages/
    LoginPage.tsx
    Dashboard.tsx
  services/
    api.ts
    cacheAPI.ts
  App.tsx
  main.tsx
```

## Docker

To run with Docker, build the image and run the container:

```bash
# Build the image
docker build -t node-llm-frontend-minimal .

# Run the container
docker run -p 3001:3001 node-llm-frontend-minimal
```
