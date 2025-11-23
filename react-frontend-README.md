# Audio Separation UI - React Frontend

A modern, dark-themed React interface for audio separation, styled after Moises.ai.

## Features

- 🎨 Dark theme with professional styling
- 📱 Responsive layout with sidebar navigation
- 🎵 Track separation interface (Basic & Custom)
- 🔒 Premium/locked feature indicators
- ♿ Accessible components with keyboard navigation
- ⚡ Built with TypeScript and styled-components

## Project Structure

```
react-frontend/
├── src/
│   ├── components/
│   │   ├── layout/          # Sidebar, MainContent, PageHeader
│   │   ├── navigation/      # NavItem components
│   │   ├── separation/      # Separation UI components
│   │   └── ui/              # Reusable UI components
│   ├── styles/
│   │   ├── theme.ts         # Design system tokens
│   │   └── globals.css      # Global styles
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions & icons
│   └── App.tsx              # Main app component
├── public/
└── package.json
```

## Installation

```bash
cd react-frontend
npm install
```

## Development

```bash
npm start
```

Runs the app in development mode at [http://localhost:3000](http://localhost:3000)

## Build

```bash
npm run build
```

Builds the app for production to the `build` folder.

## Design System

The app uses a comprehensive design system defined in `src/styles/theme.ts`:

- **Colors**: Dark theme with blue accents
- **Typography**: System font stack with clear hierarchy
- **Spacing**: Consistent 4px-based spacing scale
- **Components**: Styled-components for all UI elements

## Components

### Layout Components
- `Sidebar`: Fixed left navigation sidebar
- `MainContent`: Main content area with proper margins
- `PageHeader`: Page title and subtitle

### Separation Components
- `BasicSeparationButton`: Large buttons for preset separations
- `TrackButton`: Individual track selection buttons
- `TrackGrid`: Grid layout for track buttons
- `Section`: Content sections with optional info icons

### Navigation Components
- `NavItem`: Sidebar navigation items with icons and badges

## Integration with Backend

To connect with the Flask backend API:

1. Update the API URL in components that need backend integration
2. Add API service functions in `src/services/api.ts`
3. Use React hooks for data fetching (consider adding `react-query`)

## Next Steps

- [ ] Connect to Flask backend API
- [ ] Add file upload functionality
- [ ] Implement separation job status tracking
- [ ] Add audio player component
- [ ] Implement routing (React Router)
- [ ] Add loading states and error handling
- [ ] Add responsive mobile menu

## Technologies

- React 18
- TypeScript
- Styled Components
- Lucide React (Icons)
- Create React App

